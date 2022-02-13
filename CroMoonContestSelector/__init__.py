from datetime import datetime, timedelta
from random import randint, uniform
from time import sleep

import json
import requests

cromoon_contract_address = "0x7D30c36f845d1dEe79f852abF3A8A402fAdF3b53".lower()

SWAP_ETH_FOR_EXACT = "0xfb3bdb41"  # Only winner
DEPOSIT = "0x8dbdbe6d"
ADD_LIQUIDITY = "0xf305d719"  # Don't exclude as seller
REMOVE_LIQUIDITY = "0xded9382a"  # Don't consider winner
SWAP_EXACT_TOKENS_FOR_ETH = "0x791ac947"
TRANSFER = "0x38ed1739"  # Don't consider winner


def get_block_number_from_timestamp(timestamp: int) -> int:
    raw_result = requests.get(
        "https://api.cronoscan.com/api?module=block&action=getblocknobytime&timestamp={}&closest=after&apikey={}".format(
            timestamp, randint(10000, 999999999))).json()
    block = raw_result.get('result', 0)
    return block


class CroMoonContestSelector:
    def __init__(self, start_time: int, end_time: int, sale_embargo: int, target=None, min_num=None,
                 max_num=None):
        self._last_block = 0
        self._purchased_balance = 0
        self._current_balance = 0
        self._last_transaction_check = datetime.fromtimestamp(0)
        self._last_balance_check = datetime.fromtimestamp(0)
        self._check_interval = timedelta(minutes=5)
        self._purchases = []
        self._sales = []
        self._transactions = []
        self._start_time = datetime.fromtimestamp(start_time)
        self._start_block = get_block_number_from_timestamp(int(start_time))
        self._end_time = datetime.fromtimestamp(end_time)
        self._end_block = get_block_number_from_timestamp(int(end_time))
        self._sale_embargo_time = datetime.fromtimestamp(sale_embargo)
        self._sale_embargo_block = get_block_number_from_timestamp(int(sale_embargo))
        if target is not None:
            self._target_amount = target
        else:
            self._target_amount = round(uniform(min_num, max_num), 2)
        self._closest_guess = None
        self._sellers = []
        self._winners = []
        self._qualified_transaction = 0
        self._dex_pairs = ['0xb2ba36ee6ba6113a914f3e8812a0df094dec5994', '0xaefd1c8b1acc0eccba26d5c6c712ddf4741e24c7']
        # Uncomment this to test with only Crodex pair
        # self._dex_pairs = ['0xb2ba36ee6ba6113a914f3e8812a0df094dec5994']
        self.__get_qualified_transactions()
        self.__find_winners()

    def __get_qualified_transactions(self):
        for dex in self._dex_pairs:
            raw_result = requests.get(
                'https://api.cronoscan.com/api?module=account&action=tokentx&address={}&startblock={}&endblock={}&sort=asc&apikey={}'.format(
                    dex, self._start_block, self._sale_embargo_block, randint(10000, 999999999))).json()
            self.__add_transactions(raw_result)

    def __add_transactions(self, raw: {}):
        for res in raw.get('result', []):
            if res.get('contractAddress').lower() == cromoon_contract_address:
                if res.get('tokenSymbol') != "MOON":
                    print('WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Not MOON')
                if res.get('to').lower() in self._dex_pairs:
                    hash = res.get('hash')
                    # if self.__is_sell(hash):
                    #     self._sellers.append(res.get('from'))
                    self._sellers.append(res.get('from'))
                else:
                    self._transactions.append(res)

    def __is_sell(self, hash):
        try:
            got_result = False
            result = []
            while not got_result:
                raw_result = requests.get(
                    "https://api.cronoscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={}&apikey={}".format(
                        hash, randint(10000, 99999999))).json()
                result = raw_result.get('result', 'NONE')
                if type(result) == str:
                    print('sleeping')
                    sleep(.1)
                else:
                    got_result = True
            input_data = result.get('input')
            method = input_data[0:10]
            if method == ADD_LIQUIDITY:
                return False
            else:
                return True
        except Exception as e:
            print(e)

    def __is_buy(self, hash):
        try:
            got_result = False
            result = []
            while not got_result:
                raw_result = requests.get(
                    "https://api.cronoscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={}&apikey={}".format(
                        hash, randint(10000, 99999999))).json()
                result = raw_result.get('result', 'NONE')
                if type(result) == str:
                    print('sleeping')
                    sleep(.1)
                else:
                    got_result = True
            input_data = result.get('input')
            method = input_data[0:10]
            if method == SWAP_ETH_FOR_EXACT:
                return True
            else:
                return False
        except Exception as e:
            print(e)

    def __find_winners(self) -> list:
        for transaction in self._transactions:
            wallet = transaction.get('to')
            # print(transaction)
            if wallet in self._sellers or int(transaction.get('timeStamp')) > self._end_time.timestamp():
                continue
            value = transaction.get('value')
            decimal = int(transaction.get('tokenDecimal'))
            tokens = float(value[:-decimal] + '.' + value[len(value) - decimal:])
            missed_by = abs(tokens - self._target_amount)
            # print("{} - {}".format(f'{tokens:,.2f}', f'{missed_by:,.2f}'))
            if self._closest_guess is None or missed_by < self._closest_guess:
                if self.__is_buy(transaction.get('hash')):
                    self._closest_guess = missed_by
                    self._winners = [
                        {'wallet': wallet, 'txn': transaction.get('hash'), 'tokens': tokens, 'record': transaction}]
                    continue
            if missed_by == self._closest_guess:
                if self.__is_buy(transaction.get('hash')):
                    self._winners.append(
                        {'wallet': wallet, 'txn': transaction.get('hash'), 'tokens': tokens, 'record': transaction})
        return self._winners

    def _print_winners(self):
        for winner in self._winners:
            print(json.dumps(winner, indent=4))

    @property
    def winning_wallets(self):
        wallets = []
        for winner in self._winners:
            wallets.append(winner.get('wallet'))
        return wallets

    @property
    def is_tie(self):
        return len(self._winners) > 1

    @property
    def winners(self):
        return self._winners

    @property
    def target(self):
        return self._target_amount

    @property
    def off_by(self):
        return self._closest_guess
