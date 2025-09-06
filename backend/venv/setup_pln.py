import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import nltk
from nltk.tokenize import sent_tokenize

# Modelo abstrativo público para português
MODEL_NAME = "recogna-nlp/ptt5-base-summ"

# Define dispositivo: GPU se disponível, senão CPU
device = 0 if torch.cuda.is_available() else -1
print("Device set to use GPU" if device == 0 else "Device set to use CPU")

# --------------------------------------
# Download NLTK necessário
# --------------------------------------
nltk.download("punkt")        # Tokenização de frases
nltk.download("punkt_tab")    # Para alguns modelos antigos que usam 'punkt_tab'

# --------------------------------------
# Inicializa o tokenizer e o modelo
# --------------------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Cria pipeline de summarization
summarizer = pipeline(
    "summarization",
    model=model,
    tokenizer=tokenizer,
    device=device
)

# --------------------------------------
# Funções auxiliares
# --------------------------------------
def chunk_text(text, max_words=200):
    """
    Divide o texto em chunks menores baseados em sentenças.
    max_words: quantidade máxima de palavras por chunk
    """
    sentences = sent_tokenize(text, language="portuguese")
    chunks = []
    current_chunk = []
    current_words = 0

    for sent in sentences:
        words_in_sent = len(sent.split())
        if current_words + words_in_sent > max_words:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_words = words_in_sent
        else:
            current_chunk.append(sent)
            current_words += words_in_sent

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def summarize_long_text(text, max_words_per_chunk=200):
    """
    Resume textos longos, dividindo em chunks para não ultrapassar o limite do modelo.
    """
    chunks = chunk_text(text, max_words=max_words_per_chunk)
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return " ".join(summaries)

# --------------------------------------
# Exemplo de uso
# --------------------------------------
if __name__ == "__main__":
    example_text = """
    Seara, localizada em Santa Ctarina, foi colonizada por italianos e alemães e tem a economia voltada para a agropecuária. O município abriga uma obra monumental, o Museu Entomológico Fritz Plaumann, que guarda a maior coleção de insetos de toda a América Latina e desde a sua implantação em 1988 vem se destacando no cenário internacional de turismo científico.

Seara, cuja denominação significa terra de abundantes grãos cerealíferos. Tem no seu nobre povo, a semear no tempo, muito trabalho e dedicação. Em 1924 iniciou-se a demarcação das terras e colonização do povoado de Nova Milano, hoje Seara.

Agricultores pobres vindos do Rio Grande do Sul, das regiões próximas a Guaporé, Serafina Correa e Casca vinham a se estabelecer em Nova Milano, munidos apenas de suas precárias ferramentas de agricultura, sementes e sonhos de um futuro bom.

Em 15 de março de 1944, Nova Milano passou a se chamar Seara. Sugestão do então prefeito de Concórdia, Dogello Goss, homenageando o engenheiro agrimensor Carlos Otaviano Seara, que era encarregado de trabalhos de demarcação de terras pelo estado. No dia 3 de abril de 1954 Seara emancipa-se de Concórdia.

Além da produção de grãos, o comércio local, o turismo e a crescente preocupação e interesse de ordem ambiental, ecológica e de qualidade de vida da sua população são as primícias do planejamento da gestão municipal.

A Casa da Cultura
A ideia de construir um espaço próprio para a cultura de Seara tomou forma a partir da doação do prédio do antigo moinho de trigo Seara em maio de 1988, pela Seara Industrial S/A. A construção foi reestruturada e restaurada e transformada na Casa da Cultura Biágio Aurélio Paludo, em homenagem ao idealizador do moinho.

Hoje a Casa da Cultura move todo processo cultural do município. Lá são desenvolvidos diversos cursos. Entre eles destacamos: Acordeom, Balé, Banda Municipal, Desenho, Flauta, Guitarra, Orquestra Municipal, Piano, Sapateado, Teclado, Teoria Musical, Teatro, Violão, Violino, Viola e Violoncelo.

O município já foi referência, inclusive, em grandes festivais de dança, como o Festival de Dança de Joinville, com apresentações de balé clássico, sapateado e outras modalidades.

Praça Central
A praça central de Seara é parte da memória viva da cidade. Gerações se acomodam tranquilamente naqueles bancos, debaixo da sombra da canafístula, num espaço construído na década de 60.

A praça foi denominada Doutor Harry Quadros de Oliveira e está localizada na Avenida Anita Garibaldi. A denominação enaltece o pediatra que muito fez pela saúde dos pioneiros. Contam os antigos que, diariamente, Dr. Harry fazia o trajeto de sua casa, onde atualmente está a Rede Feminina de Combate ao Câncer, até o hospital, cortando caminho pela pracinha.

Cada banco instalado no local foi uma doação de empresários de Seara à época. Muitos já se foram e boa parte das lojas nem existe mais. As contribuições foram de: C. Bolzani & Cia Ltda e Casemiras Bossa Nova, de Arcides Benetti; o Pasqualim Alfaiate; Clair e Geraldo Bolzani e Genuíno Sfredo, o Baião, ocupando atualmente a Casa Raquel Decorações e a Agropecuária Santin; Bar Biruta, de Rizziere Dal Maz, local que hoje está instalada Caixa Econômica Federal, barzinho em que o ex-prefeito Aurélio Nardi, na sua juventude, trabalhou como garçom; Nardi Tumelero Indústria e Comércio Ltda, de João Nardi e Etelvino Pedro Tumelero, ex-prefeito e vereador de Seara – hoje o espaço abriga a Sicoob-Crediauc.

Dr. Harry também deixou um banco para a praça, assim como Theodoro Barbieri Cia Comércio em Geral, onde hoje está a Copérdia. A Seara S.A. Moinhos Ind. e Com. de Cereais funcionou até a década de 1970, onde hoje é a Casa da Cultura. Associação Rural de Seara, de Domingos Sfredo, Casa Petry, de Valentim Petry, também patrocinaram os bancos da praça.

Museu Fritz Plaumann
O Museu Entomológico Doutor Fritz Plaumann foi inaugurado em 23 de outubro de 1988 no distrito de Nova Teutônia. Lá está exposta toda a sua magnífica obra científica.

São mais de 80 mil exemplares de 17 mil espécies diferentes de insetos que poderão ser observados pelos visitantes. Seu acervo é o resultado de mais de setenta anos de pesquisas na região da bacia do Rio Uruguai, e de incursões aos estados do Paraná e Mato Grosso do Sul.
    """
    resumo = summarize_long_text(example_text)
    print("Resumo final:\n", resumo)
