from Utility import *

def Analyse(ticks):
    for tick in ticks:
        ohlc = tick['ohlc']
        prevClose = ohlc['close']
        open = ohlc['open']

        volume = tick['volume']
        gapOpenPer = (open - prevClose)/prevClose * 100

        if abs(gapOpenPer) > GAP_LOWER_LIMIT and abs(gapOpenPer) < GAP_UPPER_LIMIT:
            print "$$$ Gap alert $$$ " + str(tick['instrument_token']) + " opened at " + str(gapOpenPer) + ", closed change: " + str(tick['change'])


        #print "Tick for: " + str(tick['instrument_token']) + " LTP: " + str(tick['last_price'])
