from os import path

import hashlib
import requests, json
import pandas as pd

KEYS_LOCATION = path.dirname(path.dirname(path.abspath(__file__))) + "\\NoGithub\\"
API_KEY_FILENAME = 'api_key'
API_SECRET_FILENAME = 'api_secret'
ACCESS_TOKEN_FILENAME = 'access_token'
REFRESH_TOKEN_FILENAME = 'refresh_token'
REQUEST_TOKEN = 'tYm7aA4fFIbRNeCqPWTLDWwnO5Z2DQQj'
ACCESS_TOKEN_URL = 'https://api.kite.trade/session/token'
INSTRUMENTS_DATA_URL = 'https://api.kite.trade/instruments'

GAP_LOWER_LIMIT = 2
GAP_UPPER_LIMIT = 5

DATA_LOCATION = path.dirname(path.dirname(path.abspath(__file__))) + "\\Data\\"
ZERODHA_INSTRUMENT_LIST_FILENAME = 'instruments'
NSE500_LIST_FILENAME = 'ind_nifty500list.csv'
NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN = 'nse500withzerodhatoken'

# Request tokken url: https://kite.trade/connect/login?v=3&api_key=t7cybf56wqczkl68
#curl https://api.kite.trade/session/token -H "X-Kite-Version: 3" -d "api_key=t7cybf56wqczkl68" -d "request_token=7yg1Fh0Eh5vX2I06AnNZxfwUBa7VqJzQ" -d "checksum=ca2ab4fa3819d46578dde379799f64d7c15169e83ed5d6d8d9b5c7988d7d8436"


def GETSHA256(data):
    return hashlib.sha256(data).hexdigest()

def GetNSE500List():
    try:
        nse500ListDF = pd.read_csv(DATA_LOCATION + NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN)
        nse500InstrumentTokenList = nse500ListDF["InstrumentToken"]

        print type(nse500InstrumentTokenList)
        print nse500InstrumentTokenList
        return nse500InstrumentTokenList
    except Exception as e:
        print e
        return []