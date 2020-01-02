from Utility import *
from os import path
from datetime import datetime
from KiteOrderManager import KiteOrderManager
import thread, os

# Use this tick analyser only for nifty 50, otherwise it will crash
def Analyse(ws, ticks):
    print "Tick recieved for " + str(ticks.__len__())
    
    now = int(datetime.now().strftime("%H%M%S"))

    if now >= int(TICKERSTART) and now < int(TRADABLESTOCKSTART):
        CollectStocks(ws, ticks)
    else:
        pass


def CollectStocks(ws, ticks):
    dbInstance = DatabaseManager.GetInstance()
    for tick in ticks:
        ohlc = tick['ohlc']
        prevClose = ohlc['close']
        openPrice = ohlc['open']
        instrumentToken = tick['instrument_token']
        #high = ohlc['high']
        #low = ohlc['low']

        #volume = tick['volume']
        gapOpenPer = (openPrice - prevClose)/prevClose * 100

        if abs(gapOpenPer) > GAP_LOWER_LIMIT or abs(gapOpenPer) > GAP_UPPER_LIMIT:
            signal = ""
            if gapOpenPer > 0:      #Gap up 
                signal = "s"
            elif gapOpenPer < 0:
                signal = "b"

            try:
                dbInstance.CreateNewGapOpenTask(NIFTY50_INSTRUMENT_TOKEN_WITH_SYMBOL_LIST[instrumentToken], openPrice, signal)
                #with open(path.join(SHORTLISTED_GAP_OPEN_STOCK_LOCATION, str(instrumentToken)), 'w+') as f:
                #    f.write("symbol,open,signal,\n" + NIFTY50_INSTRUMENT_TOKEN_WITH_SYMBOL_LIST[instrumentToken] + ","
                #           + str(openPrice) + "," + signal)
                print "Shortlisted stocks | " + str(instrumentToken) +"[" + NIFTY50_INSTRUMENT_TOKEN_WITH_SYMBOL_LIST[instrumentToken] + "]" + ", opened at " + str(gapOpenPer)
            except Exception as e:
                logging.error("Exception occured!GapOpenTickAnalyser analyser", exc_info=True)
                print "Exception occured in GapOpenTickAnalyser.py"
                print e
                continue
        
        else:
            ws.unsubscribe([instrumentToken,])
            print "Unsubscribing from " + str(instrumentToken) + ", opened at " + str(gapOpenPer)
            #logging.info("Unsubscribing from " + str(instrumentToken) + ", opened at " + str(gapOpenPer))