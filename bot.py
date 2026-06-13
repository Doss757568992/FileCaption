import os
import logging
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION ---
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789")) 

CUSTOM_CAPTION = "🎬 **File Name:** {filename}\n\n✨ **Join our main channel for more updates!** ✨"
FIND_TEXT = ""
REPLACE_TEXT = ""

# Global queue for handling 100+ files safely
message_queue = asyncio.Queue()

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
        "👋 **Welcome to Auto Caption Bot (Ultra 100+ Bulk Version)!**\n\n"
        "**Commands:**\n"
        "➡ `/setcaption <text>` - New caption layout set seiya (Use `{filename}`)\n"
        "➡ `/setreplace <find> | <replace>` - File name-kul ulla text-ai replace seiya\n"
        "➡ `/setremove <text>` - File name-kul ulla text-ai remove seiya\n"
        "➡ `/status` - Current settings-ai parka"
    )

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CUSTOM_CAPTION
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setcaption text`")
        return
    raw_text = update.message.text
    CUSTOM_CAPTION = raw_text.split(None, 1)[1]
    await update.message.reply_text(f"✅ **New Caption Layout Set:**\n\n{CUSTOM_CAPTION}")

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
    await update.message.reply_text(f"✅ **File Name Replace Set:**\n🔍 Find: `{FIND_TEXT}`\n🔄 Replace: `{REPLACE_TEXT}`")

async def set_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIND_TEXT, REPLACE_TEXT
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setremove text`")
        return
    FIND_TEXT = " ".join(context.args)
    REPLACE_TEXT = ""
    await update.message.reply_text(f"✅ **File Name Remove Set:** `{FIND_TEXT}`")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    status_msg = (
        f"⚙ **Current Bot Settings:**\n\n"
        f"📝 **Caption Layout:**\n{CUSTOM_CAPTION}\n\n"
        f"🔍 **File Name Find:** `{FIND_TEXT if FIND_TEXT else 'None'}`\n"
        f"🔄 **File Name Replace/Remove:** `{REPLACE_TEXT if FIND_TEXT else 'None'}`\n\n"
        f"⚡️ *Queue Status: Handling massive bulk entries safely.*"
    )
    await update.message.reply_text(status_msg)

# --- ADVANCED QUEUE WORKER (Handles 100+ Files without Skipping) ---
async def queue_worker():
    while True:
        message = await message_queue.get()
        try:
            file_name = ""
            if message.document:
                file_name = message.document.file_name or ""
            elif message.video:
                file_name = message.video.file_name or ""

            if file_name and "." in file_name:
                file_name = ".".join(file_name.split(".")[:-1])

            # File Name Replace/Remove Logic
            if file_name and FIND_TEXT and (FIND_TEXT in file_name):
                file_name = file_name.replace(FIND_TEXT, REPLACE_TEXT)

            final_caption = CUSTOM_CAPTION
            if "{filename}" in final_caption:
                final_caption = final_caption.replace("{filename}", file_name if file_name else "File")

            # Telegram server block aagama iruka steady line edit
            await message.edit_caption(caption=final_caption, parse_mode="Markdown")
            
            # Massive files-guku continuous 3.5 seconds loop gap adiyatha maari pathukum
            await asyncio.sleep(3.5)
            
        except Exception as e:
            logging.error(f"Error in queue worker: {e}")
            # Flood wait control block vantha extra cooldown time
            if "Flood control exceeded" in str(e) or "RetryAfter" in str(e):
                await asyncio.sleep(20)
        finally:
            message_queue.task_done()

# --- CHANNEL POST RECEIVER ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message: return
    
    if message.photo or message.video or message.document:
        # 100 files vanthalum sariya task queue-la save aagidum
        await message_queue.put(message)

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

    # Background infinite loop start
    loop = asyncio.get_event_loop()
    loop.create_task(queue_worker())

    print("Koyeb High-Performance Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
