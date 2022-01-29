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
import random
import telegram
import telebot

from telebot import types

from ReflectionTracker import ReflectionTracker
from CroMoonStats import CroMoonStats
from TelegramMappings import User, Wallet, Session

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.

api_key = os.environ.get('API_KEY', 'NONE')
bot = telebot.TeleBot(api_key)
cromoon = CroMoonStats()

BOT_DONATION_ADDRESS = '0x28f9726A63000224f0D6A1FD406F9Eb71439F6Cc'

user_data = {}

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
<b><u>Reflections</u></b>: Half of the tax is automatically distributed to all token holders. Paid automatically on every transaction. There is not a transaction visible in explorer, you may screenshot your wallet and check again later. Or check out /reflections to see yours!
<b><u>LP acquisition</u></b>: The other half of the tax is added to the Liquidity Pool.
<b><u>Afterburner</u></b>: Randomly, once a week, half of LP acquired (2.5% of total) by taxes are burned. The CRO is used to buy more MOON which is also burned.
<b><u>Blackhole</u></b>: Since a dead wallet is also a token holder, it gains reflections along with other holders.
<a href="https://medium.com/@CroMoon?p=1a9a3208e548">Addition details in Medium</a>
'''

YOU_DID_GET_REFLECTIONS = """
Every wallet that holds MOON gets reflections with every buy and sell.
There are <u>no transactions visible in explorer</u>.
However, your token balance <u>has grown</u>!
You can verify that with screenshotting your wallet or using our /reflection bot.
"""

HELP_MSG_without_forget = """
To get the latest stats type /stats
To read about tokenomics type /tokenomics
To track your reflections type /reflections
To check your CroMoon value type /value
To get help type /help.
"""

HELP_MSG = """
To get the latest stats - /stats
To read about tokenomics - /tokenomics
To track your reflections - /reflections
To check your CroMoon value - /value
To have me forget your wallet - /forget
To get help - /help.
"""

DONATION_MSG = """
\nIf you enjoy this bot, please consider donating something to the creator - he did this on spare time for the community ({})
""".format(BOT_DONATION_ADDRESS)

donation_message_probability = .25
stat_donation_period = 20
stat_calls = 0


def random_show_donation():
    if random.random() < donation_message_probability:
        return DONATION_MSG
    else:
        return ''


def periodic_stat_donation(message_type=None):
    if message_type == 'private':
        return random_show_donation()
    global stat_calls
    if stat_calls > 99999999:
        stat_calls = 0
    stat_calls += 1
    if stat_calls % stat_donation_period == 0:
        return DONATION_MSG
    else:
        return ""


@bot.message_handler(commands=['start', 'Start'], chat_types=['private'])
def start_command(message):
    bot.send_message(message.chat.id, 'Greetings! I can help you with CroMoon info.\n' + HELP_MSG + DONATION_MSG + '\n')
    get_wallet_response(message)


@bot.message_handler(commands=['help', 'Help'])
def help_command(message):
    """Send a message when the command /help is issued."""
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton('Message the developer', url='telegram.me/ConsiderChaos')
    )
    bot.send_message(message.chat.id, HELP_MSG + DONATION_MSG, reply_markup=keyboard)


@bot.message_handler(
    commands=['yesyouhave', 'youhave', 'where_are_my_reflections', 'yes_you_have', 'you_got_reflections'])
def explain_they_got_reflections(message):
    bot.reply_to(message, YOU_DID_GET_REFLECTIONS, parse_mode=telegram.ParseMode.HTML)


@bot.message_handler(commands=['stats', 'Stats'])
def get_stats(message):
    reply_lines = [
        '<b><u>CroMoon Statistics</u></b> <i>(updated every 5 minutes)</i>\n',
        'Current price:          ${} ({} 24H)'.format(cromoon.price, cromoon.change_24),
        'Current MC:             ${}'.format(cromoon.market_cap),
        'Holders:                   {}'.format(cromoon.holder_count),
        '24H Volume:            ${}'.format(cromoon.volume_24),
        'Burn wallet (0x0dead):  {} ({})'.format(cromoon.burn_percent,
                                                 cromoon.burn_tokens),
    ]
    bot.send_message(
        message.chat.id,
        '\n'.join(reply_lines) + periodic_stat_donation(message.chat.type),
        parse_mode=telegram.ParseMode.HTML,
        disable_web_page_preview=True)


@bot.message_handler(commands=['tokenomics_detail'])
def tokenomics_detail(message):
    bot.send_message(
        message.chat.id, TOKENOMICS_TEXT, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


@bot.message_handler(commands=['tokenomics', 'Tokenomics'])
def tokenomics(message):
    bot.send_message(
        message.chat.id, TOKENOMICS_SHORT, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


@bot.message_handler(commands=['reflections', 'reflection', 'r', 'R', 'Reflections', 'Reflection'])
def reflections_command(message):
    wallet = get_user_wallet(message.from_user.id)
    if wallet is not None:
        if message.chat.type != "private":
            pre_text = 'Hey, I moved our chat to DM for privacy and to reduce clutter in the main channel\n'
            bot.reply_to(message, pre_text, parse_mode=telegram.ParseMode.HTML)
        msg_dest = message.from_user.id
        tracker = get_reflection_tracker(message.from_user.id)  # type: ReflectionTracker
        if tracker is not None:
            bot.send_message(msg_dest, '\n'.join(tracker.reflection_stat_str) + random_show_donation(),
                             parse_mode=telegram.ParseMode.HTML,
                             disable_web_page_preview=True)
        else:
            initialize_user(msg_dest)
            bot.send_message(msg_dest, "Please set your wallet first")
    else:
        get_wallet_response(message)


@bot.message_handler(commands=['value', 'v', 'Value'])
def value_command(message):
    logger.debug('About to initialize user in value_command')
    initialize_user(message.from_user.id)
    logger.debug('user initialized in value_command')
    wallet = get_user_wallet(message.from_user.id)
    logger.debug('got wallet: {}'.format(wallet))
    try:
        price = float(cromoon.price)
    except Exception as e:
        logger.exception("Price not a float: {}".format(e))
        price = None

    if wallet is not None:
        if message.chat.type != "private":
            pre_text = 'Hey, I moved our chat to DM for privacy and to reduce clutter in the main channel\n'
            bot.reply_to(message, pre_text, parse_mode=telegram.ParseMode.HTML)
        msg_dest = message.from_user.id
        logger.debug('Getting tracker in value_command')
        tracker = get_reflection_tracker(message.from_user.id)
        logger.debug('Tracker in value_command: {}'.format(tracker))
        if tracker is not None:
            if price is not None:
                value = tracker.balance * price
                ret_val = f'${value:,.2f}'
            else:
                ret_val = 'Unavailable'
            bot.send_message(msg_dest,
                             'Your CroMoon is currently worth: {}\n<i>BETA: Values may be incorrect.</i>'.format(
                                 ret_val) + random_show_donation(),
                             parse_mode=telegram.ParseMode.HTML,
                             disable_web_page_preview=True)
        else:
            logger.debug('About to send request to set wallet')
            bot.send_message(msg_dest, "Please set your wallet first")
    else:
        get_wallet_response(message)


def get_wallet_response(message):
    if message.chat.type == "private":
        # ask for wallet
        wait_for_wallet(message.from_user.id)
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id,
                         "What wallet do you want to track reflections and value on?\nYou have to copy/paste your PUBLIC wallet address into the chat.  I will only start showing the good stuff after you see a message that I set your wallet!",
                         parse_mode=telegram.ParseMode.HTML)
    else:
        # DM the person and ask
        wait_for_wallet(message.from_user.id)
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(telebot.types.InlineKeyboardButton('Open My DM', url='t.me/CroMoon_Statbot'))
        bot.reply_to(message, "For privacy reasons, let's move to <a href='t.me/CroMoon_Statbot'>DM</a>\n" +
                     "When you get there, type /reflections or /start to get going.\n<i>If you see this message and you weren't the one to call me, you can still click the DM link</i>",
                     reply_markup=keyboard, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


# @bot.callback_query_handler(func=lambda call: True)
# def iq_callback(query):
#     data = json.loads(query.data)
#     action = data.get('action')
#     user_id = data.get('user_id')
#     if action == 'set-wallet':
#         set_wallet_callback(query)
#     if action == 'get-reflections':
#         get_reflections_callback(query, user_id)
#     if action == 'forget-wallet':
#         forget_wallet_callback(query, user_id)


# def forget_wallet_callback(query, user_id):
#     bot.answer_callback_query(query.id)
#     send_wallet_forgotten(query.message, user_id)


@bot.message_handler(commands=['forget', 'f', 'Forget'])
def send_wallet_forgotten(message):
    userid = initialize_user(message.from_user.id)
    with Session() as session:
        user = session.query(User).filter(User.id == userid).first()
        try:
            user.wallets = []
        except Exception as e:
            logger.exception(e)
            session.rollback()
            bot.reply_to(message, "Something went wrong forgetting you.  Try again.",
                         parse_mode=telegram.ParseMode.HTML)
        else:
            session.commit()
            user_data.pop(user.telegram_id, None)
            bot.reply_to(message, "You have been forgotten", parse_mode=telegram.ParseMode.HTML)
        session.close()


def set_wallet_callback(query):
    bot.answer_callback_query(query.id)
    send_wallet_request(query.message)


def get_reflections_callback(query, user_id):
    bot.answer_callback_query(query.id)
    send_reflection_request(query.message, user_id)


def send_reflection_request(message, user_id):
    bot.send_chat_action(message.chat.id, 'typing')
    tracker = get_reflection_tracker(user_id)
    if tracker is not None:
        bot.send_message(message.chat.id, '\n'.join(tracker.reflection_stat_str), parse_mode=telegram.ParseMode.HTML,
                         disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "Please set your wallet first")


def send_wallet_request(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id,
                     "What is the wallet you want to track reflections and value on?\n\nYou have to copy/paste your PUBLIC wallet address into the chat.  I will only start showing the good stuff after you see a message that I set your wallet!",
                     parse_mode=telegram.ParseMode.HTML)


@bot.message_handler(regexp='^0x[a-fA-F0-9]{40}$', chat_types=['private'])
def wallet_address_message(message):
    if is_user_waiting_for_wallet(message.from_user.id):
        set_user_wallet(message.from_user.id, message.text)
        bot.send_message(
            message.chat.id, "I set your wallet address to {}\n".format(
                message.text) + "You can now get reflections by typing /reflections\n" + "/help is also available" +
                             DONATION_MSG,
            parse_mode=telegram.ParseMode.HTML,
            disable_web_page_preview=True, reply_markup=types.ReplyKeyboardRemove())


def initialize_user(user_id):
    session = Session()
    users = session.query(User).filter(User.telegram_id == user_id).all()
    user = None
    if len(users) > 1:
        logger.error("Too Many Users with id: {}".format(user_id))
    if len(users) == 0:
        # No users
        user_data[user_id] = {
            'wallet': None,
            'waiting_for_wallet': False,
            'tracker': None
        }
        # session.begin()
        user = User(user_id)
        session.add(user)
        session.commit()
    if len(users) == 1:
        user = users[0]
        # User exists
        user_data[user_id] = {
            'wallet': None,
            'waiting_for_wallet': True,
            'tracker': None
        }
        if len(user.wallets) == 1:
            user_data[user_id]['wallet'] = user.wallets[0]  # type: [Wallet]
            user_data[user_id]['waiting_for_wallet'] = False
            user_data[user_id]['tracker'] = ReflectionTracker(user.wallets[0].wallet_address, cromoon=cromoon)
    userid = user.id
    session.close()
    return userid


def user_exists(user_id) -> bool:
    return user_id in user_data


def wait_for_wallet(user_id):
    if not user_exists(user_id):
        initialize_user(user_id)
    user_data[user_id]['waiting_for_wallet'] = True


def get_db_user(user_id):
    session = Session()
    users = session.query(User).filter(User.telegram_id == user_id).all()
    if len(users) > 1:
        logger.error("Too Many Users with id: {}".format(user_id))
    if len(users) == 0:
        return None
    if len(users) == 1:
        return users[0]


def set_user_wallet(user_id, wallet_address):
    userid = initialize_user(user_id)
    with Session() as session:
        try:
            wallet = Wallet(wallet_address)
            session.add(wallet)
        except Exception as e:
            logger.exception(e)
            session.rollback()
            session.clos()
            return
        else:
            session.commit()

        try:
            user = session.query(User).filter(User.id == userid).first()
            user.wallets.append(wallet)
            session.add(user)
        except Exception as e:
            logger.exception(e)
            session.rollback()
        else:
            session.commit()

    user_data[user_id]['wallet'] = wallet_address
    user_data[user_id]['tracker'] = ReflectionTracker(wallet_address, cromoon=cromoon)
    user_data[user_id]['waiting_for_wallet'] = False


def is_user_waiting_for_wallet(user_id):
    initialize_user(user_id)
    return user_data[user_id]['waiting_for_wallet']


def get_user_wallet(user_id):
    if user_data.get(user_id, {}).get('wallet') is None:
        initialize_user(user_id)
    return user_data[user_id]['wallet']


def get_reflection_tracker(user_id):
    if user_data.get(user_id, {}).get('tracker') is None:
        initialize_user(user_id)
    return user_data[user_id]['tracker']


def main():
    """Start the bot."""
    global cromoon

    bot.infinity_polling()
    # while True:
    #     try:
    #         bot.infinity_polling(non_stop=True)
    #         bot.close()
    #         bot.stop_bot()
    #     except Exception as e:
    #         logger.error(e)


if __name__ == '__main__':
    main()
