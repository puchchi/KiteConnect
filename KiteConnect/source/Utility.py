from os import path

import hashlib, os
import requests, json
import pandas as pd
import logging

DATABASE_HOST = "localhost"
DATABASE_NAME = "AutoTradingDB"
DATABASE_USERNAME = "StockUser"
DATABASE_PASSWORD = "StockPass"

LEVELS_TABLENAME = "Levels"
TODO_TABLENAME = "Todo"

LEVEL_CROSS_TYPE_ENUM = ['up', 'down']
TASK_TYPE_ENUM = ['buy', 'sell', 'tp_update', 'sl_update']

HOME_DIR = path.dirname(path.dirname(path.abspath(__file__)))

LOGGING_DIR = path.join(HOME_DIR, "Logs")
FULL_LOGGING_PATH = path.join(LOGGING_DIR, 'full_logs.txt')
logging.basicConfig(filename=FULL_LOGGING_PATH, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

KEYS_LOCATION = path.join(HOME_DIR, "NoGithub")
API_KEY_PATH = path.join(KEYS_LOCATION, "api_key")
API_SECRET_PATH = path.join(KEYS_LOCATION, "api_secret")
ACCESS_TOKEN_PATH = path.join(KEYS_LOCATION, "access_token")
USERID_PATH = path.join(KEYS_LOCATION, "user_id")
PASSWORD_PATH = path.join(KEYS_LOCATION, "password")
PIN_PATH = path.join(KEYS_LOCATION, "pin")

ACCESS_TOKEN_URL = 'https://api.kite.trade/session/token'
INSTRUMENTS_DATA_URL = 'https://api.kite.trade/instruments'

GAP_LOWER_LIMIT = 2
GAP_UPPER_LIMIT = 4

DATA_LOCATION = path.join(HOME_DIR, "Data")
ZERODHA_INSTRUMENT_LIST_PATH = path.join(DATA_LOCATION, "instruments")
NSE500_LIST_PATH = path.join(DATA_LOCATION, "ind_nifty500list") 
NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN = path.join(DATA_LOCATION, "nse500withzerodhatoken")

SHORTLISTED_STOCK_LOCATION = path.join(HOME_DIR, "ShortlistedStocks")
TRADABLE_STOCK_LOCATION = path.join(HOME_DIR, "TradableStocks")

USE_CONSTANT_QUANTITY = False
CONSTANT_QUANTITY = 1
AVAILABLE_MARGIN = 30000 * 4.2        # Assuming 4.2x leavarege on Bracket order

ORDER_TYPE = 'BO'          #'BO'

TICKERSTART = '091500'     #91505     # 09:15:05 AM (added 5 second as time padding)
TRADABLESTOCKSTART = '220400'     #91800     # 09:18:00 AMl
TRADINGSTART = '092000'     #92000     # 09:20:05 AM
TRADINGCLOSE = '230000'   #152000    # 03:20:00 PM

PROFIT_PERCENTAGE = 1
STOPLOSS_PERCENTAGE = 1

INDEX_FUTURE_DATA = {14628098:{'underlyingsymbol':'NIFTY', 'tradingsymbol':'NIFTY19JUNFUT', 'expiry':'27JUN2019', 'tradable':True, 'quantity':75},}
                     #14627842:{'underlyingsymbol':'BANKNIFTY', 'tradingsymbol':'BANKNIFTY19JUNFUT','expiry':'27JUN2019', 'tradable':False}}

INDEX_FUTURES_FUTURE_DATA = {11870210:{'underlyingsymbol':'NIFTY', 'tradingsymbol':'NIFTY19JULFUT', 'expiry':'25JUL2019', 'tradable':True},
                     11869954:{'underlyingsymbol':'BANKNIFTY', 'tradingsymbol':'BANKNIFTY19JULFUT','expiry':'25JUL2019', 'tradable':False}}

FIB_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 0.888, 1.236, 1.618]
PRICE_PADDING = 0.00025

# Request tokken url: https://kite.trade/connect/login?v=3&api_key=t7cybf56wqczkl68
#curl https://api.kite.trade/session/token -H "X-Kite-Version: 3" -d "api_key=t7cybf56wqczkl68" -d "request_token=7yg1Fh0Eh5vX2I06AnNZxfwUBa7VqJzQ" -d "checksum=ca2ab4fa3819d46578dde379799f64d7c15169e83ed5d6d8d9b5c7988d7d8436"

# Equity margin (MIS order) margin sheet https://zerodha.com/margin-calculator/Equity/

def GETSHA256(data):
    return hashlib.sha256(data).hexdigest()

def GetNSE500List():
    try:
        # First check if SHORTLISTED_STOCK_LOCATION is empty r not
        try:
            shortListedStock = os.listdir(SHORTLISTED_STOCK_LOCATION)
            if shortListedStock.__len__() > 0:
                # Now check how many of these stocks have been traded
                tradedStock = os.listdir(TRADABLE_STOCK_LOCATION)

                for stock in tradedStock:
                    if stock.find("_done") != -1:
                        shortListedStock.remove(stock.split("_done")[0])

                return shortListedStock
        except Exception as e:
            print e
            return []

        nse500ListDF = pd.read_csv(NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN)
        nse500InstrumentTokenList = nse500ListDF["InstrumentToken"]

        return list(nse500InstrumentTokenList)
    except Exception as e:
        print e
        logging.critical("Unable to find nse500 list", exc_info=True)
        return []
  
def IsWeekday(datetime):
    if datetime.day!=6 and datetime != 7:
        return True
    return False

def GetNSE500ListWithSymbol():
    nse500ListDF = pd.DataFrame()
    try:
        nse500ListDF = pd.read_csv(NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN)
    except Exception as e:
        print e
        logging.critical("Unable to find nse500 list", exc_info=True)
    return nse500ListDF