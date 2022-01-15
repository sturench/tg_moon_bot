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

TOKENOMICS_TEXT = '''
Token transfers incur a 10% fee.

<b><u>Reflection</u></b> — Holders earn passive rewards through static reflection as their balance of CroMoon grows. No action is required by the token holders to gain these reflections.

<b><u>Liquidity Pool Acquisition</u></b> — A percentage of all transfer transactions is added to the liquidity pool. To keep the liquidity pool balanced 2.5% is added to the CRO token and 2.5% is added to the CroMoon token. The recipient of the LP units is the CroMoon team. To keep the funds safe we will add half of the 5% Liquidity Acquisition to the Liquidity Locker every week. The other half will be used for our Afterburner Effect (explained below)

<b><u>Afterburner</u></b> - Once a week, half of the LP tokens produced by the contract will be withdrawn into equivalent portions of CroMoon and CRO. The CroMoon portion will be burned, and the CRO will immediately be used to purchase CroMoon from the market. The purchased CroMoon will then also be burned.

Afterburner events will happen once a week on an entirely random basis and will be announced only after the above process is fully complete in order to prevent any manipulation or timed buying/selling.

The Afterburner program will simultaneously induce community hype whilst creating a significant positive price action and providing a burn outlet for the contract-generated LP tokens.

<b><u>Blackhole</u></b> - Shortly after launch the team burned a substantial amount of the supply. By doing so we created a ‘blackhole’ which will, thanks to the reflection mechanism, suck CroMoon tokens out of the supply and burn them. This turns CroMoon into a deflationary token, because every transaction some CroMoon gets send to the burn wallet.

<a href="https://medium.com/@CroMoon?p=1a9a3208e548">Medium Article</a>
'''

TOKENOMICS_SHORT = '''
<b><u>Transaction Tax</u></b>: 10%
<b><u>Reflections</u></b>: Half of the tax is automatically distributed to all token holders.
<b><u>LP acquisition</u></b>: The other half of the tax is added to the Liquidity Pool.
<b><u>Afterburner</u></b>: Randomly, once a week, half of LP acquired (2.5% of total) by taxes are burned. The CRO is used to buy more MOON which is also burned.
<b><u>Blackhole</u></b>: Since a dead wallet is also a token holder, it gains reflections along with other holders.
<a href="https://medium.com/@CroMoon?p=1a9a3208e548">Addition details in Medium</a>
'''


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('At this point, you can just type /stats or /tokenomics')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def get_stats(update, context):
    reply_lines = [
        '<b><u>CroMoon Statistics</u></b> <i>(updated every 5 minutes)</i>\n',
        'Current price:          ${} ({} 24H)'.format(cromoon.price, cromoon.change_24),
        'Current MC:             ${}'.format(cromoon.market_cap),
        'Holders:                   {}'.format(cromoon.holder_count),
        '24H Volume:            ${}'.format(cromoon.volume_24),
        'Burn wallet (0x0dead):  {} ({})'.format(cromoon.burn_percent,
                                                 cromoon.burn_tokens),
    ]
    update.message.reply_text('\n'.join(reply_lines), parse_mode=telegram.ParseMode.HTML)


def tokenomics_detail(update, context):
    update.message.reply_text(TOKENOMICS_TEXT, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


def tokenomics(update, context):
    update.message.reply_text(TOKENOMICS_SHORT, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


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
    dp.add_handler(CommandHandler("tokenomics_detail", tokenomics_detail))
    dp.add_handler(CommandHandler("tokenomics", tokenomics))

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
