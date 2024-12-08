from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import requests

# Replace with your bot token
BOT_TOKEN = "7709293848:AAGFYabjOhNuVAlxQBDWeDLCOXoCGbg0qos"
OTP_API_URL = "https://otp.glitchy.workers.dev/send?phone={phone}"

# Define states for the conversation
ASK_MESSAGE, ASK_PHONE, ASK_COUNT = range(3)

def start(update, context):
    """Start command handler"""
    update.message.reply_text("Welcome! Please provide the custom message you'd like to send along with the OTP.")
    return ASK_MESSAGE

def ask_message(update, context):
    """Store the custom message and ask for the phone number"""
    context.user_data["custom_message"] = update.message.text.strip()
    update.message.reply_text("Got it! Now, please provide the phone number to send the OTP.")
    return ASK_PHONE

def ask_phone(update, context):
    """Store the phone number and ask for the number of OTPs to send"""
    context.user_data["phone_number"] = update.message.text.strip()
    update.message.reply_text("How many OTPs would you like to send?")
    return ASK_COUNT

def ask_count(update, context):
    """Send the requested number of OTPs along with the custom message"""
    try:
        count = int(update.message.text.strip())
        phone_number = context.user_data.get("phone_number", "")
        custom_message = context.user_data.get("custom_message", "")
        
        for _ in range(count):
            # Call the Send OTP API
            response = requests.get(OTP_API_URL.format(phone=phone_number))
            if response.status_code != 200 or response.json().get("status") != 1:
                update.message.reply_text(f"Failed to send OTP to {phone_number}.")
                return ConversationHandler.END
        
        update.message.reply_text(f"Success! {count} OTPs have been sent to {phone_number}.\n\nCustom Message: {custom_message}")
    except ValueError:
        update.message.reply_text("Please enter a valid number.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")
    
    return ConversationHandler.END

def cancel(update, context):
    """Cancel the conversation"""
    update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    """Main function to set up the bot"""
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, ask_message)],
            ASK_PHONE: [MessageHandler(Filters.text & ~Filters.command, ask_phone)],
            ASK_COUNT: [MessageHandler(Filters.text & ~Filters.command, ask_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
  
