from kiteconnect import KiteTicker
from kiteconnect import KiteConnect

import hashlib, time, requests, thread, logging
import TickAnalyser, Utility
from InitToken import TokenManager


#kite = KiteConnect(api_key=API_KEY)
#data = kite.generate_session(REQUEST_TOKEN, api_secret=API_SECRET)
#kite.set_access_token(data["access_token"])


def on_ticks(ws, ticks):
    # Callback to receive ticks.

    try:
        thread.start_new_thread(TickAnalyser.Analyse, (ws, ticks))
    except Exception as e:
        print "e"
        raise "Exception in on_ticks in Ticker.py"
        logging.error("Exception occured!", exc_info=True)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    
    print "Connection successful....."
    logging.info("Connection successful.....")
    subscriberList = Utility.GetNSE500List()
    ws.subscribe(subscriberList)

    # Set RELIANCE to tick in `full` mode.
    #ws.set_mode(ws.MODE_QUOTE, [738561])
    #ws.set_mode(ws.MODE_FULL, [5633])
    #ws.set_mode(ws.MODE_QUOTE, subscriberList)
    ws.set_mode(ws.MODE_QUOTE, subscriberList)

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

def StartTicker():

    tokenManager = TokenManager.GetInstance()
    kws = KiteTicker(tokenManager.GetApiKey(), tokenManager.GetAccessToken())
    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_message = on_message
    kws.connect()




