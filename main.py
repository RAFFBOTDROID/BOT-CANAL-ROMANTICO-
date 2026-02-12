import os
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from groq import Groq

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_KEY:
    raise ValueError("⚠️ BOT_TOKEN ou GROQ_API_KEY não configurados nas variáveis de ambiente.")

client = Groq(api_key=GROQ_KEY)

# ===== CONFIG PADRÃO =====
channels = ["@seu_canal_teste"]
interval_hours = 2
style = "romantico"
text_size = "medio"
enabled = True

# ===== PROMPTS IA =====
PROMPT_STYLES = {
    "romantico": ["Escreva um texto romântico profundo, intenso e marcante, com começo, meio e fim"],
    "sensual": ["Escreva um texto sensual elegante, intenso e provocante, com começo, meio e fim"],
    "dark": ["Escreva um texto dark romance melancólico, profundo e intenso, com começo, meio e fim"],
    "fofo": ["Escreva um texto fofo, doce e emocional, com começo, meio e fim"]
}

# ===== TAMANHO TEXTO =====
TEXT_LIMITS = {"curto": 140, "medio": 220, "longo": 320, "gigante": 480}

# ===== GERAR TEXTO =====
async def gerar_post(style_, size_):
    prompt = random.choice(PROMPT_STYLES.get(style_, PROMPT_STYLES["romantico"]))
    char_limit = TEXT_LIMITS.get(size_, 220)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "Gere UM ÚNICO TEXTO curto, em UMA ÚNICA ESTROFE. "
                    "O TEXTO DEVE TER começo, meio e fim. "
                    "Finalize a ideia completamente. "
                    "Não use clichês repetidos. "
                    "Não quebre linhas. "
                    "Parecer humano, intenso e natural."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=250
        )
        texto = response.choices[0].message.content.strip().replace("\n", " ").replace("  ", " ")
        if len(texto) > char_limit:
            texto = texto[:char_limit].rsplit(" ", 1)[0] + "."
        if not texto.endswith("."):
            texto += "."
        return texto
    except Exception as e:
        print("❌ ERRO GROQ:", e)
        return "⚠️ IA temporariamente indisponível."

# ===== POSTAGEM =====
async def postar(app: Application):
    global enabled
    if not enabled:
        return
    for canal in channels:
        try:
            texto = await gerar_post(style, text_size)
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
        "💘 BOT ROMÂNTICO IA\n\nTextos curtos, intensos e completos",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global channels, interval_hours, style, text_size, enabled
    query = update.callback_query
    await query.answer()
    if query.data == "channels":
        canais = "\n".join(channels) if channels else "Nenhum canal"
        await query.edit_message_text(f"📢 Canais:\n{canais}\n\nUse /addcanal @canal")
    elif query.data == "interval":
        await query.edit_message_text(f"⏰ Intervalo: {interval_hours}h\nUse /intervalo 2")
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
        await query.edit_message_text("✅ Estilo atualizado")
    elif query.data.startswith("setsize_"):
        text_size = query.data.replace("setsize_", "")
        await query.edit_message_text("✅ Tamanho atualizado")
    elif query.data == "enable":
        enabled = True
        await query.edit_message_text("▶️ Autopost ATIVADO")
    elif query.data == "disable":
        enabled = False
        await query.edit_message_text("⏸ Autopost PAUSADO")
    elif query.data == "post_now":
        await query.edit_message_text("⚡ Gerando agora...")
        await postar(context.application)
        await query.edit_message_text("✅ Post enviado")
    elif query.data == "status":
        status = "🟢 ATIVO" if enabled else "🔴 PAUSADO"
        await query.edit_message_text(
            f"📊 STATUS\n\n"
            f"Canais: {len(channels)}\n"
            f"Intervalo: {interval_hours}h\n"
            f"Estilo: {style}\n"
            f"Tamanho: {text_size}\n"
            f"Status: {status}"
        )

# ===== COMANDOS =====
async def add_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global channels
    if not context.args:
        await update.message.reply_text("Use: /addcanal @canal")
        return
    canal = context.args[0]
    if canal not in channels:
        channels.append(canal)
        await update.message.reply_text(f"✅ Canal adicionado: {canal}")

async def intervalo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global interval_hours, scheduler
    try:
        horas = int(context.args[0])
        interval_hours = horas
        scheduler.reschedule_job("post_job", trigger=IntervalTrigger(hours=interval_hours))
        await update.message.reply_text(f"⏰ Intervalo alterado para {horas}h")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")

# ===== APP =====
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addcanal", add_canal))
app.add_handler(CommandHandler("intervalo", intervalo))
app.add_handler(CallbackQueryHandler(menu_handler))

# ===== SCHEDULER =====
scheduler = AsyncIOScheduler()
async def iniciar_scheduler():
    async def job_wrapper():
        await postar(app)
    scheduler.add_job(job_wrapper, trigger=IntervalTrigger(hours=interval_hours), id="post_job")
    scheduler.start()

# ===== MAIN =====
if __name__ == "__main__":
    asyncio.run(iniciar_scheduler())
    app.run_polling()
