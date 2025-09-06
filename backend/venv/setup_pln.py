import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import nltk
from nltk.tokenize import sent_tokenize
from flask import Flask, request, jsonify
from flask_cors import CORS

# ----------------------------
# Inicializa Flask
# ----------------------------
app = Flask(__name__)
CORS(app)  # Permite que a extensão faça requisições

# ----------------------------
# Configura modelo
# ----------------------------
MODEL_NAME = "recogna-nlp/ptt5-base-summ"

device = 0 if torch.cuda.is_available() else -1
print("Device set to use GPU" if device == 0 else "Device set to use CPU")

# ----------------------------
# Download NLTK necessário
# ----------------------------
nltk.download("punkt")
nltk.download("punkt_tab")

# ----------------------------
# Inicializa tokenizer e modelo
# ----------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

summarizer = pipeline(
    "summarization",
    model=model,
    tokenizer=tokenizer,
    device=device
)

# ----------------------------
# Funções auxiliares
# ----------------------------
def chunk_text(text, max_words=200):
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
    chunks = chunk_text(text, max_words=max_words_per_chunk)
    summaries = []
    for chunk in chunks:
        summary = summarizer(
            chunk,
            max_length=150,
            min_length=30,
            do_sample=False
        )
        summaries.append(summary[0]['summary_text'])
    return " ".join(summaries)

# ----------------------------
# Endpoint Flask
# ----------------------------
@app.route("/resumir", methods=["POST"])
def resumir():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Nenhum texto fornecido"}), 400

    text = data["text"]
    try:
        resumo = summarize_long_text(text)
        return jsonify({"resumo": resumo})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Inicia Flask
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
