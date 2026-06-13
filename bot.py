import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789")) 

# Default initial caption
CUSTOM_CAPTION = "🎬 **File Name:** {filename}\n\n✨ **Join our main channel for more updates!** ✨"

# --- KOYEB HEALTH CHECK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ADMIN COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(
        "👋 **Welcome to Auto Caption Bot!**\n\n"
        "**Commands:**\n"
        "➡ `/setcaption <text>` - Paazhaya caption-ai azhithu puthiya caption set seiya (Use `{filename}` for file name)\n"
        "➡ `/status` - Current caption settings-ai parka"
    )

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CUSTOM_CAPTION
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setcaption text`")
        return
    
    # Full message-il irundhu line breaks kooda exact-ah caption-ai edukum
    raw_text = update.message.text
    CUSTOM_CAPTION = raw_text.split(None, 1)[1]
    await update.message.reply_text(f"✅ **Puthiya Caption Set Seiyapattathu!**\n\n{CUSTOM_CAPTION}")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    status_msg = (
        f"⚙ **Current Bot Settings:**\n\n"
        f"📝 **Your Active Caption:**\n{CUSTOM_CAPTION}\n\n"
        f"ℹ️ *Note: Paazhaya captions automatically remove aagividum!*"
    )
    await update.message.reply_text(status_msg)

# --- MAIN CAPTION LOGIC (AUTO REMOVE & REPLACE) ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message: return

    # 1. File name-ai properly edupathaarku
    file_name = ""
    if message.document:
        file_name = message.document.file_name or ""
    elif message.video:
        file_name = message.video.file_name or ""

    # .mkv, .mp4 pondra extensions-ai remove seiya
    if file_name and "." in file_name:
        file_name = ".".join(file_name.split(".")[:-1])

    # 2. Paazhaya caption-ai muzhuvathaga puram thalliittu, puthiya caption-ai ready seigirathu
    final_caption = CUSTOM_CAPTION
    
    # 3. `{filename}` keyword irundhal athai original file name kooda replace seiyum
    if "{filename}" in final_caption:
        final_caption = final_caption.replace("{filename}", file_name if file_name else "File")

    try:
        # Inga paazhaya caption-guku velaiyillai, fresh formatted caption mattum update aagum
        await message.edit_caption(caption=final_caption, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error editing caption: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN missing!")
        return

    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcaption", set_caption))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_channel_post))

    print("Koyeb Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
