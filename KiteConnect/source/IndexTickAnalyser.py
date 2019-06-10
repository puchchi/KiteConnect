import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
sys.path.append( path.dirname( path.dirname( path.dirname(path.abspath(__file__)) ) ) )

from Utility import *
from os import path
from datetime import datetime
from KiteOrderManager import KiteOrderManager
from DatabaseManager import DatabaseManager
import thread, os, time

def Analyse(ws, ticks):
    print "Tick recieved for " + str(ticks.__len__())
    Trade(ws, ticks)

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
            [isSuccessfull, todoTaskList] = dbInstance.GetToDoTaskList(instrumentToken)

            if isSuccessfull == False:
                return

            if todoTaskList.__len__() == 0:
                dbInstance.CreateOneSDLevelsAndSetupInitialTask(instrumentToken, openPrice)
            else:
                # todo table index [0:InstrumentToken, 1:symbol, 2:TPLevelType, 3:LevelPrice, 4:TP, 5:SL, 6:TaskType, 7:LevelCrossType, 8:OrderNo(Null)
                for task in todoTaskList:
                    if task[7] == LEVEL_CROSS_TYPE_ENUM[0] and levelCrossType == LEVEL_CROSS_TYPE_ENUM[0] and lastPrice >= task[3]:
                        PlacePriceUpOrder(list(task), lastPrice)
                    elif task[7] == LEVEL_CROSS_TYPE_ENUM[1] and levelCrossType == LEVEL_CROSS_TYPE_ENUM[1] and lastPrice <= task[3]:
                        PlacePriceDownOrder(list(task), lastPrice)

        except Exception as e:
            DumpExceptionInfo(e, "Trade")

def PlacePriceUpOrder(task, lastPrice):
    if task[6] == TASK_TYPE_ENUM[0]:        #'buy'
        # First of all delete this task from db, if function is able to delete, it means
        # no other thread can process this task even if it has got data extracted from db
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                levelType = task[2]
                tp = task[4]
                sl = task[5]
                prevTp = tp
                while 1:
                    nextLevel = dbInstance.GetNextLevel(task[0], levelType)
                    if nextLevel.__len__() == 0:
                        break
                    if lastPrice < nextLevel[0][1]:
                        break
                    prevLevel = dbInstance.GetPrevLevel(task[0], levelType)
                    if prevLevel.__len__() == 0:
                        break
                    if lastPrice > nextLevel[0][1]:
                        levelType = nextLevel[0][0]
                        tp = nextLevel[0][1]
                        sl = prevLevel[0][1]

                task[2] = levelType
                task[4] = tp
                task[5] = sl
                # Place order
                buyOrderNo = BuyStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                if buyOrderNo == '':
                    print 'No buy order placed!!!Trying to sell again'
                    buyOrderNo = BuyStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                if buyOrderNo == '':
                    return

                # Now check status of this order and on completion, put 2 todo order in db
                while GetOrderStatus_COMPLETE(buyOrderNo) == False:
                    time.sleep(5)

                # We are here, it means buy order completed
                childOrder = GetChildOrder(buyOrderNo)
                SetTpUpdateNSlUpdateOrder_UP(task, childOrder)
                    
        except Exception as e:
            print e

    elif task[6] == TASK_TYPE_ENUM[2]:      #'tp_update'
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                kiteInstance = KiteOrderManager.GetInstance()
                kiteInstance.ModifyBOTpOrder(task[8], task[4])
                SetTpUpdateOrder_UP(task)
        except Exception as e:
            print e

    elif task[6] == TASK_TYPE_ENUM[3]:      #'sl_update'
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                kiteInstance = KiteOrderManager.GetInstance()
                kiteInstance.ModifyBOSlOrder(task[8], task[5])
                SetSlUpdateOrder_UP(task)
        except Exception as e:
            print e

def SetTpUpdateNSlUpdateOrder_UP(task, childOrder):
    tpFound = False
    slFound = False

    tpOfPosition = 0
    tpOrderID = 0

    slOfPosition = 0
    slOrderID = 0
    for order in childOrder:
        if order['order_type']=='LIMIT':
            tpFound = True
            tpOrderID = order['order_id']
            tpOfPosition = order['price']        
        elif order['order_type'] == 'SL':
            slFound = True
            slOrderID = order['order_id']

    dbInstance = DatabaseManager.GetInstance()

    # This level is already 1 down of current tp, so we need to get next level type then set tpupdate n slupdate task
    levelType = task[2]
    tmpNxtLevel = dbInstance.GetNextLevel(task[0], levelType)
    if tmpNxtLevel.__len__()==0:
        return
    #levelType = tmpNxtLevel[0][0]

    if tpFound:
        levelPrice = tpOfPosition*(1-0.0005)
        nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
        if nxtLevel.__len__() >0:
            nextTP = nxtLevel[0][1]
            nextLevelType = nxtLevel[0][0]
            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[0], tpOrderID)

    if slFound:
        levelPrice = tpOfPosition*(1-0.0003)
        # Only first time we need prev level, for other time, we need next level
        prevLevel = dbInstance.GetPrevLevel(task[0], levelType)
        if prevLevel.__len__() >0:
            nextSL = prevLevel[0][1]
            nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
            if nxtLevel.__len__() >0:
                nextLevelType = nxtLevel[0][0]
                dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, 0.0, nextSL, TASK_TYPE_ENUM[3], LEVEL_CROSS_TYPE_ENUM[0], slOrderID)
                         
def SetTpUpdateOrder_UP(task):
    # Now before setting another order, check whether this order is still open or not
    if OrderClosed(task[8]):
        return

    levelType = task[2]
    levelPrice = task[4]*(1-0.0005)

    dbInstance = DatabaseManager.GetInstance()
    nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
    if nxtLevel.__len__() >0:
        nextTP = nxtLevel[0][1]
        nextLevelType = nxtLevel[0][0]
        dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[0], task[8])

def SetSlUpdateOrder_UP(task):
    # Now before setting another order, check whether this order is still open or not
    if OrderClosed(task[8]):
        return
    levelType = task[2]
    nextSL = task[3]        # current level(old tp) will be new sl
    dbInstance = DatabaseManager.GetInstance()
    currentLevel = dbInstance.GetCurrentLevel(task[0], levelType)
    if currentLevel.__len__() >0:
        nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
        if nxtLevel.__len__() >0:
            nextLevelType = nxtLevel[0][0]
            nextLevelPrice = currentLevel[0][1]*(1-0.0003)
            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, nextLevelPrice, 0.0, nextSL, TASK_TYPE_ENUM[3], LEVEL_CROSS_TYPE_ENUM[0], task[8])


def PlacePriceDownOrder(task, lastPrice):
    if task[6] == TASK_TYPE_ENUM[1]:        #'sell'
        # First of all delete this task from db, if function is able to delete, it means
        # no other thread can process this task even if it has got data extracted from db
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                levelType = task[2]
                tp = task[4]
                sl = task[5]
                prevTp = tp
                while 1:
                    nextLevel = dbInstance.GetNextLevel(task[0], levelType)
                    if nextLevel.__len__() == 0:
                        break
                    if lastPrice > nextLevel[0][1]:
                        break
                    prevLevel = dbInstance.GetPrevLevel(task[0], levelType)
                    if prevLevel.__len__() == 0:
                        break
                    if lastPrice < nextLevel[0][1]:
                        levelType = nextLevel[0][0]
                        tp = nextLevel[0][1]
                        sl = prevLevel[0][1]

                task[2] = levelType
                task[4] = tp
                task[5] = sl
                # Place order
                sellOrderNo = SellStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                if sellOrderNo == '':
                    print 'No sell order placed!!!Trying to sell again'
                    sellOrderNo = SellStock(task[1], lastPrice, task[4], task[5], INDEX_FUTURE_DATA[task[0]]['quantity'], INDEX_FUTURE_DATA[task[0]]['tradable'])
                if sellOrderNo == '':
                    return

                # Now check status of this order and on completion, put 2 todo order in db
                while GetOrderStatus_COMPLETE(sellOrderNo) == False:
                    time.sleep(5)

                # We are here, it means buy order completed
                childOrder = GetChildOrder(sellOrderNo)
                SetTpUpdateNSlUpdateOrder_DOWN(task, childOrder)
        except Exception as e:
            print e

    elif task[6] == TASK_TYPE_ENUM[2]:      #'tp_update'
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                kiteInstance = KiteOrderManager.GetInstance()
                kiteInstance.ModifyBOTpOrder(task[8], task[4])
                SetTpUpdateOrder_DOWN(task)
        except Exception as e:
            print e

    elif task[6] == TASK_TYPE_ENUM[3]:      #'sl_update'
        try:
            dbInstance = DatabaseManager.GetInstance()
            if dbInstance.DeleteToDoTask(task) > 0:
                kiteInstance = KiteOrderManager.GetInstance()
                kiteInstance.ModifyBOSlOrder(task[8], task[5])
                SetSlUpdateOrder_DOWN(task)
        except Exception as e:
            DumpExceptionInfo(e, "PlacePriceDownOrder")

def SetTpUpdateNSlUpdateOrder_DOWN(task, childOrder):
    tpFound = False
    slFound = False

    tpOfPosition = 0
    tpOrderID = 0

    slOfPosition = 0
    slOrderID = 0
    for order in childOrder:
        if order['order_type']=='LIMIT':
            tpFound = True
            tpOrderID = order['order_id']
            tpOfPosition = order['price']        
        elif order['order_type'] == 'SL':
            slFound = True
            slOrderID = order['order_id']
    
    dbInstance = DatabaseManager.GetInstance()

    # This level is already 1 down of current tp, so we need to get next level type then set tpupdate n slupdate task
    levelType = task[2]
    tmpNxtLevel = dbInstance.GetNextLevel(task[0], levelType)
    if tmpNxtLevel.__len__()==0:
        return
    #levelType = tmpNxtLevel[0][0]

    if tpFound:
        levelPrice = tpOfPosition*(1+0.0005)
        nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
        if nxtLevel.__len__() >0:
            nextTP = nxtLevel[0][1]
            nextLevelType = nxtLevel[0][0]
            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[1], tpOrderID)

    if slFound:
        levelPrice = tpOfPosition(1+0.0003)
        # Only first time we need prev level, for other time, we need next level
        prevLevel = dbInstance.GetPrevLevel(task[0], levelType)
        if prevLevel.__len__() >0:
            nextSL = prevLevel[0][1]
            nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
            if nxtLevel.__len__() >0:
                nextLevelType = nxtLevel[0][0]
                dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, 0.0, nextSL, TASK_TYPE_ENUM[3], LEVEL_CROSS_TYPE_ENUM[1], slOrderID)
                         
def SetTpUpdateOrder_DOWN(task):
    # Now before setting another order, check whether this order is still open or not
    if OrderClosed(task[8]):
        return
    levelType = task[2]
    levelPrice = task[4]*(1+0.0005)

    dbInstance = DatabaseManager.GetInstance()
    nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
    if nxtLevel.__len__() >0:
        nextTP = nxtLevel[0][1]
        nextLevelType = nxtLevel[0][0]
        dbInstance.CreateNewTask(task[0], task[1], nextLevelType, levelPrice, nextTP, 0.0, TASK_TYPE_ENUM[2], LEVEL_CROSS_TYPE_ENUM[1], task[8])

def SetSlUpdateOrder_DOWN(task):
    # Now before setting another order, check whether this order is still open or not
    if OrderClosed(task[8]):
        return
    levelType = task[2]
    nextSL = task[3]        # current level(old tp) will be new sl
    dbInstance = DatabaseManager.GetInstance()
    currentLevel = dbInstance.GetCurrentLevel(task[0], levelType)
    if currentLevel.__len__() >0:
        nxtLevel = dbInstance.GetNextLevel(task[0], levelType)
        if nxtLevel.__len__() >0:
            nextLevelType = nxtLevel[0][0]
            nextLevelPrice = currentLevel[0][1]*(1+0.0003)
            dbInstance.CreateNewTask(task[0], task[1], nextLevelType, nextLevelPrice, 0.0, nextSL, TASK_TYPE_ENUM[3], LEVEL_CROSS_TYPE_ENUM[1], task[8])

def BuyStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In buy"
        targetPoint = int(abs(lastPrice-tp))
        stopLossPoint = int(abs(lastPrice-sl))
        trailingSL = stopLossPoint

        # making market order
        tradePrice = (lastPrice + (lastPrice * 0.001)).__format__('.1f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            orderNo = instance.BuyOrder(symbol, tradePrice, targetPoint, stopLossPoint, trailingSL, quantity)

        #Add order api here
        print "Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
        logging.critical("Buy order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))
        return orderNo

    except Exception as e:
        DumpExceptionInfo(e, "BuyStock")

def SellStock(symbol, lastPrice, tp, sl, quantity, istradable):
    try:
        print "In sell"
        targetPoint = int(abs(lastPrice-tp))
        stopLossPoint = int(abs(lastPrice-sl))
        trailingSL = stopLossPoint

        # making market order
        tradePrice = (lastPrice - (lastPrice * 0.001)).__format__('.1f')

        orderNo = 0
        if istradable:
            instance = KiteOrderManager.GetInstance()
            orderNo = instance.SellOrder(symbol, tradePrice, targetPoint, stopLossPoint, trailingSL, quantity)

        #Add order api here
        print "Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint)
        logging.critical("Sell order triggered of " + symbol + " at " + str(tradePrice) + " with target point " + str(targetPoint) + " and stoploss point " + str(stopLossPoint))
        return orderNo
    except Exception as e:
        DumpExceptionInfo(e, "SellStock")

def GetOrderStatus_COMPLETE(orderNo):
    try:
        instance = KiteOrderManager.GetInstance()
        orderHistory = instance.GetOrderHistory(orderNo)
        len = orderHistory.__len__()
        if orderHistory[len-1]['status'] == 'COMPLETE':
            return True
        return False

    except Exception as e:
        DumpExceptionInfo(e, "GetOrderStatus_COMPLETE")
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
        DumpExceptionInfo(e, "GetChildOrder")
        return False 
    return []

def DumpExceptionInfo(e, funcName):
    logging.error("Error in IndexTickAnalyser::" + funcName, exc_info=True)
    print e
    print "Error in IndexTickAnalyser::" + funcName

def OrderClosed(orderNo):
    try:
        instance = KiteOrderManager.GetInstance()
        orderHistory = instance.GetOrderHistory(orderNo)
        len = orderHistory.__len__()
        if orderHistory[len-1]['status'] == 'COMPLETE' or orderHistory[len-1]['status'] == 'CANCELLED':
            return True
        return False

    except Exception as e:
        DumpExceptionInfo(e, "OrderClosed")
        return False