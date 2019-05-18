from Utility import *

def Analyse(ticks):
    for tick in ticks:
        ohlc = tick['ohlc']
        prevClose = ohlc['close']
        open = ohlc['open']
        high = ohlc['high']
        low = ohlc['low']

        volume = tick['volume']
        gapOpenPer = (open - prevClose)/prevClose * 100

        if abs(gapOpenPer) > GAP_LOWER_LIMIT and abs(gapOpenPer) < GAP_UPPER_LIMIT:
            openToHighPer = (high - open)/open * 100
            openToLowPer = (low - open) / open *100
            print "$$$ Gap alert $$$ " + str(tick['instrument_token']) + " opened at " + str(gapOpenPer) + ", closed change: " + str(tick['change']) + ", open to high%: " + str(openToHighPer) + ", open to low %: " + str(openToLowPer)
            print "\t\tOHLC:" + str(ohlc) + ", Last price:" + str(tick['last_price'])

        #print "Tick for: " + str(tick['instrument_token']) + " LTP: " + str(tick['last_price'])
