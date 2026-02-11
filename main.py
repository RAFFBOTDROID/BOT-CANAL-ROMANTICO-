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
    "enabled": True,
    "text_size": "longo"
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
        "Escreva um texto romântico profundo, intenso, emocional, poético e marcante",
        "Crie uma carta de amor madura, profunda e extremamente sentimental",
        "Texto de amor longo, apaixonado, emocional e inesquecível"
    ],
    "sensual": [
        "Escreva um texto sensual intenso, elegante, provocante e emocional",
        "Mensagem de desejo profunda, quente e envolvente",
        "Texto sedutor intenso, apaixonado e marcante"
    ],
    "dark": [
        "Texto dark romance profundo, melancólico, intenso e emocional",
        "Mensagem de amor intensa com dor, saudade e desejo",
        "Romance sombrio sentimental e marcante"
    ],
    "fofo": [
        "Texto fofo, doce, emocional e acolhedor",
        "Mensagem carinhosa longa, terna e cheia de afeto",
        "Texto romântico leve, doce e reconfortante"
    ]
}

# ===== CONTROLE TAMANHO =====
TEXT_LIMITS = {
    "curto": 140,
    "medio": 260,
    "longo": 420,
    "gigante": 700
}

# ===== IA GROQ — 1 ESTROFE COESA =====
async def gerar_post(style, size):
    prompt = random.choice(PROMPT_STYLES.get(style, PROMPT_STYLES["romantico"]))
    max_tokens = TEXT_LIMITS.get(size, 420)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você escreve UM ÚNICO TEXTO em UMA ÚNICA ESTROFE. "
                        "O texto deve ser PROFUNDO, INTENSO, ORIGINAL e 100% AUTORAL. "
                        "NÃO use clichês, NÃO repita frases comuns, NÃO copie estilos prontos. "
                        "NÃO use listas. NÃO quebre em parágrafos. "
                        "O texto deve ser COMPLETO, COESO e FINALIZAR a ideia. "
                        "Nunca corte o texto no meio. Sempre termine com ponto final. "
                        "Evite frases robóticas. Faça parecer humano, real e emocional."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"{prompt}. Gere em uma única estrofe, "
                        f"sem pular linha, com começo, meio e fim, "
                        f"finalizando o pensamento de forma completa."
                    )
                }
            ],
            temperature=0.95,
            max_tokens=max_tokens
        )

        texto = response.choices[0].message.content.strip()

        # LIMPEZA PARA GARANTIR 1 ESTROFE
        texto = texto.replace("\n", " ").replace("  ", " ")

        # GARANTIR FINAL COMPLETO
        if not texto.endswith("."):
            texto += "."

        return texto

    except Exception as e:
        print("❌ ERRO GROQ:", e)
        return "⚠️ IA indisponível. Tentando novamente na próxima postagem."
# ===== POSTAGEM =====
async def postar(app: Application):
    config = load_config()
    if not config["enabled"]:
        return

    for canal in config["channels"]:
        try:
            texto = await gerar_post(config["style"], config["text_size"])
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
        [InlineKeyboardButton("📏 Tamanho Texto", callback_data="size")],
        [InlineKeyboardButton("⚡ Postar AGORA", callback_data="post_now")],
        [InlineKeyboardButton("▶️ Ligar", callback_data="enable")],
        [InlineKeyboardButton("⏸ Pausar", callback_data="disable")],
        [InlineKeyboardButton("📊 Status", callback_data="status")]
    ]

    await update.message.reply_text(
        "💘 BOT ROMÂNTICO IA ULTRA\n\nTextos 100% gerados por IA",
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

    elif query.data == "size":
        buttons = [
            [InlineKeyboardButton("✏️ Curto", callback_data="setsize_curto")],
            [InlineKeyboardButton("📝 Médio", callback_data="setsize_medio")],
            [InlineKeyboardButton("📜 Longo", callback_data="setsize_longo")],
            [InlineKeyboardButton("📖 Gigante", callback_data="setsize_gigante")]
        ]
        await query.edit_message_text("📏 Escolha o tamanho:", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith("setstyle_"):
        style = query.data.replace("setstyle_", "")
        config["style"] = style
        save_config(config)
        await query.edit_message_text(f"✅ Estilo alterado para {style}")

    elif query.data.startswith("setsize_"):
        size = query.data.replace("setsize_", "")
        config["text_size"] = size
        save_config(config)
        await query.edit_message_text(f"✅ Tamanho alterado para {size}")

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
            f"Tamanho: {config['text_size']}\n"
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
