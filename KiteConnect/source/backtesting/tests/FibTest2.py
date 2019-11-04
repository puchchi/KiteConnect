#from source.backtesting import BackTestData, BackTestOrderManager
#from source.backtesting.BackTestOrderManager import OrderManagerStockStruct
#from source.Utility import *

from KiteConnect.source.backtesting import BackTestData, BackTestOrderManager
from KiteConnect.source.backtesting.BackTestOrderManager import OrderManagerStockStruct
from KiteConnect.source.Utility import *
import datetime as dt
import math

# DEFS
ROOT_STOCK_NAME = 'NIFTYBANK'                                   # We will generate report with this name
ROOT_STOCK = 'NIFTY BANK'                 #'NIFTY19JULFUT'
EXCHANGE = 'NSE'
FROM_DATE = '2019-01-01 09:00:00'
TO_DATE = '2019-10-31 16:00:00'
ANNUALISED_VOLATILITY = 0.241
CALL_PUT_MULTIPLE_OF = 100

INTERVAL_MINUTE = 'minute'
INTERVAL_DAY = 'day'
INTERVAL_5MINUTE = '5minute'

TEST_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
REPORT_NAME = 'FibTest'

__FIB_LEVEL_L = [-0.236, -0.382, -0.5, -0.618, -0.786, -0.888, -1.236, -1.618]
__FIB_LEVEL_U = [0.236, 0.382, 0.5, 0.618, 0.786, 0.888, 1.236, 1.618]
#NIFTY_FIB_UPPER_TP_SL_LEVEL = [[__FIB_LEVEL_U[0], 0], [__FIB_LEVEL_U[1], 0], [__FIB_LEVEL_U[2], __FIB_LEVEL_U[0]], [__FIB_LEVEL_U[3], __FIB_LEVEL_U[1]], [__FIB_LEVEL_U[4], __FIB_LEVEL_U[2]], [__FIB_LEVEL_U[5], __FIB_LEVEL_U[3]], [__FIB_LEVEL_U[6], __FIB_LEVEL_U[4]], [__FIB_LEVEL_U[7], __FIB_LEVEL_U[5]]]
#NIFTY_FIB_LOWER_TP_SL_LEVEL = [[__FIB_LEVEL_L[0], 0], [__FIB_LEVEL_L[1], 0], [__FIB_LEVEL_L[2], __FIB_LEVEL_L[0]], [__FIB_LEVEL_L[3], __FIB_LEVEL_L[1]], [__FIB_LEVEL_L[4], __FIB_LEVEL_L[2]], [__FIB_LEVEL_L[5], __FIB_LEVEL_L[3]], [__FIB_LEVEL_L[6], __FIB_LEVEL_L[4]], [__FIB_LEVEL_L[7], __FIB_LEVEL_L[5]]]

NIFTY_FIB_UPPER_TP_SL_LEVEL = [[__FIB_LEVEL_U[1], 0], [__FIB_LEVEL_U[2], __FIB_LEVEL_U[0]], [__FIB_LEVEL_U[3], __FIB_LEVEL_U[1]], [__FIB_LEVEL_U[4], __FIB_LEVEL_U[2]], [__FIB_LEVEL_U[5], __FIB_LEVEL_U[3]], [__FIB_LEVEL_U[6], __FIB_LEVEL_U[4]], [__FIB_LEVEL_U[7], __FIB_LEVEL_U[5]]]
NIFTY_FIB_LOWER_TP_SL_LEVEL = [[__FIB_LEVEL_L[1], 0], [__FIB_LEVEL_L[2], __FIB_LEVEL_L[0]], [__FIB_LEVEL_L[3], __FIB_LEVEL_L[1]], [__FIB_LEVEL_L[4], __FIB_LEVEL_L[2]], [__FIB_LEVEL_L[5], __FIB_LEVEL_L[3]], [__FIB_LEVEL_L[6], __FIB_LEVEL_L[4]], [__FIB_LEVEL_L[7], __FIB_LEVEL_L[5]]]


class FibTest(BackTestData.BackTest):
    
    #################
    # Strategy
    # 1: We will break time frame in week time,
    # Reset on monday
    # If price is going up, buy 1 lot future and 1 lot put for hedging.
    
    def __init__(self):
        BackTestData.BackTest.__init__(self)
        self.fFromDateDT = dt.datetime.strptime(FROM_DATE, TEST_TIME_FORMAT)
        self.fToDateDT = dt.datetime.strptime(TO_DATE, TEST_TIME_FORMAT)
        self.fBackTestOrderManager = BackTestOrderManager.OrderManager(REPORT_NAME ,ROOT_STOCK_NAME)
    
    def __call__(self):
        rootStockInstrument, rootLotSize = self.GetInstrumentTokenAndLotSize(ROOT_STOCK, EXCHANGE)
        
        _fromDateDT = self.fFromDateDT
        
        # If current from date is not monday, then we will shift from date to next monday
        if (_fromDateDT.isoweekday() != 1):
            _fromDateDT += dt.timedelta(days = (7 - _fromDateDT.isoweekday() + 1))
            
        # Now we will get last close value of current stock. To get that, we will get last 7 day daywise data just to be safe side
        last7DayFromDate = (_fromDateDT - dt.timedelta(days=7)).strftime(TEST_TIME_FORMAT)
        last7DayToDate = (_fromDateDT - dt.timedelta(days=0)).strftime(TEST_TIME_FORMAT)
        last7DayData = self.GetHisoricalData(rootStockInstrument, last7DayFromDate, last7DayToDate, INTERVAL_DAY, False)
        if (last7DayData.__len__() == 0):
            print "Last 7 day data of " + str(ROOT_STOCK) + " from start date " + str(last7DayFromDate) + " is nil"
            return 
        
        lastDayClose = last7DayData[-1]['close']

        while (_fromDateDT < self.fToDateDT):
            
            # Getting data of root stock
            _fromDate = _fromDateDT.strftime(TEST_TIME_FORMAT)
            _toDate = (_fromDateDT + dt.timedelta(days=1)).strftime(TEST_TIME_FORMAT)
            rootStockTickData = self.GetHisoricalData(rootStockInstrument, _fromDate, _toDate, INTERVAL_MINUTE, False)
            if (rootStockTickData.__len__()==0):
                _fromDateDT += dt.timedelta(days=1)
                continue
            
            # Get fib levels
            fibUpperLevels, fibLowerLevels = self.GetFibLevels(lastDayClose)#rootStockTickData[0]['open'])#lastDayClose)
            
            isOpenUpTrade = False
            isUpTradeSLHit = False
            isUpTradeComplete = False
            upOrderPositionDetail = []
            
            isOpenDownTrade = False
            isDownTradeSLHit = False
            isDownTradeComplete = False
            downOrderPositionDetail = []
            
            upTradePriceToWatchIndex = 0
            downTradePriceToWatchIndex = 0
            
            # delete me
            rootStockDayTickData = self.GetHisoricalData(rootStockInstrument, _fromDate, _toDate, INTERVAL_DAY, False)
            if (rootStockDayTickData.__len__()>0):
                tempData = rootStockDayTickData[0]
                print " ===================\n"
                print "Date: " + str(tempData['date'].strftime(TEST_TIME_FORMAT)) + ', Open: ' + str(tempData['open']) + ', High: ' + str(tempData['high'])+ ', Low: ' + str(tempData['low'])+ ', Close: ' + str(tempData['close'])
            
            # Now we walk stock data
            for tick in rootStockTickData:
                
                if (isOpenUpTrade and isUpTradeComplete == False):
                    if (tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0] ):#or tick['open'] < fibUpperLevels[upTradePriceToWatchIndex][1]):
                        upTradePriceToWatchIndex +=1
                        
                    if (upTradePriceToWatchIndex == fibUpperLevels.__len__()):
                        self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, tick['date'])
                        upOrderPositionDetail = []
                        isUpTradeComplete = True
                        continue
                    
                    # SL hit
                    if (tick['open'] < fibUpperLevels[upTradePriceToWatchIndex][1]):
                        isUpTradeComplete = True
                        self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, tick['date'])
                        upOrderPositionDetail = []
                        
                elif (isOpenDownTrade and isDownTradeComplete == False):
                    if (tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0] ):#or tick['open'] > fibLowerLevels[downTradePriceToWatchIndex][1]):
                        downTradePriceToWatchIndex += 1
                        
                    if (downTradePriceToWatchIndex == fibLowerLevels.__len__()):
                        self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, tick['date'])
                        downOrderPositionDetail = []
                        isDownTradeComplete = True
                        continue
                    
                    # SL hit
                    if (tick['open'] > fibLowerLevels[downTradePriceToWatchIndex][1]):
                        isDownTradeComplete = True
                        self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, tick['date'])
                        downOrderPositionDetail = []
                        
                elif (isOpenUpTrade == False and tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0]):
                    isOpenUpTrade = True
                    upTradePriceToWatchIndex += 1
                    
                    # Getting stock details for current position
                    stock1 = OrderManagerStockStruct(ROOT_STOCK, rootLotSize, rootLotSize, rootStockTickData, tick['open'], INVALID_PRICE)
                    upOrderPositionDetail.append(stock1)
                    
                    while (tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0]):
                        upTradePriceToWatchIndex += 1
                        #print ' Index: ' + str(upTradePriceToWatchIndex) + ' and fib length: ' + str(fibUpperLevels.__len__())
                        if (upTradePriceToWatchIndex == fibUpperLevels.__len__()):
                            upOrderPositionDetail = []
                            isUpTradeComplete = True
                            break
                        
                    if (isUpTradeComplete == True):
                        continue
                    #if (tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0]):
                    #    self.fBackTestOrderManager.MissedTrigger(upOrderPositionDetail, tick['date'])
                    #    upOrderPositionDetail = []
                    #    isUpTradeComplete = True
                    #    continue
                    
                    self.fBackTestOrderManager.OpenedNewPosition(upOrderPositionDetail, tick['date'])
                    
                elif (isOpenDownTrade == False and tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0] ):
                    isOpenDownTrade = True
                    downTradePriceToWatchIndex += 1
                    
                    # Getting stock details for current position
                    stock1 = OrderManagerStockStruct(ROOT_STOCK, rootLotSize, rootLotSize, rootStockTickData, INVALID_PRICE, tick['open'])
                    downOrderPositionDetail.append(stock1)
                    
                    while (tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0]):
                        downTradePriceToWatchIndex += 1
                        if (downTradePriceToWatchIndex == fibLowerLevels.__len__()):
                            downOrderPositionDetail = []
                            isDownTradeComplete = True
                            break
                    
                    if (isDownTradeComplete == True):
                        continue
                    #if (tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0]):
                    #    self.fBackTestOrderManager.MissedTrigger(downOrderPositionDetail, tick['date'])
                    #    downOrderPositionDetail = []
                    #    isDownTradeComplete = True
                    #    continue
                    
                    self.fBackTestOrderManager.OpenedNewPosition(downOrderPositionDetail, tick['date'])
            
            if (upOrderPositionDetail.__len__()>0):
                self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, rootStockTickData[-1]['date'])
                upOrderPositionDetail = []
                
            if (downOrderPositionDetail.__len__()>0):
                self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, rootStockTickData[-1]['date'])
                downOrderPositionDetail = []
                
            # reset close price 
            if (type(rootStockTickData) == list and rootStockTickData.__len__()>0):
                lastDayClose = rootStockTickData[-1]['close']
            _fromDateDT += dt.timedelta(days=1)
            
        self.fBackTestOrderManager.DumpFullProfitOrLoss()    
        
        
    def GetFibLevels(self, price):
        # 1 sd formula = annual volatility * price * sqrt(1)/sqrt(365)      // Here 1 is no of days
        _1SD = ANNUALISED_VOLATILITY * price * math.sqrt(1/365.00)
        #fibLevels = [_1SD * i for i in FIB_LEVELS]
        #fibUpperLevels = [price + i for i in fibLevels]
        #fibLowerLevels = [price - i for i in fibLevels]
        
        fibUpperLevels = [[price + (j*_1SD) for j in i] for i in NIFTY_FIB_UPPER_TP_SL_LEVEL]
        fibLowerLevels = [[price + (j*_1SD) for j in i] for i in NIFTY_FIB_LOWER_TP_SL_LEVEL]
        
        return [fibUpperLevels, fibLowerLevels]
        
    def GetClosestPutOrCallStrikeSymbol(self, price, putOrCall):
        # We will try to get in the money put
        
        # we will find left & right multiple of price
        leftPrice = int(price/CALL_PUT_MULTIPLE_OF) * CALL_PUT_MULTIPLE_OF
        rightPrice = int(leftPrice + CALL_PUT_MULTIPLE_OF)
        
        # Ideally rightprice should be in the money put, but we will select which ever is closest
        closestPrice = leftPrice
        if ((rightPrice + leftPrice)/2 < price):
            closestPrice = rightPrice
            
        if (putOrCall == 'PUT'):
            return DERIVATIVE_STOCK_PREFIX + str(closestPrice) + 'PE'
        else:
            return DERIVATIVE_STOCK_PREFIX + str(closestPrice) + 'CE'
    
    
if __name__ == '__main__':
    test = FibTest()
    test()
        