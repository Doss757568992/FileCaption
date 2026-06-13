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

# Inga multiple rules list-aga save aagum
REPLACE_RULES = {} 

# Global queue for handling 100+ files safely
message_queue = asyncio.Queue()

# --- HELPER FUNCTION TO PREVENT ENTITY ERRORS ---
def convert_markdown_to_html(text: str) -> str:
    """
    User template-la ulla **bold** markdown text-ai safe-ana HTML tags-ga
    maathuthu, filename-la ulla extra characters-al error varama thadukum.
    """
    if not text:
        return ""
    
    # Simple Markdown text conversion logic
    if "**" in text:
        parts = text.split("**")
        html_text = ""
        for idx, part in enumerate(parts):
            if idx % 2 == 1:
                html_text += f"<b>{part}</b>"
            else:
                html_text += part
        return html_text
    return text

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
        "👋 **Welcome to Multi-Replace Auto Caption Bot!**\n\n"
        "**Commands:**\n"
        "➡ `/setcaption <text>` - New caption layout (Use `{filename}`)\n"
        "➡ `/setreplace old1|new1, old2|new2` - Multiple text replace seiya\n"
        "➡ `/setremove old1, old2, old3` - Multiple text-ai remove seiya\n"
        "➡ `/clear` - Replace rules anaithaiyum azhika\n"
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
    global REPLACE_RULES
    if update.effective_user.id != ADMIN_ID: return
    raw_text = update.message.text.split(None, 1)
    if len(raw_text) < 2:
        await update.message.reply_text("❌ Usage: `/setreplace old1|new1, old2|new2`")
        return
    
    pairs = raw_text[1].split(",")
    new_rules = {}
    for pair in pairs:
        if "|" in pair:
            parts = pair.split("|")
            new_rules[parts[0].strip()] = parts[1].strip()
            
    REPLACE_RULES.update(new_rules)
    
    msg = "✅ **Added Replace Rules:**\n"
    for k, v in new_rules.items():
        msg += f"🔍 `{k}` ➡ 🔄 `{v}`\n"
    await update.message.reply_text(msg)

async def set_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REPLACE_RULES
    if update.effective_user.id != ADMIN_ID: return
    raw_text = update.message.text.split(None, 1)
    if len(raw_text) < 2:
        await update.message.reply_text("❌ Usage: `/setremove old1, old2, old3`")
        return
    
    items = raw_text[1].split(",")
    new_rules = {}
    for item in items:
        if item.strip():
            new_rules[item.strip()] = ""
            
    REPLACE_RULES.update(new_rules)
    
    msg = "✅ **Added Remove Rules:**\n"
    for k in new_rules.keys():
        msg += f"❌ Removed: `{k}`\n"
    await update.message.reply_text(msg)

async def clear_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REPLACE_RULES
    if update.effective_user.id != ADMIN_ID: return
    REPLACE_RULES = {}
    await update.message.reply_text("🗑️ **All replace and remove rules cleared!**")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    rules_text = ""
    if REPLACE_RULES:
        for k, v in REPLACE_RULES.items():
            rules_text += f"• `{k}` ➡ `{v if v else '[REMOVE]'}`\n"
    else:
        rules_text = "None"
        
    status_msg = (
        f"⚙ **Current Bot Settings:**\n\n"
        f"📝 **Caption Layout:**\n{CUSTOM_CAPTION}\n\n"
        f"🔄 **Active Replace/Remove Rules:**\n{rules_text}\n\n"
        f"⚡️ *Queue Status: Bulk handling activated.*"
    )
    await update.message.reply_text(status_msg)

# --- ADVANCED QUEUE WORKER ---
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

            # MULTI-REPLACE/REMOVE LOGIC
            if file_name and REPLACE_RULES:
                for target_text, replacement in REPLACE_RULES.items():
                    if target_text in file_name:
                        file_name = file_name.replace(target_text, replacement)

            final_caption = CUSTOM_CAPTION
            if "{filename}" in final_caption:
                final_caption = final_caption.replace("{filename}", file_name.strip() if file_name else "File")

            # Markdown asterisks-ai HTML format-guku convert seigirom
            final_caption = convert_markdown_to_html(final_caption)

            # parse_mode HTML-aga maathiyathaal filename-la ulla brackets-al error varathu
            await message.edit_caption(caption=final_caption, parse_mode="HTML")
            await asyncio.sleep(3.5) # Anti-flood delay for 100+ files
            
        except Exception as e:
            logging.error(f"Error in queue worker: {e}")
            if "Flood control exceeded" in str(e) or "RetryAfter" in str(e):
                await asyncio.sleep(20)
        finally:
            message_queue.task_done()

# --- CHANNEL POST RECEIVER ---
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message: return
    
    if message.photo or message.video or message.document:
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
    application.add_handler(CommandHandler("clear", clear_rules))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_channel_post))

    loop = asyncio.get_event_loop()
    loop.create_task(queue_worker())

    print("Koyeb Multi-Replace Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
