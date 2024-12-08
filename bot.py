from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import requests

# Replace with your bot token
BOT_TOKEN = "7709293848:AAGFYabjOhNuVAlxQBDWeDLCOXoCGbg0qos"
OTP_API_URL = "https://otp.glitchy.workers.dev/send?phone={phone}"

# Define states for the conversation
ASK_MESSAGE, ASK_PHONE, ASK_COUNT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text("Welcome! Please provide the custom message you'd like to send along with the OTP.")
    return ASK_MESSAGE

async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the custom message and ask for the phone number"""
    context.user_data["custom_message"] = update.message.text.strip()
    await update.message.reply_text("Got it! Now, please provide the phone number to send the OTP.")
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the phone number and ask for the number of OTPs to send"""
    context.user_data["phone_number"] = update.message.text.strip()
    await update.message.reply_text("How many OTPs would you like to send?")
    return ASK_COUNT

async def ask_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the requested number of OTPs along with the custom message"""
    try:
        count = int(update.message.text.strip())
        phone_number = context.user_data.get("phone_number", "")
        custom_message = context.user_data.get("custom_message", "")
        
        for _ in range(count):
            # Call the Send OTP API
            response = requests.get(OTP_API_URL.format(phone=phone_number))
            if response.status_code != 200 or response.json().get("status") != 1:
                await update.message.reply_text(f"Failed to send OTP to {phone_number}.")
                return ConversationHandler.END
        
        await update.message.reply_text(f"Success! {count} OTPs have been sent to {phone_number}.\n\nCustom Message: {custom_message}")
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    """Main function to set up the bot"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_message)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
