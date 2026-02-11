import os
import json
import openai
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

openai.api_key = OPENAI_KEY

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "channels": [],
    "interval": 3,
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

PROMPT_STYLES = {
    "romantico": [
        "Escreva uma frase romântica profunda",
        "Crie uma mensagem apaixonada",
        "Escreva um poema romântico curto"
    ],
    "sensual": [
        "Mensagem romântica sensual leve",
        "Texto apaixonado intenso",
        "Frase sedutora elegante"
    ],
    "dark": [
        "Mensagem dark romance intensa",
        "Frase romântica melancólica",
        "Texto amoroso sombrio"
    ],
    "fofo": [
        "Mensagem fofa sobre amor",
        "Frase doce romântica",
        "Texto carinhoso leve"
    ]
}

async def gerar_post(style):
    prompt = random.choice(PROMPT_STYLES.get(style, PROMPT_STYLES["romantico"]))

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você escreve mensagens românticas bonitas e emocionantes."},
            {"role": "user", "content": prompt}
        ]
    )

    return resposta.choices[0].message.content.strip()

async def postar():
    config = load_config()
    if not config["enabled"]:
        return

    for canal in config["channels"]:
        try:
            texto = await gerar_post(config["style"])
            await app.bot.send_message(chat_id=canal, text=f"💖 {texto}")
            print(f"✅ Post enviado para {canal}")
        except Exception as e:
            print(f"❌ Erro em {canal}:", e)

app = ApplicationBuilder().token(BOT_TOKEN).build()

# ===== MENU =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Canais", callback_data="channels")],
        [InlineKeyboardButton("⏰ Intervalo", callback_data="interval")],
        [InlineKeyboardButton("🎨 Estilo", callback_data="style")],
        [InlineKeyboardButton("▶️ Ligar", callback_data="enable")],
        [InlineKeyboardButton("⏸ Pausar", callback_data="disable")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]
    await update.message.reply_text("💘 MENU DO BOT ROMÂNTICO", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = load_config()

    if query.data == "channels":
        texto = "📢 Canais atuais:\n" + "\n".join(config["channels"]) if config["channels"] else "Nenhum canal"
        await query.edit_message_text(texto + "\n\nUse /addcanal @canal")

    elif query.data == "interval":
        await query.edit_message_text(f"⏰ Intervalo atual: {config['interval']} horas\nUse /intervalo 2")

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
        await query.edit_message_text("▶️ Autopost LIGADO")

    elif query.data == "disable":
        config["enabled"] = False
        save_config(config)
        await query.edit_message_text("⏸ Autopost PAUSADO")

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

# ===== SCHEDULER =====
scheduler = BackgroundScheduler()
scheduler.add_job(postar, "interval", hours=3, id="post_job")
scheduler.start()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addcanal", add_canal))
app.add_handler(CommandHandler("intervalo", intervalo))
app.add_handler(CallbackQueryHandler(menu_handler))

print("💘 Bot multicanal rodando no Koyeb...")
app.run_polling()
