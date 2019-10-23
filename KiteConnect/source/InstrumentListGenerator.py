import pandas as pd
from Utility import *

from KiteConnect.source.Utility import *

class InstrumentListGenerator():
    
    def __init__(self):
        None

    def CreateNSE500ToZerodhaInstrumentList(self):

        try:
            desiredExchange = "NSE"
            zerodhaInstDF = pd.read_csv(DATA_LOCATION + ZERODHA_INSTRUMENT_LIST_FILENAME)
            nse500ListDF = pd.read_csv(DATA_LOCATION + NSE500_LIST_FILENAME)

            finalListDF = pd.DataFrame(columns=("Symbol", "InstrumentToken", "ExchangeToken"))
            finalListCount = 0

            for i in range(nse500ListDF["Symbol"].__len__()):
                nseSymbol = nse500ListDF["Symbol"][i]
                for j in range(zerodhaInstDF["tradingsymbol"].__len__()):
                    if nseSymbol == zerodhaInstDF["tradingsymbol"][j] and zerodhaInstDF["exchange"][j] == desiredExchange:
                        finalListDF.loc[finalListCount] = [nseSymbol, zerodhaInstDF["instrument_token"][j], zerodhaInstDF["exchange_token"][j]]
                        finalListCount += 1
                        break

            finalListDF.to_csv(DATA_LOCATION + NSE500_WITH_ZERODHA_INSTRUMENT_TOKEN)

        except Exception as e:
            print e


if __name__=='__main__':
    instrumentListGen = InstrumentListGenerator()
    instrumentListGen.CreateNSE500ToZerodhaInstrumentList()