from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import os

import hashlib, time, requests, thread, logging
from Utility import *
from InitToken import TokenManager
from multiprocessing import Process, Queue
#from TickAnalyser import Analyse
from IndexTickAnalyser import Analyse
import CleanNCreateDBTables
from datetime import datetime


#kite = KiteConnect(api_key=API_KEY)
#data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
#kite.set_access_token(data["access_token"])


def on_ticks(ws, ticks):
    # Callback to receive ticks.

    try:
        thread.start_new_thread(Analyse, (ws, ticks))
    except Exception as e:
        print "e"
        raise "Exception in on_ticks in Ticker.py"
        logging.error("Exception occured!", exc_info=True)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    
    print "Connection successful....."
    logging.info("Connection successful.....")
    #subscriberList = Utility.GetNSE500List()
    #subscriberList = INDEX_FUTURE_DATA.keys()
    subscriberList = NIFTY50_INSTRUMENT_TOKEN_WITH_SYMBOL_LIST.keys()
    
    ws.subscribe(subscriberList)
    #ws.subscribe([738561])

    # Set RELIANCE to tick in `full` mode.
    #ws.set_mode(ws.MODE_FULL, [738561])
    #ws.set_mode(ws.MODE_FULL, [5633])
    #ws.set_mode(ws.MODE_QUOTE, subscriberList)
    #ws.set_mode(ws.MODE_QUOTE, subscriberList)

def on_message(ws, payload, is_binary):
    if is_binary:
        None

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`

    print "Reason for closing websocket: " + str(reason)
    logging.info("Closing websocket!")
    logging.info("Reason for closing websocket: " + str(reason))
    ws.stop()

    logging.info("Exiting ticker process")
    print "Exiting ticker process"
    #exit()

def StartTicker():
    tokenManager = TokenManager.GetInstance()
    kws = KiteTicker(tokenManager.GetApiKey(), tokenManager.GetAccessToken())
    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_message = on_message
    kws.connect()

class kCommand:

    def __init__(self, *args):
        self.args = args

    def run_job(self, queue, args):
        try:
            StartTicker()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    def run_process(self):
        queue = Queue()
        process = Process(target=self.run_job, args=(queue, self.args))
        process.start()
        #result = queue.get()
        #process.join()

        #if result is not None:
        #    raise result

        return process

    def do(self):
        process = self.run_process()
        while(1):
            now = int(datetime.now().strftime("%H%M%S"))

            if now >= int(TICKERSTART) and now < int(TRADINGCLOSE):
                try:
                    if process.is_alive() == False:
                        print "Ticker process has stopped, Running it again..."
                        logging.critical("Ticker process has stopped, Running it again...")
                        process = self.run_process()
                except Exception as e:
                    print e
                    print "Exception while restaring ticker process"
                    logging.critical("Exception while restaring ticker process", exc_info=True)
            elif process.is_alive() == True:
                try:
                    print "Force stopping ticker process at " + str(datetime.now().strftime("%H:%M:%S")) + "..."
                    logging.critical("Force stopping ticker process...")
                    process.terminate()
                    return
                except Exception as e:
                    print e
                    print "Exception while force stopping ticker process"
                    logging.critical("Exception while force stopping ticker process", exc_info=True)
                    return

            time.sleep(5)
        
    def get_name(self):
        return "Start sticker command"


if __name__=='__main__':
    dbCmd = CleanNCreateDBTables.kCommand()
    #dbCmd.do()
    StartTicker()

