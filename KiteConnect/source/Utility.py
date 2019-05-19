from os import path

import hashlib
import requests, json
import pandas as pd
import logging

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
GAP_UPPER_LIMIT = 50

DATA_LOCATION = path.join(HOME_DIR, "Data")
ZERODHA_INSTRUMENT_LIST_PATH = path.join(DATA_LOCATION, "instruments")
NSE500_LIST_PATH = path.join(DATA_LOCATION, "ind_nifty500list") 
NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN = path.join(DATA_LOCATION, "nse500withzerodhatoken")

SHORTLISTED_STOCK_LOCATION = path.join(HOME_DIR, "ShortlistedStocks")
TRADABLE_STOCK_LOCATION = path.join(HOME_DIR, "TradableStocks")

AVAILABLE_MARGIN = 20000 * 4        # Assuming 4x leavarege on Bracket order

TIMESTAMP1 = 191100#91505     # 09:15:05 AM (added 5 second as time padding)
TIMESTAMP2 = 191300#91800     # 09:18:00 AM
TIMESTAMP3 = 191400#92000     # 09:20:05 AM
TIMESTAMP10 = 193000    # 03:20:00 PM

# Request tokken url: https://kite.trade/connect/login?v=3&api_key=t7cybf56wqczkl68
#curl https://api.kite.trade/session/token -H "X-Kite-Version: 3" -d "api_key=t7cybf56wqczkl68" -d "request_token=7yg1Fh0Eh5vX2I06AnNZxfwUBa7VqJzQ" -d "checksum=ca2ab4fa3819d46578dde379799f64d7c15169e83ed5d6d8d9b5c7988d7d8436"

# Equity margin (MIS order) margin sheet https://zerodha.com/margin-calculator/Equity/

def GETSHA256(data):
    return hashlib.sha256(data).hexdigest()

def GetNSE500List():
    try:
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
    try:
        nse500ListDF = pd.read_csv(NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN)
        return nse500ListDF
    except Exception as e:
        print e
        logging.critical("Unable to find nse500 list", exc_info=True)
        return []