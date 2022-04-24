from datetime import datetime, timedelta
from random import randint

import requests

# https://api.cronoscan.com/api?module=account&action=tokentx&address=0x062F95282A797c49F0994699c2c96AE566293e0C&sort=asc&apikey=YourApiKeyToken

cromoon_contract_address = "0x7D30c36f845d1dEe79f852abF3A8A402fAdF3b53".lower()


class ReflectionTracker:
    def __init__(self, wallet_address: str, initialize_data: bool = True, cromoon=None):
        self._wallet_address = wallet_address.lower()
        self._last_block = 0
        self._purchased_balance = 0
        self._current_balance = 0
        self._last_transaction_check = datetime.fromtimestamp(0)
        self._last_balance_check = datetime.fromtimestamp(0)
        self._check_interval = timedelta(minutes=5)
        self._purchases = []
        self._sales = []
        self._transactions = []
        self._cromoon = cromoon
        if initialize_data:
            self.get_all_transactions()
            self.get_current_balance()

    def get_all_transactions(self):
        self._transactions = []
        self._purchases = []
        self._sales = []
        self._purchased_balance = 0
        self._last_block = 0
        self.get_transactions_since_block(0, force=True)

    def get_recent_transactions(self):
        self.get_transactions_since_block(self._last_block)

    def get_transactions_since_block(self, block: int, force: bool = False):
        now = datetime.now()
        if force or now > self._last_transaction_check + self._check_interval:
            raw_result = requests.get(
                'https://api.cronoscan.com/api?module=account&action=tokentx&address={}&startblock={}&sort=asc&apikey={}'.format(
                    self._wallet_address, self._last_block, 'M6WJHQ5E24Y5DX51PGYKUJ539MQ5Q9QNX4')).json()
            self.__process_transactions(raw_result)
            self._last_transaction_check = now

    def __process_transactions(self, raw: {}):
        for res in raw.get('result', []):
            block = int(res.get('blockNumber'))
            if block > self._last_block:
                self._last_block = block + 1
            if res.get('contractAddress').lower() == cromoon_contract_address:
                if res.get('tokenSymbol') != "MOON":
                    print('WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Not MOON')
                self._transactions.append(res)
                if res.get('to').lower() == self._wallet_address:
                    self.__add_purchase(res)
                if res.get('from').lower() == self._wallet_address:
                    self.__add_sale(res)

    def __add_purchase(self, record: dict):
        # print("BUY: {}".format(record))
        self._purchases.append(record)
        value = record.get('value')
        decimal = int(record.get('tokenDecimal'))
        tokens = float(value[:-decimal] + '.' + value[len(value) - decimal:])
        # print("Bought: {}".format(tokens))
        self._purchased_balance += tokens

    def __add_sale(self, record: dict):
        # print("SALE: {}".format(record))
        self._sales.append(record)
        value = record.get('value')
        decimal = int(record.get('tokenDecimal'))
        tokens = float(value[:-decimal] + '.' + value[len(value) - decimal:])
        actual_tokens = tokens / 0.9
        self._purchased_balance -= actual_tokens
        # print("Sold: {}".format(actual_tokens))
        if self._purchased_balance < 0:
            print('Setting to 0')
            self._purchased_balance = 0

    def get_current_balance(self):
        now = datetime.now()
        if now > self._last_balance_check + self._check_interval:
            result = requests.get(
                'https://api.cronoscan.com/api?module=account&action=tokenbalance&contractaddress=0x7d30c36f845d1dee79f852abf3a8a402fadf3b53&address={}&tag=latest&apikey={}'.format(
                    self._wallet_address, 'M6WJHQ5E24Y5DX51PGYKUJ539MQ5Q9QNX4')).json()
            value = result.get('result')
            decimal = 9
            tokens = float(value[:-decimal] + '.' + value[len(value) - decimal:])
            self._current_balance = tokens
            self._last_balance_check = now

    @property
    def balance(self):
        return self._current_balance

    @property
    def balance_str(self):
        return f'{self.balance:,.2f}'

    @property
    def purchased(self):
        return self._purchased_balance

    @property
    def purchased_str(self):
        return f'{self._purchased_balance:,.2f}'

    @property
    def reflections(self):
        return self._current_balance - self._purchased_balance

    @property
    def reflections_str(self):
        return f'{self.reflections:,.2f}'

    @property
    def reflections_percent(self):
        return self.reflections / self._current_balance

    @property
    def reflections_percent_str(self):
        if self.reflections:
            return f'{self.reflections_percent:.2%}'
        else:
            return f'{0:.2%}'

    @property
    def reflection_stat_str(self):
        self.get_all_transactions()
        self.get_current_balance()
        reply_lines = [
            "<b>Purchased MOON</b>:     {}".format(self.purchased_str),
            "<b>Current Balance</b>:    {}".format(self.balance_str),
            "<b>Total Reflections</b>:  {} ({} of total)".format(self.reflections_str,
                                                                 self.reflections_percent_str),
        ]
        if self._cromoon is not None:
            try:
                price = float(self._cromoon.price)
            except Exception as e:
                price = None
            if price is not None:
                value = self.balance * price
                ref_val = f'${value:,.2f}'
            else:
                ref_val = 'Unavailable'
            reply_lines.append("<b>MOON Value USD</b>: {}".format(ref_val))
        reply_lines += [
            "<a href='https://cronoscan.com/token/{}?a={}'>Transaction Details</a>".format(cromoon_contract_address,
                                                                                           self._wallet_address),
            "<i>BETA: Values may be incorrect.  Please consult Cronoscan if you are unsure</i>"
        ]
        return reply_lines
