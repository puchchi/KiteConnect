from Utility import *
from os import path
from datetime import datetime
from KiteOrderManager import KiteOrderManager
from DatabaseManager import DatabaseManager
import thread, os

def Analyse(ws, ticks):
    print "Tick recieved for " + str(ticks.__len__())
    
    now = int(datetime.now().strftime("%H%M%S"))

    if now >= int(TICKERSTART) and now < int(TRADINGCLOSE):
        Trade(ws, ticks)
    else:
        pass

def Trade(ws, ticks):
    for tick in ticks:
        try:
            instrumentToken = tick['instrument_token']
            openPrice = tick['ohlc']['open']
            lastPrice = tick['last_price']
            levelCrossType = LEVEL_CROSS_TYPE_ENUM[0]
            if lastPrice < openPrice:
                levelCrossType = LEVEL_CROSS_TYPE_ENUM[1]

            # Get tasks list from DB
            dbInstance = DatabaseManager.GetInstance()
            todoTaskList = dbInstance.GetToDoTaskList(instrumentToken)

            if todoTaskList.__len__() == 0:
                dbInstance.CreateOneSDLevelsAndSetupInitialTask(instrumentToken, openPrice)
            else:
                # todo table index [0:InstrumentToken, 1:symbol, 2:TPLevelType, 3:LevelPrice, 4:TP, 5:SL, 6:TaskType, 7:LevelCrossType, 8:OrderNo(Null)
                for task in todoTaskList:
                    if task[7] == levelCrossType and lastPrice > task[3]:
                        PlacePriceUpOrder(task)
                    elif task[7] == levelCrossType and lastPrice < task[3]:
                        PlacePriceDownOrder(task)

        except Exception as e:
            print "Exception in IndexTickAnalyser::Trade()"
            print e

def PlacePriceUpOrder(task, lastPrice):
    if task[6] == TASK_TYPE_ENUM[0]:        #'buy'
        # First of all delete this task from db, if function is able to delete, it means
        # no other thread can process this task even if it has got data extracted from db
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                levelType = task[2]
                # Place order
                buyOrderNo = BuyStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                
                if 0:
                    # Now check status of this order and on completion, put 2 todo order in db
                    while GetOrderStatus(orderNo) == False:
                        time.sleep(5)

                    # We are here, it means buy order completed
                    childOrder = GetChildOrder(orderNo)
                    for order in childOrder:
                        if order['order_type']=='LIMIT':
                            orderId = order['order_id']
                            levelPrice = order['price']*(1-0.0005)
                            nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
                            if nxtLevel.__len__() != 1:
                                print "Critical error"
                                return
                            nextTP = nxtLevel[0][1]
                            nextLevelType = nxtLevel[0][0]
                            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[0], orderId)
                    
                        elif order['order_type'] == 'SL':
                            orderId = order['order_id']
                            levelPrice = order['price']*(1-0.0005)
                            nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
                            if nxtLevel.__len__() != 1:
                                print "Critical error"
                                return
                            nextTP = nxtLevel[0][1]
                            nextLevelType = nxtLevel[0][0]
                            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[0], orderId)
                    
        except Exception as e:
            print e

    elif task[6] == TASK_TYPE_ENUM[2]:      #'tp_update'
        pass
    elif task[6] == TASK_TYPE_ENUM[3]:      #'sl_update'
        pass


def PlacePriceDownOrder(task, lastPrice):
    if task[6] == TASK_TYPE_ENUM[1]:        #'sell'
        # First of all delete this task from db, if function is able to delete, it means
        # no other thread can process this task even if it has got data extracted from db
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                levelType = task[2]
                # Place order
                sellOrderNo = SellStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                
        except Exception as e:
            print e

def BuyStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In buy"
        targetPoint = int(abs(lastPrice-tp))
        stopLossPoint = int(abs(lastPrice-sl))
        trailingSL = stopLossPoint

        # making market order
        tradePrice = (lastPrice + (lastPrice * 0.001)).__format__('.2f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            orderNo = instance.BuyOrder(symbol, tradePrice, targetPoint, stopLossPoint, trailingSL, quantity)

        #Add order api here
        print "Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
        logging.critical("Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))
        return orderNo

    except Exception as e:
        None

def SellStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In sell"
        targetPoint = int(abs(lastPrice-tp))
        stopLossPoint = int(abs(lastPrice-sl))
        trailingSL = stopLossPoint

        # making market order
        tradePrice = (lastPrice - (lastPrice * 0.001)).__format__('.2f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            orderNo = instance.SellOrder(symbol, tradePrice, targetPoint, stopLossPoint, trailingSL, quantity)

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
        orders = instance.GetOrders()
        childOrder = []
        for order in orders:
            if order['parent_order_id'] == str(orderNo):
                childOrder.append(order)
        return childOrder
    except Exception as e:
        print "Exception in IndexTickAnalyser::GetOrderStatus()"
        print e
        return False 
    return []