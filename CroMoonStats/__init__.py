from datetime import datetime, timedelta
from random import randint

import requests


def _avg_price_values(price_dict: dict):
    price_sum = 0
    for price in price_dict.values():
        price_sum += price
    return price_sum / len(price_dict)


def _add_volume(volume_dict: dict):
    volume_sum = 0
    for vol in volume_dict.values():
        volume_sum += float(vol)
    return volume_sum


class CroMoonStats:
    def __init__(self):
        self.total_supply = 1000000000000000
        self.last_dextools_update_time = datetime.fromtimestamp(0)
        self._dextools_result = {}
        self.dextools_interval = timedelta(seconds=15)
        self.last_cronoscan_update_time = datetime.fromtimestamp(0)
        self.cronoscan_interval = timedelta(minutes=5)
        self.cronoscan_result = None
        self.last_crodex_update = datetime.fromtimestamp(0)
        self.crodex_result = None
        self.crodex_interval = timedelta(minutes=5)
        self._all_prices = {}
        self._all_price24h = {}
        self._all_volume = {}
        self._price = 0
        self._price24h = 0
        self.dexscreener_result = None
        self.dexscreener_update_time = datetime.fromtimestamp(0)
        self.dexscreener_interval = timedelta(minutes=5)
        self.last_cronos_explorer_token_update = datetime.fromtimestamp(0)
        self.cronos_explorer_result = None
        self.cronos_explorer_interval = timedelta(minutes=5)
        self._dex_pairs = ['0xb2ba36ee6ba6113a914f3e8812a0df094dec5994', '0xaefd1c8b1acc0eccba26d5c6c712ddf4741e24c7']

    def get_dead_wallet_string(self):
        return f'{self.get_dead_wallet():,}'

    def get_dead_wallet(self):
        self.get_cronoscan()
        count = self.cronoscan_result['result']
        r = int(count) / 1000000000
        return r

    def get_current_price_string(self):
        self.get_dextools()
        return self._price

    def get_market_cap(self):
        return self._price * (self.total_supply - self.get_dead_wallet())

    def get_percent_burned(self):
        return self.get_dead_wallet() / self.total_supply

    def get_cronoscan(self):
        now = datetime.now()
        if now > self.last_cronoscan_update_time + self.cronoscan_interval:
            self.cronoscan_result = requests.get(
                'https://api.cronoscan.com/api?module=account&action=tokenbalance&contractaddress=0x7d30c36f845d1dee79f852abf3a8a402fadf3b53&address=0x000000000000000000000000000000000000dEaD&tag=latest&apikey={}'.format(
                    randint(10000, 999999999))).json()
            self.last_cronoscan_update_time = now

    def get_dextools(self):
        now = datetime.now()
        if now > self.last_dextools_update_time + self.dextools_interval:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
            for pair in self._dex_pairs:
                self._dextools_result[pair] = requests.get(
                    'https://www.dextools.io/chain-cronos/api/pair/summary?address={}&foo={}'.format(
                        pair, randint(1000, 9999999999)),
                    headers=headers).json()
                self._all_prices[pair] = self._dextools_result[pair].get('price', 0)
                self._all_price24h[pair] = self._dextools_result[pair].get('price24h', '0')
                self._all_volume[pair] = self._dextools_result[pair].get("volume24", 0)

            self._price = _avg_price_values(self._all_prices)
            self._price24h = _avg_price_values(self._all_price24h)
            self._volume24 = _add_volume(self._all_volume)
            self.last_dextools_update_time = now

    # def get_crodex(self):
    #     now = datetime.now()
    #     if now > self.last_crodex_update + self.crodex_interval:
    #         self.crodex_result = requests.get(
    #             'https://chartapi.crodex.app/token/0x7D30c36f845d1dEe79f852abF3A8A402fAdF3b53/info?foo={}'.format(randint(10000,999999999))).json()
    #         self.cromoon_price = self.crodex_result.get('priceInUSDT', "ERROR")
    #         self.last_crodex_update = now

    def get_token_holder_count(self):
        self.get_cronos_explorer_holder()
        return self.cronos_explorer_result.get('token_holder_count', '')

    def get_dexscreener(self):
        ## NOT IN USE
        now = datetime.now()
        if now > self.dexscreener_update_time + self.dexscreener_interval:
            self.dexscreener_result = requests.get(
                'https://io9.dexscreener.io/u/trading-history/recent/cronos/0xb2bA36ee6ba6113a914f3E8812A0dF094DEC5994').json()
            self._price = self.dexscreener_result.get('tradingHistory', [])[0].get('priceUsd', '0')
            self.dexscreener_update_time = now

    def get_cronos_explorer_holder(self):
        now = datetime.now()
        if now > self.last_cronos_explorer_token_update + self.cronos_explorer_interval:
            self.cronos_explorer_result = requests.get(
                'https://cronos.crypto.org/explorer/token-counters?id=0x7D30c36f845d1dEe79f852abF3A8A402fAdF3b53').json()
            self.last_cronos_explorer_token_update = now

    @property
    def price(self):
        self.get_dextools()
        return f'{self._price:.12f}'

    @property
    def price24(self):
        self.get_dextools()
        return f'{self._price24h:.12f}'

    @property
    def market_cap(self):
        return f'{self.get_market_cap():,.2f}'

    @property
    def burn_percent(self):
        return f'{self.get_percent_burned():.2%}'

    @property
    def burn_tokens(self):
        return self.get_dead_wallet_string()

    @property
    def holder_count(self):
        return self.get_token_holder_count()

    @property
    def volume_24(self):
        self.get_dextools()
        return f'{self._volume24:,.2f}'

    @property
    def change_24(self):
        self.get_dextools()
        price = self._price
        price24 = self._price24h
        if price == 0 or price24 == 0:
            return 'n/a'
        change = (price - price24) / price24
        return f'{change:+.2%}'
