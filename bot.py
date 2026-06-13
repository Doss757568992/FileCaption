import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION ---
# Ungal Telegram User ID-ai ingey mathavum (To find ID: @MissRose_bot-guku /id nu anupavum)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789")) 

# Default values
CUSTOM_CAPTION = "✨ **Join our main channel for more updates!** ✨"
FIND_TEXT = ""
REPLACE_TEXT = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "👋 **Welcome to Auto Caption Bot!**\n\n"
        "**Commands:**\n"
        "➡ `/setcaption <your text>` - New caption set seiya\n"
        "➡ `/setreplace <find> | <replace>` - Text-ai replace seiya\n"
        "➡ `/setremove <text>` - Oru text-ai remove seiya\n"
        "➡ `/status` - Current settings-ai parka"
    )

# --- ADMIN COMMANDS TO CHANGE SETTINGS ---

async def set_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CUSTOM_CAPTION
    if update.effective_user.id != ADMIN_ID: return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setcaption Text dynamic caption inge kudukavum`")
        return
        
    CUSTOM_CAPTION = " ".join(context.args)
    await update.message.reply_text(f"✅ **New Caption Set Successfully:**\n\n{CUSTOM_CAPTION}")

async def set_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIND_TEXT, REPLACE_TEXT
    if update.effective_user.id != ADMIN_ID: return
    
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("❌ Usage: `/setreplace old_text | new_text` (Use '|' symbol to split)")
        return
        
    parts = text.split("|")
    FIND_TEXT = parts[0].strip()
    REPLACE_TEXT = parts[1].strip()
    await update.message.reply_text(f"✅ **Find & Replace Set:**\n🔍 Find: `{FIND_TEXT}`\n🔄 Replace: `{REPLACE_TEXT}`")

async def set_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global FIND_TEXT, REPLACE_TEXT
    if update.effective_user.id != ADMIN_ID: return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setremove text_to_delete`")
        return
        
    FIND_TEXT = " ".join(context.args)
    REPLACE_TEXT = "" # Empty text means it will be removed
    await update.message.reply_text(f"✅ **Text to Remove Set:** `{FIND_TEXT}` (Ithu post-il irundhu nekkapadum)")

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    status_msg = (
        f"⚙ **Current Bot Settings:**\n\n"
        f"📝 **Caption:** {CUSTOM_CAPTION}\n"
        f"🔍 **Find Text:** `{FIND_TEXT if FIND_TEXT else 'None'}`\n"
        f"🔄 **Replace/Remove Text:** `{REPLACE_TEXT if FIND_TEXT else 'None'}`"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


# --- MAIN CAPTION LOGIC FOR CHANNELS ---

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.channel_post
    if not message:
        return

    # Check if message has media that can have caption
    if not (message.photo or message.video or message.document):
        return

    original_caption = message.caption or ""
    final_caption = ""

    # 1. Find and Replace / Remove Logic
    if FIND_TEXT and (FIND_TEXT in original_caption):
        # Text iruntha athai replace illa remove (empty string) seiyum
        final_caption = original_caption.replace(FIND_TEXT, REPLACE_TEXT)
    else:
        # Original caption kooda namma custom caption-ai add seiyum
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

    application = Application.builder().token(TOKEN).build()

    # Commands for Admin
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setcaption", set_caption))
    application.add_handler(CommandHandler("setreplace", set_replace))
    application.add_handler(CommandHandler("setremove", set_remove))
    application.add_handler(CommandHandler("status", show_status))

    # Channel post handler
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_channel_post))

    print("Advanced Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()