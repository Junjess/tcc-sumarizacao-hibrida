# importa a biblioteca torch (PyTorch) usada para verificar GPU e, opcionalmente, para operações com tensores
import torch

# importa utilitários do Hugging Face Transformers:
# - AutoTokenizer: carrega o tokenizador do modelo
# - AutoModelForSeq2SeqLM: carrega o modelo seq2seq (T5-like) para geração
# - pipeline: fornece um wrapper fácil para tarefas (aqui: summarization)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# importa classes do Flask para criar a API:
# - Flask: cria a aplicação
# - request: obtém dados da requisição (JSON enviado pelo client)
# - jsonify: transforma dicionários Python em resposta JSON
from flask import Flask, request, jsonify

# importa CORS para permitir chamadas cross-origin (útil para front-end rodando em outra origem)
from flask_cors import CORS

# BeautifulSoup para parse de HTML (extração de texto a partir do HTML enviado)
from bs4 import BeautifulSoup

# funções do NLTK:
# - sent_tokenize: divide texto em sentenças
# - stopwords: lista de stopwords (palavras comuns) para português
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

# importa o nltk para baixar recursos (punkt, stopwords)
import nltk

# expressão regular (regex) via módulo re
import re


# Cria a aplicação Flask. __name__ ajuda o Flask a localizar recursos relativos.
app = Flask(__name__)

# Habilita CORS para todas as rotas da aplicação (permite que o front-end faça requests)
CORS(app)


# ----------------------------
# Preparação do NLTK (recursos)
# ----------------------------
# baixa o modelo de tokenização de sentenças 'punkt' (necessário para sent_tokenize)
nltk.download("punkt")
# baixa a lista de stopwords em vários idiomas, incluindo 'portuguese'
nltk.download("stopwords")


# ----------------------------
# Configuração do modelo de summarization
# ----------------------------
# nome do modelo Hugging Face que será carregado (fine-tuned para sumarização em pt)
MODEL_NAME = "recogna-nlp/ptt5-base-summ"

# seleciona device: se houver GPU disponível via torch, usa 0 (índice da GPU), senão -1 (usa CPU para o pipeline)
device = 0 if torch.cuda.is_available() else -1

# imprime no console qual device foi selecionado (útil para debug/monitoramento)
print("Device:", "GPU" if device == 0 else "CPU")


# carrega o tokenizador do modelo especificado (faz download se necessário / usa cache)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# carrega o modelo seq2seq (T5-like) do Hugging Face
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# cria um pipeline de summarization com o modelo e tokenizador carregados, apontando para o device escolhido
# o pipeline lida com tokenização + inferência + decodificação do texto gerado
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)


# ----------------------------
# Funções auxiliares de pré-processamento
# ----------------------------

def clean_html(html):
    """Remove tags desnecessárias e retorna apenas o texto limpo."""
    # cria o objeto BeautifulSoup para parse do HTML; especifica 'lxml' como parser (mais rápido/robusto)
    soup = BeautifulSoup(html, "lxml")

    # desfaz (remove) tags que normalmente não são conteúdo textual relevante
    # (script/style/img/nav/footer/aside/form/button/iframe/header)
    for tag in soup(["script","style","img","nav","footer","aside","form","button","iframe","header"]):
        tag.decompose()  # decompose() remove o nó e seu conteúdo do DOM

    # extrai o texto (concatena nós de texto com um separador espaço)
    text = soup.get_text(separator=" ", strip=True)

    # passa por uma limpeza adicional (função abaixo) e retorna o texto limpo
    return clean_text(text)


def clean_text(text):
    """Remove múltiplos espaços, quebras e caracteres especiais desnecessários."""
    # substitui sequências de whitespace (quebras de linha, tabs, múltiplos espaços) por um único espaço
    text = re.sub(r'\s+', ' ', text)

    # remove caracteres que não sejam letras/dígitos/underline, espaços e sinais de pontuação básicos
    # [^\w\s,.!?;:] -> remove tudo que não for palavra (\w), espaço (\s) ou esses sinais
    text = re.sub(r'[^\w\s,.!?;:]', '', text)

    # remove espaços nas pontas e retorna
    return text.strip()


def filter_sentences(text, min_words=5):
    """
    Divide o texto em sentenças e filtra sentenças curtas ou com alta proporção de stopwords.
    - min_words: número mínimo de palavras para considerar a sentença relevante.
    """
    # tokeniza o texto em sentenças (usando 'punkt' do NLTK em português)
    sentences = sent_tokenize(text, language="portuguese")

    # carrega as stopwords do português e converte para set (busca rápida)
    stopwords_pt = set(stopwords.words("portuguese"))

    result = []  # lista final de sentenças relevantes

    # para cada sentença:
    for sent in sentences:
        # extrai "palavras" alfabéticas via regex e filtra tokens que não são alfabéticos
        words = [w for w in re.findall(r"\w+", sent) if w.isalpha()]

        # se a sentença tem menos que min_words palavras, ignora
        if len(words) >= min_words:
            # calcula a proporção de stopwords na sentença
            sw_ratio = sum(1 for w in words if w.lower() in stopwords_pt) / len(words)

            # se a proporção de stopwords for menor que 0.7 (heurística), considera relevante
            if sw_ratio < 0.7:
                result.append(sent)

    # retorna a lista de sentenças filtradas
    return result


def chunk_text(sentences, max_words=150):
    """
    Agrupa sentenças em "chunks" (blocos) com até max_words palavras.
    Isso é útil para evitar enviar textos muito longos ao modelo de uma só vez.
    """
    chunks = []           # lista de blocos finais (cada bloco é string)
    current_chunk = []    # sentenças do bloco atual
    current_words = 0     # contador de palavras do bloco atual

    for sent in sentences:
        n_words = len(sent.split())  # aproximação: conta palavras pela separação por espaço

        # se adicionar a sentença atual excede max_words, fecha o bloco atual
        if current_words + n_words > max_words:
            if current_chunk:
                # junta as sentenças do bloco atual em uma string e adiciona a chunks
                chunks.append(" ".join(current_chunk))
            # inicia novo bloco com a sentença atual
            current_chunk = [sent]
            current_words = n_words
        else:
            # caso contrário, acrescenta a sentença ao bloco atual
            current_chunk.append(sent)
            current_words += n_words

    # adiciona o último bloco se existir conteúdo
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_chunks(chunks, max_length=200, min_length=80):
    """
    Resume cada chunk usando o pipeline summarizer e concatena os resumos.
    - max_length/min_length definem limites do summary gerado.
    """
    summaries = []

    for chunk in chunks:
        try:
            # chama o pipeline; o pipeline retorna lista de outputs; pegamos 'summary_text'
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            # em caso de erro ao resumir um chunk (por exemplo, tokenização ou OOM),
            # imprime o erro no log e usa o próprio chunk como fallback (resumo literal)
            print("Erro no chunk:", e)
            summaries.append(chunk)  # fallback

    # junta todos os resumos em uma única string coesa
    return " ".join(summaries)


# ----------------------------
# Rota HTTP para resumo (/resumir)
# ----------------------------
@app.route("/resumir", methods=["POST"])
def resumir():
    # obtém o JSON enviado pelo client
    data = request.get_json()

    # valida entrada: espera que exista 'html' no JSON
    if not data or "html" not in data:
        return jsonify({"error": "Nenhum HTML fornecido"}), 400

    try:
        html = data["html"]  # texto/HTML enviado pelo front

        # limpa o HTML e converte para texto puro
        cleaned_text = clean_html(html)

        # filtra sentenças relevantes
        sentences = filter_sentences(cleaned_text)

        # se não encontrou sentenças relevantes, retorna mensagem amigável
        if not sentences:
            return jsonify({"resumo": "Não foi possível extrair texto relevante da página."})

        # divide as sentenças em chunks e resume
        chunks = chunk_text(sentences, max_words=150)
        resumo_coeso = summarize_chunks(chunks, max_length=200, min_length=80)

        # heurística simples para detectar "títulos" (se quiser gerar tópicos)
        sections = []
        for sent in sentences:
            # se a sentença estiver em maiúsculas ou contém ":" consideramos potencial título
            if sent.isupper() or ":" in sent:
                sections.append({"titulo": sent, "resumo": ""})

        # se encontrou títulos, atribui o mesmo resumo_coeso a cada seção (simplificação)
        if sections:
            for i, sec in enumerate(sections):
                sec["resumo"] = resumo_coeso  # NOTA: aqui é simplificado; pode ser melhorado
        else:
            sections = None  # se não há títulos, devolve None para evitar lista vazia

        # retorna JSON com o resumo coeso e as seções (ou null)
        return jsonify({"resumo_coeso": resumo_coeso, "sections": sections})

    except Exception as e:
        # em caso de exceção, imprime no console e retorna erro 500 ao front
        print("Erro ao gerar resumo:", e)
        return jsonify({"resumo": "Erro ao gerar resumo"}), 500


# executa a app Flask em modo debug quando o script for executado diretamente
if __name__ == "__main__":
    app.run(debug=True)
