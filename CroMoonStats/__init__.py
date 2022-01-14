from datetime import datetime, timedelta
from random import randint

import requests


class CroMoonStats:
    def __init__(self):
        self.total_supply = 1000000000000000
        # self.last_dextools_update_time = datetime.fromtimestamp(0)
        # self.dextools_result = None
        # self.dextools_interval = timedelta(seconds=15)
        self.last_cronoscan_update_time = datetime.fromtimestamp(0)
        self.cronoscan_interval = timedelta(minutes=5)
        self.cronoscan_result = None
        self.last_crodex_update = datetime.fromtimestamp(0)
        self.crodex_result = None
        self.crodex_interval = timedelta(minutes=5)
        self.cromoon_price = 0
        self.dexscreener_result = None
        self.dexscreener_update_time = datetime.fromtimestamp(0)
        self.dexscreener_interval = timedelta(minutes=5)

    def get_dead_wallet_string(self):
        return f'{self.get_dead_wallet():,}'

    def get_dead_wallet(self):
        self.get_cronoscan()
        count = self.cronoscan_result['result']
        r = int(count) / 1000000000
        return r

    def get_current_price_string(self):
        self.get_dexscreener()
        return self.cromoon_price

    def get_current_price(self):
        self.get_dexscreener()
        return float(self.cromoon_price)

    def get_market_cap(self):
        return self.get_current_price() * (self.total_supply - self.get_dead_wallet())

    def get_percent_burned(self):
        return self.get_dead_wallet()/self.total_supply

    def get_cronoscan(self):
        now = datetime.now()
        if now > self.last_cronoscan_update_time + self.cronoscan_interval:
            self.cronoscan_result = requests.get(
                'https://api.cronoscan.com/api?module=account&action=tokenbalance&contractaddress=0x7d30c36f845d1dee79f852abf3a8a402fadf3b53&address=0x000000000000000000000000000000000000dEaD&tag=latest&apikey={}'.format(randint(10000,999999999))).json()
            self.last_cronoscan_update_timescan_update_time = now

    # def get_dextools(self):
    #     now = datetime.now()
    #     if now > self.last_dextools_update_time + self.dextools_interval:
    #         self.dextools_result = requests.get(
    #             'https://www.dextools.io/chain-cronos/api/pair/summary?address=0xb2ba36ee6ba6113a914f3e8812a0df094dec5994&foo=1234').json()
    #         self.last_dextools_update_time = now

    # def get_crodex(self):
    #     now = datetime.now()
    #     if now > self.last_crodex_update + self.crodex_interval:
    #         self.crodex_result = requests.get(
    #             'https://chartapi.crodex.app/token/0x7D30c36f845d1dEe79f852abF3A8A402fAdF3b53/info?foo={}'.format(randint(10000,999999999))).json()
    #         self.cromoon_price = self.crodex_result.get('priceInUSDT', "ERROR")
    #         self.last_crodex_update = now

    def get_dexscreener(self):
        now = datetime.now()
        if now > self.dexscreener_update_time + self.dexscreener_interval:
            self.dexscreener_result = requests.get(
                'https://io9.dexscreener.io/u/trading-history/recent/cronos/0xb2bA36ee6ba6113a914f3E8812A0dF094DEC5994').json()
            self.cromoon_price = self.dexscreener_result.get('tradingHistory', [])[0].get('priceUsd', '0')
            self.dexscreener_update_time = now
