import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from groq import Groq

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "channels": [],
    "interval": 2,
    "style": "romantico",
    "enabled": True
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===== PROMPTS IA =====
PROMPT_STYLES = {
    "romantico": [
        "Escreva um texto romântico profundo, longo, emocional, intenso e poético, como uma carta de amor real",
        "Crie uma mensagem de amor madura, profunda e sentimental, cheia de saudade e paixão",
        "Escreva um texto romântico marcante que toque o coração intensamente"
    ],
    "sensual": [
        "Escreva um texto sensual intenso, elegante, provocante e emocional",
        "Crie uma mensagem de desejo profunda, quente, romântica e envolvente",
        "Texto sedutor intenso, apaixonado e marcante"
    ],
    "dark": [
        "Escreva um texto dark romance profundo, melancólico, intenso e emocional",
        "Crie uma mensagem de amor intenso com dor, saudade e desejo profundo",
        "Texto romântico sombrio, sentimental e marcante"
    ],
    "fofo": [
        "Escreva um texto fofo, doce, emocional e acolhedor sobre amor",
        "Crie uma mensagem carinhosa longa, terna e cheia de afeto",
        "Texto romântico leve, fofo e reconfortante"
    ]
}

# ===== IA GROQ — SEM FRASES LOCAIS =====
async def gerar_post(style):
    prompt = random.choice(PROMPT_STYLES.get(style, PROMPT_STYLES["romantico"]))

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você escreve textos românticos EXTREMAMENTE PROFUNDOS, LONGOS, "
                        "emocionantes, intensos, poéticos e marcantes. "
                        "O texto deve parecer uma carta de amor real, madura, "
                        "cheia de saudade, desejo, conexão emocional e impacto. "
                        "Nunca escreva frases curtas. Sempre produza textos longos."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.98,
            max_tokens=480
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("❌ ERRO GROQ:", e)

        # fallback automático para modelo menor
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Escreva um texto romântico profundo, longo e emocional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.95,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except:
            return "⚠️ IA temporariamente indisponível. Tentando novamente em instantes."
# ===== POSTAGEM =====
async def postar(app: Application):
    config = load_config()
    if not config["enabled"]:
        return

    for canal in config["channels"]:
        try:
            texto = await gerar_post(config["style"])
            await app.bot.send_message(chat_id=canal, text=f"💖 {texto}")
            print(f"✅ Post enviado para {canal}")
        except Exception as e:
            print(f"❌ Erro em {canal}: {e}")

# ===== MENU =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Canais", callback_data="channels")],
        [InlineKeyboardButton("⏰ Intervalo", callback_data="interval")],
        [InlineKeyboardButton("🎨 Estilo", callback_data="style")],
        [InlineKeyboardButton("⚡ Postar AGORA", callback_data="post_now")],
        [InlineKeyboardButton("▶️ Ligar", callback_data="enable")],
        [InlineKeyboardButton("⏸ Pausar", callback_data="disable")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]

    await update.message.reply_text(
        "💘 BOT ROMÂNTICO IA PROFUNDA\n\nTextos 100% gerados por IA",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = load_config()

    if query.data == "channels":
        canais = "\n".join(config["channels"]) if config["channels"] else "Nenhum canal"
        await query.edit_message_text(f"📢 Canais:\n{canais}\n\nUse /addcanal @canal")

    elif query.data == "interval":
        await query.edit_message_text(f"⏰ Intervalo: {config['interval']}h\nUse /intervalo 2")

    elif query.data == "style":
        buttons = [
            [InlineKeyboardButton("💗 Fofo", callback_data="setstyle_fofo")],
            [InlineKeyboardButton("🔥 Romântico", callback_data="setstyle_romantico")],
            [InlineKeyboardButton("😈 Sensual", callback_data="setstyle_sensual")],
            [InlineKeyboardButton("🖤 Dark", callback_data="setstyle_dark")]
        ]
        await query.edit_message_text("🎨 Escolha o estilo:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("setstyle_"):
        style = query.data.replace("setstyle_", "")
        config["style"] = style
        save_config(config)
        await query.edit_message_text(f"✅ Estilo alterado para {style}")

    elif query.data == "enable":
        config["enabled"] = True
        save_config(config)
        await query.edit_message_text("▶️ Autopost ATIVADO")

    elif query.data == "disable":
        config["enabled"] = False
        save_config(config)
        await query.edit_message_text("⏸ Autopost PAUSADO")

    elif query.data == "post_now":
        await query.edit_message_text("⚡ Gerando e postando AGORA...")
        await postar(context.application)
        await query.edit_message_text("✅ Posts enviados!")

    elif query.data == "status":
        status = "🟢 ATIVO" if config["enabled"] else "🔴 PAUSADO"
        await query.edit_message_text(
            f"📊 STATUS\n\n"
            f"Canais: {len(config['channels'])}\n"
            f"Intervalo: {config['interval']}h\n"
            f"Estilo: {config['style']}\n"
            f"Status: {status}"
        )

# ===== COMANDOS =====
async def add_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /addcanal @canal")
        return

    canal = context.args[0]
    config = load_config()

    if canal not in config["channels"]:
        config["channels"].append(canal)
        save_config(config)
        await update.message.reply_text(f"✅ Canal adicionado: {canal}")

async def intervalo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /intervalo 2")
        return

    horas = int(context.args[0])
    config = load_config()
    config["interval"] = horas
    save_config(config)

    scheduler.reschedule_job("post_job", trigger="interval", hours=horas)
    await update.message.reply_text(f"⏰ Intervalo alterado para {horas} horas")

# ===== APP =====
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addcanal", add_canal))
app.add_handler(CommandHandler("intervalo", intervalo))
app.add_handler(CallbackQueryHandler(menu_handler))

# ===== SCHEDULER =====
scheduler = AsyncIOScheduler()

async def iniciar_scheduler():
    scheduler.add_job(postar, "interval", hours=2, id="post_job", args=[app])
    scheduler.start()

async def main():
    await iniciar_scheduler()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
