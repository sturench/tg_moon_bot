"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from CroMoonStats import CroMoonStats

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
api_key = os.environ.get('API_KEY', 'NONE')
cromoon = CroMoonStats()


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('At this point, you can just type /stats')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_stats(update, context):
    reply_lines = [
        '<b><u>CroMoon Statistics</u></b> <i>(updated every 5 minutes)</i>\n',
        'Current price:                 ${}'.format(f'{cromoon.get_current_price():.12f}'),
        'Current MC:                    ${}'.format(f'{cromoon.get_market_cap():,.2f}'),
        'Burn wallet (0x0dead):   {} ({})'.format(f'{cromoon.get_percent_burned():.2%}',
                                                  cromoon.get_dead_wallet_string()),
    ]
    update.message.reply_text('\n'.join(reply_lines), parse_mode=telegram.ParseMode.HTML)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(api_key, use_context=True)
    global cromoon

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    # dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("stats", get_stats))

    # log all errors
    dp.add_error_handler(error)

    cromoon = CroMoonStats()

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
