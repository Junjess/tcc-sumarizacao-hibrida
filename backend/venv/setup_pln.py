import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import nltk
import re

app = Flask(__name__)
CORS(app)

#stopwords
nltk.download("punkt")
nltk.download("stopwords")


MODEL_NAME = "recogna-nlp/ptt5-base-summ" 
device = 0 if torch.cuda.is_available() else -1
print("Device:", "GPU" if device == 0 else "CPU")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=device)

def clean_html(html):
    """Remove tags desnecessárias e retorna apenas o texto limpo."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","img","nav","footer","aside","form","button","iframe","header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return clean_text(text)

def clean_text(text):
    """Remove múltiplos espaços, quebras e caracteres especiais desnecessários."""
    text = re.sub(r'\s+', ' ', text)            
    text = re.sub(r'[^\w\s,.!?;:]', '', text) 
    return text.strip()

def filter_sentences(text, min_words=5):
    sentences = sent_tokenize(text, language="portuguese")
    stopwords_pt = set(stopwords.words("portuguese"))
    result = []
    for sent in sentences:
        words = [w for w in re.findall(r"\w+", sent) if w.isalpha()]
        if len(words) >= min_words:
            sw_ratio = sum(1 for w in words if w.lower() in stopwords_pt) / len(words)
            if sw_ratio < 0.7:
                result.append(sent)
    return result

def chunk_text(sentences, max_words=150):
    chunks = []
    current_chunk = []
    current_words = 0
    for sent in sentences:
        n_words = len(sent.split())
        if current_words + n_words > max_words:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_words = n_words
        else:
            current_chunk.append(sent)
            current_words += n_words
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def summarize_chunks(chunks, max_length=200, min_length=80):
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            print("Erro no chunk:", e)
            summaries.append(chunk)  
    return " ".join(summaries)

@app.route("/resumir", methods=["POST"])
def resumir():
    data = request.get_json()
    if not data or "html" not in data:
        return jsonify({"error": "Nenhum HTML fornecido"}), 400
    try:
        html = data["html"]

        cleaned_text = clean_html(html)
        sentences = filter_sentences(cleaned_text)

        if not sentences:
            return jsonify({"resumo": "Não foi possível extrair texto relevante da página."})

        chunks = chunk_text(sentences, max_words=150)
        resumo_coeso = summarize_chunks(chunks, max_length=200, min_length=80)

        # para criar tópicos
        sections = []
        for sent in sentences:
            if sent.isupper() or ":" in sent: 
                sections.append({"titulo": sent, "resumo": ""})
        if sections:
            for i, sec in enumerate(sections):
                sec["resumo"] = resumo_coeso 
        else:
            sections = None

        return jsonify({"resumo_coeso": resumo_coeso, "sections": sections})

    except Exception as e:
        print("Erro ao gerar resumo:", e)
        return jsonify({"resumo": "Erro ao gerar resumo"}), 500


if __name__ == "__main__":
    app.run(debug=True)
