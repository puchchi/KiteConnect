from Utility import *
from os import path
from datetime import datetime

def Analyse(ws, ticks):
    now = int(datetime.now().strftime("%H%M%S"))
    if now >= TIMESTAMP1 and now < TIMESTAMP2:
        CollectStocks(ws, ticks)
    elif now >= TIMESTAMP2 and now < TIMESTAMP3:
        pass
    elif now >= TIMESTAMP3 and now < TIMESTAMP10:
        Trade(ws, ticks)
    else:
       # ws.close()
       CollectStocks(ws, ticks)

def CollectStocks(ws, ticks):
    for tick in ticks:
        ohlc = tick['ohlc']
        prevClose = ohlc['close']
        openPrice = ohlc['open']
        instrumentToken = tick['instrument_token']
        #high = ohlc['high']
        #low = ohlc['low']

        #volume = tick['volume']
        gapOpenPer = (openPrice - prevClose)/prevClose * 100

        if abs(gapOpenPer) > GAP_LOWER_LIMIT and abs(gapOpenPer) < GAP_UPPER_LIMIT:
            signal = ""
            if gapOpenPer > 0:      #Gap up 
                signal = "sell"
            elif gapOpenPer < 0:
                signal = "buy"

            try:
                with open(path.join(SHORTLISTED_STOCK_LOCATION, str(instrumentToken)), 'w+') as f:
                    f.write("open,"+"signal\n" + str(openPrice) + "," + signal)
                print "Shortlisted stocks | " + str(instrumentToken) + ", opened at " + str(gapOpenPer)
            except Exception as e:
                logging.error("Exception occured!Tick analyser", exc_info=True)
                print "Exception occured in TickAnalyser.py"
                print e
                continue

            #openToHighPer = (high - openPrice)/openPrice * 100
            #openToLowPer = (low - openPrice) / open *100
            #print "$$$ Gap alert $$$ " + str(tick['instrument_token']) + " opened at " + str(gapOpenPer) + ", closed change: " + str(tick['change']) + ", open to high%: " + str(openToHighPer) + ", open to low %: " + str(openToLowPer)
            #print "\t\tOHLC:" + str(ohlc) + ", Last price:" + str(tick['last_price'])
        
        ws.unsubscribe([instrumentToken,])
        print "Unsubscribing from " + str(instrumentToken) + ", opened at " + str(gapOpenPer)
        #logging.info("Unsubscribing from " + str(instrumentToken) + ", opened at " + str(gapOpenPer))

def Trade(ws, ticks):
    pass