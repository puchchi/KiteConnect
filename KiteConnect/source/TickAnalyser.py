from Utility import *
from os import path
from datetime import datetime
from KiteOrderManager import KiteOrderManager
import thread

def Analyse(ws, ticks):
    now = int(datetime.now().strftime("%H%M%S"))

    if now >= TIMESTAMP1 and now < TIMESTAMP2:
        CollectStocks(ws, ticks)
    elif now >= TIMESTAMP2 and now < TIMESTAMP3:
        instance = KiteOrderManager.GetInstance()
    elif now >= TIMESTAMP3 and now < TIMESTAMP10:
        Trade(ws, ticks)
    else:
       # ws.close()
       pass

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
    for tick in ticks:
        lastPrice = tick['last_price']
        openPrice = tick['ohlc']['open']
        prevClose = tick['ohlc']['close']
        instrumentToken = tick['instrument_token']

        #Gap down opening
        if prevClose > openPrice and  lastPrice > openPrice:
            thread.start_new_thread(BuyStock, (ws, instrumentToken, lastPrice))
        #Gap up opening
        elif prevClose < openPrice and lastPrice < openPrice:
            thread.start_new_thread(SellStock, (ws, instrumentToken, lastPrice))


def BuyStock(ws, instrumentToken, lastPrice):
        
    try:
        with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'r') as f:
            df = pd.read_csv(f)
            targetPoint = (lastPrice * PROFIT_PERCENTAGE / 100).__format__('.1f')
            stopLossPoint = (lastPrice * STOPLOSS_PERCENTAGE / 100).__format__('.1f')

            # making market order
            tradePrice = (lastPrice + (lastPrice * 0.01)).__format__('.1f')
            symbol = df['symbol'][0]
            quantity = df['quantity'][0]

            instance = KiteOrderManager.GetInstance()
            instance.BuyBracketOrder(symbol, tradePrice, targetPoint, stopLossPoint, quantity)

            #Add order api here
            print "Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
            logging.critical("Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))

            ws.unsubscribe(instrumentToken)
            print "Unsubscribing from " + str(instrumentToken) + ", after placing order."
    except Exception as e:
        print "Eception in TickAnalyser::Trade()"
        print e
        logging.error("Eception in TickAnalyser::Trade()", exc_info=True)

def SellStock(ws, instrumentToken, lastPrice):
        
    try:
        with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'r') as f:
            df = pd.read_csv(f)
            targetPoint = (lastPrice * PROFIT_PERCENTAGE / 100).__format__('.1f')
            stopLossPoint = (lastPrice * STOPLOSS_PERCENTAGE / 100).__format__('.1f')

            # making market order
            tradePrice = (lastPrice - (lastPrice * 0.01)).__format__('.1f')
            symbol = df['symbol'][0]
            quantity = df['quantity'][0]

            instance = KiteOrderManager.GetInstance()
            instance.SellBracketOrder(symbol, tradePrice, targetPoint, stopLossPoint, quantity)

            #Add order api here
            print "Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
            logging.critical("Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))

            ws.unsubscribe(instrumentToken)
            print "Unsubscribing from " + str(instrumentToken) + ", after placing order."
    except Exception as e:
        print "Eception in TickAnalyser::Trade()"
        print e
        logging.error("Eception in TickAnalyser::Trade()", exc_info=True)