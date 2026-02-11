import os
import openai
import random
import time
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
CANAL = os.getenv("CANAL")  # Ex: @SeuCanalRomantico

openai.api_key = OPENAI_KEY
bot = Bot(token=BOT_TOKEN)

PROMPTS = [
    "Escreva uma frase romântica profunda e curta",
    "Crie uma mensagem apaixonada para alguém especial",
    "Faça um poema romântico curto",
    "Escreva uma mensagem de saudade amorosa",
    "Crie uma indireta romântica elegante",
    "Mensagem noturna romântica e intensa",
    "Mensagem doce e fofa sobre amor",
    "Mensagem romântica intensa e marcante",
]

def gerar_post():
    prompt = random.choice(PROMPTS)

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você escreve mensagens românticas emocionantes, bonitas e envolventes."},
            {"role": "user", "content": prompt}
        ]
    )

    return resposta.choices[0].message.content.strip()

def postar():
    try:
        texto = gerar_post()
        bot.send_message(chat_id=CANAL, text=f"💖 {texto}")
        print("✅ Post enviado")
    except Exception as e:
        print("❌ Erro ao postar:", e)

scheduler = BackgroundScheduler()
scheduler.add_job(postar, "interval", hours=3)  # posta a cada 3 horas
scheduler.start()

print("💘 Bot romântico rodando no Koyeb...")

while True:
    time.sleep(10)
