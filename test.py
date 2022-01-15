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


def get_stats():
    reply_lines = [
        '<b><u>CroMoon Statistics</u></b> <i>(updated every 5 minutes)</i>\n',
        'Current price:          ${} ({} 24H)'.format(cromoon.price, cromoon.change_24),
        'Current MC:             ${}'.format(cromoon.market_cap),
        'Holders:                   {}'.format(cromoon.holder_count),
        '24H Volume:             ${}'.format(cromoon.volume_24),
        'Burn wallet (0x0dead):  {} ({})'.format(cromoon.burn_percent,
                                                 cromoon.burn_tokens),
    ]
    return reply_lines


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    global cromoon

    cromoon = CroMoonStats()

    res = get_stats()
    holder_count = cromoon.get_token_holder_count()
    print('\n'.join(res))


if __name__ == '__main__':
    main()
