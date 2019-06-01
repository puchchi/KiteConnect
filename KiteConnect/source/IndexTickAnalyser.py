from Utility import *
from os import path
from datetime import datetime
from KiteOrderManager import KiteOrderManager
from AnnualisedVolatility import AnnualisedVolatility
import thread, os

def Analyse(ws, ticks):
    print "Tick recieved for " + str(ticks.__len__())
    
    now = int(datetime.now().strftime("%H%M%S"))

    if now >= int(TICKERSTART) and now < int(TRADINGCLOSE):
        Trade(ws, ticks)
    else:
        #Trade(ws, ticks)
       # ws.close()
        pass


def Trade(ws, ticks):
    for tick in ticks:
        instrumentToken = tick['instrument_token']
        try:
            #with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'r') as f:
            tradableStockList = os.listdir(TRADABLE_STOCK_LOCATION)
            stockFound = False
            stockMarkedDone = True
            for file in tradableStockList:
                if file.find(str(instrumentToken))!=-1:
                    stockFound = True
                    if file == str(instrumentToken):
                        stockMarkedDone = False
                    break

            if stockFound == False:
                # Now create file
                print "Creating trading table for instrument: " + str(instrumentToken)
                obj = AnnualisedVolatility(INDEX_FUTURE_DATA[instrumentToken]['underlyingsymbol'], INDEX_FUTURE_DATA[instrumentToken]['expiry'])

                annualVolatility = obj.GetAnnualisedVolatility()
                print "Annualised volatility: " + str(annualVolatility)
                price = tick['ohlc']['open']
                # 1 sd formula = annual volatility * price * sqrt(1)/sqrt(365)      // Here 1 is no of days
                _1SD = annualVolatility * price / 19.105 / 100
                fibLevels = [_1SD * i for i in FIB_LEVELS]
                fibUpperLevels = [price + i for i in fibLevels]
                fibLowerLevels = [price - i for i in fibLevels]

                # inserting price at 0th index, so that it can used as sl
                fibUpperLevels.insert(0, price)
                fibLowerLevels.insert(0, price)

                stockDict = {'underlying':INDEX_FUTURE_DATA[instrumentToken]['underlyingsymbol'],
                             'upperlevels':fibUpperLevels, 'lowerlevels':fibLowerLevels}
                stockData = json.dumps(stockDict)
                print stockData
                with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'w+') as f:
                    f.write(stockData)

            elif stockMarkedDone == False:
                with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), 'r') as f:
                    
                    stockDict = json.loads(f.read())
                    lastPrice = tick['last_price']
                    openPrice = tick['ohlc']['open']
                    if lastPrice < openPrice:
                        lowerLevels = stockDict['lowerlevels']
                        sellFlag = False
                        tp=0.0
                        sl=lowerLevels[0]
                        ran = range(1, lowerLevels.__len__() -1)
                        ran.reverse()
                        if lastPrice > lowerLevels[ran[0]]:
                            for i in ran:
                                if lastPrice*(1 - PRICE_PADDING) <= lowerLevels[i]:
                                    tp = float(lowerLevels[i+1])
                                    sl = float(lowerLevels[i-1])
                                    sellFlag = True
                                    break
                        if sellFlag:
                            try:    
                                quantity = AVAILABLE_MARGIN / lastPrice
                                orderNo = SellStock(stockDict['underlying'], lastPrice, tp, sl, quantity, INDEX_FUTURE_DATA[instrumentToken]['tradable'])
                                f.close()
                                os.rename(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_done'))
                                print "Renamed tradable stock | " + str(instrumentToken)
                                with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_place_order'), 'w+') as f: 
                                    f.write(str(orderNo))
                            except Exception as e:
                                print e   

                    else:
                        upperLevels = stockDict['upperlevels']
                        buyFlag = False
                        tp=0.0
                        sl=upperLevels[0]
                        ran = range(1, upperLevels.__len__() -1)
                        ran.reverse()
                        if lastPrice < upperLevels[ran[0]]:
                            for i in ran:
                                if lastPrice *(1+ PRICE_PADDING) <= upperLevels[i]:
                                    tp = float(upperLevels[i+1])
                                    sl = float(upperLevels[i-1])
                                    buyFlag = True
                                    break
                        if buyFlag:
                            try:    
                                quantity = AVAILABLE_MARGIN / lastPrice
                                orderNo = BuyStock(stockDict['underlying'], lastPrice, tp, sl, quantity, INDEX_FUTURE_DATA[instrumentToken]['tradable'])
                                f.close()
                                os.rename(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken)), path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_done'))
                                print "Renamed tradable stock | " + str(instrumentToken)
                                with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_place_order'), 'w+') as f: 
                                    f.write(str(orderNo))
                            except Exception as e:
                                print e
                                pass        # No need to log, as many thread are working at same time
            else:
                print "Time to check n update sl & tp"
                for stock in tradableStockList:
                    if str(instrumentToken) + '_place_order' == stock:
                        with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_place_order'), 'r') as f: 
                            orderNo = f.read()
                            if GetOrderStatus(orderNo) == True:
                                with open(path.join(TRADABLE_STOCK_LOCATION, str(instrumentToken) + '_complete_order'), 'r') as f: 
                                    GetOrderHistory(orderNo)
        except Exception as e:
            print e

def BuyStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In buy"
        targetPoint = abs(lastPrice-tp)
        stopLossPoint = abs(lastPrice-sl)

        # making market order
        tradePrice = (lastPrice + (lastPrice * 0.001)).__format__('.2f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            #orderNo = instance.BuyOrder(symbol, tradePrice, targetPoint, stopLossPoint, quantity)

        #Add order api here
        print "Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
        logging.critical("Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))
        return orderNo

    except Exception as e:
        None

def SellStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In sell"
        targetPoint = abs(lastPrice-tp)
        stopLossPoint = abs(lastPrice-sl)

        # making market order
        tradePrice = (lastPrice - (lastPrice * 0.001)).__format__('.2f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            orderNo = instance.SellOrder(symbol, tradePrice, targetPoint, stopLossPoint, quantity)

        #Add order api here
        print "Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
        logging.critical("Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))
        return orderNo
    except Exception as e:
        print e

def GetOrderStatus(orderNo):
    try:
        instance = KiteOrderManager.GetInstance()
        orderHistory = instance.GetOrderHistory(orderNo)
        len = orderHistory.__len__()
        if orderHistory[len-1]['status'] == 'COMPLETE':
            return True
        return False

    except Exception as e:
        print "Exception in IndexTickAnalyser::GetOrderStatus()"
        print e
        return False

def GetChildOrder(orderNo):
    try:
        instance = KiteOrderManager.GetInstance()
        orderHistory = instance.GetOrdeHistory(orderNo)
        childOrder = []
        for order in orderHistory:
            if order['parent_order_id'] == str(orderNo):
                pass
    except Exception as e:
        print "Exception in IndexTickAnalyser::GetOrderStatus()"
        print e
        return False 