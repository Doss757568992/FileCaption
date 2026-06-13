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

CUSTOM_CAPTION = "✨ **Join our main channel for more updates!** ✨"
FIND_TEXT = ""
REPLACE_TEXT = ""

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
        "➡ `/setcaption <text>` - New caption set seiya (Use `{filename}` for file name)\n"
        "➡ `/setreplace <find> | <replace>` - Text-ai replace seiya\n"
        "➡ `/setremove <text>` - Oru text-ai remove seiya\n"
        "➡ `/status` - Current settings-ai parka"
    )

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CUSTOM_CAPTION
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setcaption text`")
        return
    # Message text-il irundhu command-ai mattum thookittu full caption-ai line breaks kooda edukum
    raw_text = update.message.text
    CUSTOM_CAPTION = raw_text.split(None, 1)[1]
    await update.message.reply_text(f"✅ **New Caption Set:**\n\n{CUSTOM_CAPTION}")

async def set_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIND_TEXT, REPLACE_TEXT
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("❌ Usage: `/setreplace old | new`")
        return
    parts = text.split("|")
    FIND_TEXT = parts[0].strip()
    REPLACE_TEXT = parts[1].strip()
    await update.message.reply_text(f"✅ **Find & Replace Set:**\n🔍 Find: `{FIND_TEXT}`\n🔄 Replace: `{REPLACE_TEXT}`")

async def set_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIND_TEXT, REPLACE_TEXT
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setremove text`")
        return
    FIND_TEXT = " ".join(context.args)
    REPLACE_TEXT = ""
    await update.message.reply_text(f"✅ **Text to Remove Set:** `{FIND_TEXT}`")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    status_msg = (
        f"⚙ **Current Bot Settings:**\n\n"
        f"📝 **Caption:**\n{CUSTOM_CAPTION}\n\n"
        f"🔍 **Find Text:** `{FIND_TEXT if FIND_TEXT else 'None'}`\n"
        f"🔄 **Replace/Remove Text:** `{REPLACE_TEXT if FIND_TEXT else 'None'}`"
    )
    await update.message.reply_text(status_msg)

# --- MAIN CAPTION LOGIC ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message: return

    # File name edukuratha check seiya
    file_name = ""
    if message.document:
        file_name = message.document.file_name or ""
    elif message.video:
        file_name = message.video.file_name or ""

    # .mkv, .mp4 extension-ai remove seiya (if exists)
    if file_name and "." in file_name:
        file_name = ".".join(file_name.split(".")[:-1])

    original_caption = message.caption or ""
    
    # 1. First Find and Replace/Remove process-ai seiyum
    if FIND_TEXT and (FIND_TEXT in original_caption):
        working_caption = original_caption.replace(FIND_TEXT, REPLACE_TEXT)
    else:
        working_caption = original_caption

    # 2. Custom Caption logic with {filename} variable replacement
    current_custom = CUSTOM_CAPTION
    if "{filename}" in current_custom:
        current_custom = current_custom.replace("{filename}", file_name if file_name else "File")

    # 3. Line breaks properly maintain panni combine seiyum
    if working_caption:
        # Paazhaya caption-gukum puthiya caption-gukum naduvil clear gap vizhum
        final_caption = f"{working_caption}\n\n{current_custom}"
    else:
        final_caption = current_custom

    try:
        await message.edit_caption(caption=final_caption)
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
    application.add_handler(CommandHandler("setreplace", set_replace))
    application.add_handler(CommandHandler("setremove", set_remove))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_channel_post))

    print("Koyeb Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
