import telebot
import requests

API_KEY = "CHAVE_DO_TELEGRAM"
BACKEND_URL = "http://localhost:5000/summarize"

bot = telebot.TeleBot(API_KEY)

@bot.message_handler(content_types=["text"])
def handle_text(message):
    response = requests.post(BACKEND_URL, json={"text": message.text})
    summary = response.json().get("summary", "Erro ao gerar resumo.")
    bot.reply_to(message, summary)

@bot.message_handler(content_types=["document"])
def handle_doc(message):
    file_info = bot.get_file(message.document.file_id)
    file_url = f"https://api.telegram.org/file/bot{API_KEY}/{file_info.file_path}"
    text = requests.get(file_url).text

    response = requests.post(BACKEND_URL, json={"text": text})
    summary = response.json().get("summary", "Erro ao gerar resumo.")
    bot.reply_to(message, summary)

print("Bot rodando...")
bot.infinity_polling()
