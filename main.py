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
import datetime
import logging
import os
import random
import telegram
import telebot

from telebot import types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from ReflectionTracker import ReflectionTracker
from CroMoonStats import CroMoonStats
from CroMoonContestSelector import CroMoonContestSelector
from TelegramMappings import User, Wallet, Session

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.

api_key = os.environ.get('API_KEY', 'NONE')
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(api_key, state_storage=state_storage)
cromoon = CroMoonStats()

BOT_DONATION_ADDRESS = '0x28f9726A63000224f0D6A1FD406F9Eb71439F6Cc Cronos/Ethereum ONLY'

user_data = {}


# States group.
class ContestStates(StatesGroup):
    start_time = State()
    end_time = State()
    embargo_end_time = State()
    low_number = State()
    high_number = State()
    confirmation = State()


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
<b><u>Reflections</u></b>: Half of the tax is automatically distributed to all token holders. Paid automatically on every transaction. There is not a transaction visible in explorer, you may screenshot your wallet and check again later. Or check out <a href='t.me/CroMoon_Statbot'>reflections bot</a> to see yours!
<b><u>LP acquisition</u></b>: The other half of the tax is added to the Liquidity Pool.
<b><u>Afterburner</u></b>: Randomly, once a week, half of LP acquired (2.5% of total) by taxes are burned. The CRO is used to buy more MOON which is also burned.
<b><u>Blackhole</u></b>: Since a dead wallet is also a token holder, it gains reflections along with other holders.
<a href="https://medium.com/@CroMoon?p=1a9a3208e548">Addition details in Medium</a>
'''

YOU_DID_GET_REFLECTIONS = """
Every wallet that holds MOON gets reflections with every buy and sell.
There are <u>no transactions visible in explorer</u>.
However, your token balance <u>has grown</u>!
You can verify that with screenshotting your wallet or using our <a href="t.me/CroMoon_Statbot">reflection bot</a>.
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
    bot.reply_to(message, YOU_DID_GET_REFLECTIONS, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)


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
        'NOTE: Now shows combined Crodex and MMF Volume'
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
                             'Your CroMoon is currently worth (USD): {}\n<i>BETA: Values may be incorrect.</i>'.format(
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


def check_cancel_steps(message):
    answer = message.text
    if answer == u'cancel':
        bot.reply_to(message, "OK, I cancelled the contest.  Feel free to start over any time")
        bot.delete_state(message.from_user.id, message.chat.id)
        return True
    return False


@bot.message_handler(commands=['runcontest'], is_chat_admin=True)
def pick_winner(message):
    pass
    bot.reply_to(message, """\
<u>Let's get this contest started</u>!

I will gather some information and make it happen.
You can type '<b>cancel</b>' at any time to quit this contest setup.

First, tell me the start time (in <a href="https://www.epochconverter.com/">epoch</a>)    
    """, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    bot.set_state(message.from_user.id, ContestStates.start_time.name, message.chat.id)


@bot.message_handler(state=ContestStates.start_time.name)
def process_start_time_step(message):
    if check_cancel_steps(message):
        return
    try:
        if message.text == u'cheat':
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['start_time'] = datetime.datetime.fromtimestamp(1644505227)
                data['end_time'] = datetime.datetime.fromtimestamp(1644516027)
                data['embargo_end_time'] = datetime.datetime.fromtimestamp(1644516027)
                data['low_number'] = 50979881731
                data['high_number'] = 50979881732
            bot.reply_to(message, "Say '<b>pick</b>' to cheat")
            bot.set_state(message.from_user.id, ContestStates.confirmation.name, message.chat.id)
            return
        time = int(message.text)
        epoch_time = datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['start_time'] = epoch_time
        bot.reply_to(message, "What is the end time of the contest?")
        bot.set_state(message.from_user.id, ContestStates.end_time.name, message.chat.id)
    except Exception as e:
        bot.reply_to(message, "That didn't look like a time to me, please try giving start time again")


@bot.message_handler(state=ContestStates.end_time.name)
def process_end_time_step(message):
    if check_cancel_steps(message):
        return
    try:
        time = int(message.text)
        epoch_time = datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['end_time'] = epoch_time
        bot.reply_to(message, "What is the end of the no-sale window, or 'now'?")
        bot.set_state(message.from_user.id, ContestStates.embargo_end_time.name, message.chat.id)
    except Exception as e:
        bot.reply_to(message, "That didn't look like a time to me, please try giving end time again")


@bot.message_handler(state=ContestStates.embargo_end_time.name)
def process_embargo_end_time_step(message):
    if check_cancel_steps(message):
        return
    try:
        if message.text == u'now':
            epoch_time = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            time = int(message.text)
            epoch_time = datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['embargo_end_time'] = epoch_time
        bot.reply_to(message, """
Now let's pick our purchase target. We will pick a random number between two numbers...
What is the low number?      
        """)
        bot.set_state(message.from_user.id, ContestStates.low_number.name, message.chat.id)
    except Exception as e:
        bot.reply_to(message,
                     "That didn't look like number to me, please try giving end of the no sale window again")


@bot.message_handler(state=ContestStates.low_number.name)
def process_low_range_step(message):
    if check_cancel_steps(message):
        return
    try:
        number = float(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['low_number'] = number
        bot.reply_to(message, """
What is the high number?      
        """)
        bot.set_state(message.from_user.id, ContestStates.high_number.name, message.chat.id)
    except Exception as e:
        bot.reply_to(message, "That didn't look like number to me, please try giving me a low number again")


@bot.message_handler(state=ContestStates.high_number.name)
def process_high_range_step(message):
    if check_cancel_steps(message):
        return
    try:
        number = float(message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['high_number'] = number
            contest_data = data
        bot.reply_to(message, """
Alright! We are almost ready to run the contest.
Start Time: {start_time}
End Time: {end_time}
End of Sales Embargo: {embargo_end_time}
Target is a number between {low_number:,.2f} and {high_number:,.2f}      

If this looks right, please type '<b>pick</b>'
If not, type '<b>cancel</b>' and then start over
        """.format(start_time=contest_data['start_time'].strftime('%c %Z'),
                   end_time=contest_data['end_time'].strftime('%c %Z'),
                   embargo_end_time=contest_data['embargo_end_time'].strftime('%c %Z'),
                   low_number=contest_data['low_number'],
                   high_number=contest_data['high_number']
                   ), parse_mode=telegram.ParseMode.HTML)
        bot.set_state(message.from_user.id, ContestStates.confirmation.name, message.chat.id)
    except Exception as e:
        logger.exception(e)
        bot.reply_to(message, "That didn't look like number to me, please try giving me a high number again")


@bot.message_handler(state=ContestStates.confirmation.name)
def process_confirm_step(message):
    if check_cancel_steps(message):
        return
    try:
        answer = message.text
        if answer == u'pick':
            bot.send_chat_action(message.chat.id, 'typing')
            bot.reply_to(message, "Running the selector....please wait")
            bot.send_chat_action(message.chat.id, 'typing')
            single_winner_found = False
            contest = None
            while not single_winner_found:
                with bot.retrieve_data(message.from_user.id, message.chat.id) as contest_data:
                    contest = CroMoonContestSelector(start_time=contest_data['start_time'].timestamp(),
                                                     end_time=contest_data['end_time'].timestamp(),
                                                     sale_embargo=contest_data['embargo_end_time'].timestamp(),
                                                     min_num=contest_data['low_number'],
                                                     max_num=contest_data['high_number']
                                                     )
                if not contest.is_tie:
                    single_winner_found = True
            response = """
Congratulations to <a href="https://cronoscan.com/token/0x7d30c36f845d1dee79f852abf3a8a402fadf3b53?a={wallet}">{wallet}</a>!!

The random MOON target was: {target:,.2f}
The winner bought: {purchased:,.2f}
They were only off by: {off_by:,.2f}
The transaction hash is: <a href="https://cronoscan.com/tx/{txn}">{txn}</a>

All of this can be verified on the blockchain using <a href="https://cronoscan.com">cronoscan.com</a>
            """.format(wallet=contest.winning_wallets[0],
                       target=contest.target,
                       purchased=contest.winners[0]['tokens'],
                       off_by=contest.off_by,
                       txn=contest.winners[0]['txn'],
                       )
            bot.send_message(message.chat.id, response, parse_mode=telegram.ParseMode.HTML,
                             disable_web_page_preview=True)
            bot.delete_state(message.from_user.id, message.chat.id)
        else:
            raise Exception("Only pick or cancel are accepted here")
    except Exception as e:
        logger.exception(e)
        bot.reply_to(message, "Please say '<b>pick</b>' or '<b>cancel</b>'", parse_mode=telegram.ParseMode.HTML)


def main():
    """Start the bot."""
    global cromoon

    bot.add_custom_filter(custom_filters.IsAdminFilter(bot))
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling()


if __name__ == '__main__':
    main()
