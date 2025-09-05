import nltk
import spacy

# Baixar pacotes do NLTK
print("🔽 Baixando recursos do NLTK...")
nltk.download("punkt")
nltk.download("stopwords")

# Baixar modelo do spaCy para português
print("🔽 Baixando modelo spaCy para português...")
spacy.cli.download("pt_core_news_sm")

print("✅ Setup concluído! Agora você já pode rodar o backend.")
