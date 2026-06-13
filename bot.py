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
# Koyeb bot-ai "Healthy" nu nenaika intha chinna web server thevai
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # Koyeb auto-ah 'PORT' variable tharum, illati 8080-la odum
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ADMIN COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text(
        "👋 **Welcome to Auto Caption Bot on Koyeb!**\n\n"
        "**Commands:**\n"
        "➡ `/setcaption <text>` - New caption set seiya\n"
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
    CUSTOM_CAPTION = " ".join(context.args)
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
        f"📝 **Caption:** {CUSTOM_CAPTION}\n"
        f"🔍 **Find Text:** `{FIND_TEXT if FIND_TEXT else 'None'}`\n"
        f"🔄 **Replace/Remove Text:** `{REPLACE_TEXT if FIND_TEXT else 'None'}`"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")

# --- MAIN CAPTION LOGIC ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message or not (message.photo or message.video or message.document): return

    original_caption = message.caption or ""
    final_caption = ""

    if FIND_TEXT and (FIND_TEXT in original_caption):
        final_caption = original_caption.replace(FIND_TEXT, REPLACE_TEXT)
    else:
        if original_caption:
            final_caption = f"{original_caption}\n\n{CUSTOM_CAPTION}"
        else:
            final_caption = CUSTOM_CAPTION

    try:
        await message.edit_caption(caption=final_caption, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error editing caption: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN missing!")
        return

    # Start Flask server in background thread for Koyeb Health Check
    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcaption", set_caption))
    application.add_handler(CommandHandler("setreplace", set_replace))
    application.add_handler(CommandHandler("setremove", set_remove))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_channel_post))

    print("Koyeb Compatible Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()