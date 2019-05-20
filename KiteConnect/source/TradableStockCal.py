from multiprocessing import Process, Queue
import os
import pandas as pd
from Utility import *
import datetime as dt

def Calculate():
    print "Tradable stock calculation starts...."
    logging.info("Tradable stock calculation starts....")

    tempFiles = os.listdir(TRADABLE_STOCK_LOCATION)
    if tempFiles.__len__() >0:
        print "TradableStocks folder already contains some stocks, returning ....."
        logging.info("TradableStocks folder already contains some stocks, returning .....")

    # Get all files in Shortlisted stocks
    shortlistedStocks = os.listdir(SHORTLISTED_STOCK_LOCATION)
    stockToOpenPrice = {}
    stockToSignal = {}
    for stock in shortlistedStocks:
        try:
            with open(os.path.join(SHORTLISTED_STOCK_LOCATION, stock), 'r') as f:
                df = pd.read_csv(f)
                stockToOpenPrice.update({stock:df["open"][0]})
                stockToSignal.update({stock:df["signal"][0]})
        except Exception as e:
            print "Exception occured in TradableStockCal::Calculate()"
            logging.error("Exception occured", exc_info=True)

    marginForEachStock = AVAILABLE_MARGIN / shortlistedStocks.__len__()
    nse500DF = GetNSE500ListWithSymbol()
    for i in range(nse500DF.index.__len__()):
        instrumentToken = nse500DF["InstrumentToken"][i]
        #print instrumentToken
        if stockToOpenPrice.has_key(str(instrumentToken)):
            openPrice = stockToOpenPrice[str(instrumentToken)]
            quantity = int(marginForEachStock / openPrice)
            if USE_CONSTANT_QUANTITY:
                quantity = CONSTANT_QUANTITY
            if quantity == 0:
                logging.info("Not enough margin avaible")
                print "Not enough margin avaible"
                continue

            symbol = nse500DF["Symbol"][i]
            try:
                with open(os.path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'w+') as f:
                    f.write("symbol," + "open," + "quantity," + "signal\n")
                    f.write(symbol + "," + str(openPrice) + "," + str(quantity) + "," + stockToSignal[str(instrumentToken)])
                logging.info("Tradable stock: " + symbol + " at open price: " + str(openPrice))
            except Exception as e:
                print "Exception occured in TradableStockCal::Calculate()"
                logging.error("Exception occured", exc_info=True)

    print "Tradable stock calculation end...."
    logging.info("Tradable stock calculation end....")

class kCommand:

    def __init__(self, *args):
        self.args = args

    def run_job(self, queue, args):
        try:
            Calculate()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    def do(self):

        queue = Queue()
        process = Process(target=self.run_job, args=(queue, self.args))
        process.start()
        result = queue.get()
        process.join()

        if result is not None:
            raise result

    def get_name(self):
        return "Tradable stock cal command"

