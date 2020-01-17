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
GAP_OPEN_TABLENAME = "GapOpen"             # Symbol, open price, tasktype (b/s), Status(open/done)

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

GAP_LOWER_LIMIT = 1
GAP_UPPER_LIMIT = 1

DATA_LOCATION = path.join(HOME_DIR, "Data/")
ZERODHA_INSTRUMENT_LIST_FILENAME = "instruments"
ZERODHA_INSTRUMENT_LIST_PATH = path.join(DATA_LOCATION, ZERODHA_INSTRUMENT_LIST_FILENAME)
NSE500_LIST_PATH = path.join(DATA_LOCATION, "ind_nifty500list") 
NSE500_LIST_FILENAME = "nse500withzerodhatoken"
NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN = path.join(DATA_LOCATION, NSE500_LIST_FILENAME)

SHORTLISTED_STOCK_LOCATION = path.join(HOME_DIR, "ShortlistedStocks")
TRADABLE_STOCK_LOCATION = path.join(HOME_DIR, "TradableStocks")
SHORTLISTED_GAP_OPEN_STOCK_LOCATION = path.join(HOME_DIR, "GapOpenShortlistedStocks")

USE_CONSTANT_QUANTITY = False
CONSTANT_QUANTITY = 1
AVAILABLE_MARGIN = 20000 * 12        # Assuming 10x leavarege on Bracket order

ORDER_TYPE = 'BO'          #'BO'

TICKERSTART = '091000'     #091200     # 09:15:05 AM (added 5 second as time padding)
TRADABLESTOCKSTART = '220400'     #91800     # 09:18:00 AMl
GAPUPTRADINGPREP = '091430'    #091430             # 09:14:30 AM  # 30 second early to start kite manager
TRADINGSTART = '091500'     #091500     # 09:20:05 AM       
TRADINGCLOSE = '153000'   #152000    # 03:20:00 PM

PROFIT_PERCENTAGE = 0.5
STOPLOSS_PERCENTAGE = 0.5
PRICE_PADDING_PERCENTAGE = 0.5
INVALID_PRICE = -1

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

NIFTY50_LIST = ['ADANIPORTS','POWERGRID','NTPC', 'VEDL', 'INFY', 'INFRATEL', 'M&M', 'HDFC', 'LT', 'HINDUNILVR', 'UPL', 'WIPRO', 'HDFCBANK',
               'ULTRACEMCO', 'HCLTECH', 'TCS', 'SBIN', 'DRREDDY', 'BRITANNIA', 'COALINDIA', 'SUNPHARMA', 'IOC', 'ITC', 'ASIANPAINT', 
               'TECHM', 'BPCL', 'GAIL', 'BAJFINANCE', 'GRASIM', 'NESTLEIND', 'RELIANCE', 'ICICIBANK', 'BAJAJFINSV', 'CIPLA',
               'HEROMOTOCO', 'BHARTIARTL', 'TATAMOTORS', 'HINDALCO', 'JSWSTEEL', 'KOTAKBANK', 'AXISBANK', 'MARUTI', 'TATASTEEL',
               'BAJAJ-AUTO', 'ZEEL', 'ONGC', 'INDUSINDBK', 'EICHERMOT', 'TITAN']

NIFTY50_SYMBOL_WITH_INSTRUMENT_TOKEN_LIST = {'ADANIPORTS':3861249,'POWERGRID':3834113,'NTPC':2977281, 'VEDL':784129, 'INFY':408065,
              'INFRATEL':7458561, 'M&M':519937, 'HDFC':340481, 'LT':2939649, 'HINDUNILVR':356865, 'UPL':2889473, 'WIPRO':969473,
              'HDFCBANK':341249, 'ULTRACEMCO':2952193, 'HCLTECH':1850625, 'TCS':2953217, 'SBIN':779521, 'DRREDDY':225537, 
              'BRITANNIA':140033, 'COALINDIA':5215745, 'SUNPHARMA':857857, 'IOC':415745, 'ITC':424961, 'ASIANPAINT':60417, 
               'TECHM':3465729, 'BPCL':134657, 'GAIL':1207553, 'BAJFINANCE':81153, 'GRASIM':315393, 'NESTLEIND':4598529, 
               'RELIANCE':738561, 'ICICIBANK':1270529, 'BAJAJFINSV':4268801, 'CIPLA':177665, 'HEROMOTOCO':345089,
              'BHARTIARTL':2714625, 'TATAMOTORS':884737, 'HINDALCO':348929, 'JSWSTEEL':3001089, 'KOTAKBANK':492033, 'AXISBANK':1510401,
             'MARUTI':2815745, 'TATASTEEL':895745, 'BAJAJ-AUTO':4267265, 'ZEEL':975873, 'ONGC':633601, 'INDUSINDBK':1346049,
            'EICHERMOT':232961, 'TITAN':897537}

NIFTY50_INSTRUMENT_TOKEN_WITH_SYMBOL_LIST = {3861249:'ADANIPORTS',3834113:'POWERGRID',2977281:'NTPC', 784129:'VEDL', 408065:'INFY',
              7458561:'INFRATEL', 519937:'M&M', 340481:'HDFC', 2939649:'LT', 356865:'HINDUNILVR', 2889473:'UPL', 969473:'WIPRO',
              341249:'HDFCBANK', 2952193:'ULTRACEMCO', 1850625:'HCLTECH', 2953217:'TCS', 779521:'SBIN', 225537:'DRREDDY', 
              140033:'BRITANNIA', 5215745:'COALINDIA', 857857:'SUNPHARMA', 415745:'IOC', 424961:'ITC', 60417:'ASIANPAINT', 
               3465729:'TECHM', 134657:'BPCL', 1207553:'GAIL', 81153:'BAJFINANCE', 315393:'GRASIM', 4598529:'NESTLEIND', 
               738561:'RELIANCE', 1270529:'ICICIBANK', 4268801:'BAJAJFINSV', 177665:'CIPLA', 345089:'HEROMOTOCO',
              2714625:'BHARTIARTL', 884737:'TATAMOTORS', 348929:'HINDALCO', 3001089:'JSWSTEEL', 492033:'KOTAKBANK', 1510401:'AXISBANK',
             2815745:'MARUTI', 895745:'TATASTEEL', 4267265:'BAJAJ-AUTO', 975873:'ZEEL', 633601:'ONGC', 1346049:'INDUSINDBK',
            232961:'EICHERMOT', 897537:'TITAN'}