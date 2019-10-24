from source.backtesting import BackTestData, BackTestOrderManager
from source.backtesting.BackTestOrderManager import OrderManagerStockStruct
from source.Utility import *

#from KiteConnect.source.backtesting import BackTestData, BackTestOrderManager
#from KiteConnect.source.backtesting.BackTestOrderManager import OrderManagerStockStruct
#from KiteConnect.source.Utility import *
import datetime as dt
import math

# DEFS
ROOT_STOCK_NAME = 'NIFTY'                                   # We will generate report with this name
DERIVATIVE_STOCK_PREFIX = 'NIFTY19OCT'
ROOT_STOCK = DERIVATIVE_STOCK_PREFIX + 'FUT'                 #'NIFTY19JULFUT'
SUB_STOCK_LIST = [DERIVATIVE_STOCK_PREFIX + '12000CE', DERIVATIVE_STOCK_PREFIX + '11900PE']
EXCHANGE = 'NFO'
FROM_DATE = '2019-10-01 09:00:00'
TO_DATE = '2019-10-31 16:00:00'
ANNUALISED_VOLATILITY = 0.13
CALL_PUT_MULTIPLE_OF = 50

INTERVAL_MINUTE = 'minute'
INTERVAL_DAY = 'day'
INTERVAL_5MINUTE = '5minute'

TEST_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
REPORT_NAME = 'FibTest'

__FIB_LEVEL_L = [-0.236, -0.382, -0.5, -0.618, -0.786, -0.888, -1.236, -1.618]
__FIB_LEVEL_U = [0.236, 0.382, 0.5, 0.618, 0.786, 0.888, 1.236, 1.618]
NIFTY_FIB_UPPER_TP_SL_LEVEL = [[__FIB_LEVEL_U[0], __FIB_LEVEL_L[1]], [__FIB_LEVEL_U[1], __FIB_LEVEL_L[1]], [__FIB_LEVEL_U[2], __FIB_LEVEL_L[1]], [__FIB_LEVEL_U[3], __FIB_LEVEL_U[1]], [__FIB_LEVEL_U[4], __FIB_LEVEL_U[2]], [__FIB_LEVEL_U[5], __FIB_LEVEL_U[3]], [__FIB_LEVEL_U[6], __FIB_LEVEL_U[4]], [__FIB_LEVEL_U[7], __FIB_LEVEL_U[5]]]
NIFTY_FIB_LOWER_TP_SL_LEVEL = [[__FIB_LEVEL_L[0], __FIB_LEVEL_U[1]], [__FIB_LEVEL_L[1], __FIB_LEVEL_U[1]], [__FIB_LEVEL_L[2], __FIB_LEVEL_U[1]], [__FIB_LEVEL_L[3], __FIB_LEVEL_L[1]], [__FIB_LEVEL_L[4], __FIB_LEVEL_L[2]], [__FIB_LEVEL_L[5], __FIB_LEVEL_L[3]], [__FIB_LEVEL_L[6], __FIB_LEVEL_L[4]], [__FIB_LEVEL_L[7], __FIB_LEVEL_L[5]]]

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
        last7DayData = self.GetHisoricalData(rootStockInstrument, last7DayFromDate, last7DayToDate, INTERVAL_DAY, True)
        if (last7DayData.__len__() == 0):
            print "Last 7 day data of " + str(ROOT_STOCK) + " from start date " + str(last7DayFromDate) + " is nil"
            return 
        
        lastWeekClose = last7DayData[-1]['close']

        while (_fromDateDT < self.fToDateDT):
            
            # Get fib levels
            fibUpperLevels, fibLowerLevels = self.GetFibLevels(lastWeekClose)
            
            isOpenUpTrade = False
            isUpTradeSLHit = False
            upOrderPositionDetail = []
            
            isOpenDownTrade = False
            isDownTradeSLHit = False
            downOrderPositionDetail = []
            
            upTradePriceToWatchIndex = 0
            downTradePriceToWatchIndex = 0
            putLegTickData = []
            callLegTickData = []
            
            # Getting data of root stock
            _fromDate = _fromDateDT.strftime(TEST_TIME_FORMAT)
            _toDate = (_fromDateDT + dt.timedelta(days=6)).strftime(TEST_TIME_FORMAT)
            rootStockTickData = self.GetHisoricalData(rootStockInstrument, _fromDate, _toDate, INTERVAL_DAY, True)
            
            # Now we walk stock data
            for tick in rootStockTickData:
                
                if (isOpenUpTrade):
                    if (tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0]):
                        upTradePriceToWatchIndex += 1
                        
                    # SL hit
                    if (tick['open'] < fibUpperLevels[upTradePriceToWatchIndex][1]):
                        isUpTradeSLHit = True
                        self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, tick['date'])
                        upOrderPositionDetail = []
                        
                elif (isOpenDownTrade):
                    if (tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0]):
                        downTradePriceToWatchIndex += 1
                        
                    # SL hit
                    if (tick['open'] > fibLowerLevels[downTradePriceToWatchIndex][1]):
                        isDownTradeSLHit = True
                        self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, tick['date'])
                        downOrderPositionDetail = []
                        
                elif (tick['open'] > fibUpperLevels[upTradePriceToWatchIndex][0] and isUpTradeSLHit == False):
                    isOpenUpTrade = True
                    upTradePriceToWatchIndex += 1
                    closestPutSymbol = self.GetClosestPutOrCallStrikeSymbol(tick['open'], 'PUT')
                    putLegInstrument, putLegLotSize = self.GetInstrumentTokenAndLotSize(closestPutSymbol, EXCHANGE)
                    putLegTickData = self.GetHisoricalData(putLegInstrument, _fromDate, _toDate, INTERVAL_DAY, True)
                    
                    # Getting stock details for current position
                    stock1 = OrderManagerStockStruct(ROOT_STOCK, rootLotSize, rootLotSize, rootStockTickData, tick['open'], INVALID_PRICE)
                    stock2 = OrderManagerStockStruct(closestPutSymbol, putLegLotSize, putLegLotSize, putLegTickData, BackTestData.GetOpenPriceAtTime(tick['date'], putLegTickData), INVALID_PRICE)
                    upOrderPositionDetail.append(stock1)
                    upOrderPositionDetail.append(stock2)
                    
                    self.fBackTestOrderManager.OpenedNewPosition(upOrderPositionDetail, tick['date'])
                    
                elif (tick['open'] < fibLowerLevels[downTradePriceToWatchIndex][0] and isDownTradeSLHit == False):
                    isOpenDownTrade = True
                    downTradePriceToWatchIndex += 1
                    closestCallSymbol = self.GetClosestPutOrCallStrikeSymbol(tick['open'], 'CALL')
                    callLegInstrument, callLegLotSize = self.GetInstrumentTokenAndLotSize(closestCallSymbol, EXCHANGE)
                    callLegTickData = self.GetHisoricalData(callLegInstrument, _fromDate, _toDate, INTERVAL_DAY, True)
                    
                    # Getting stock details for current position
                    stock1 = OrderManagerStockStruct(ROOT_STOCK, rootLotSize, rootLotSize, rootStockTickData, INVALID_PRICE, tick['open'])
                    stock2 = OrderManagerStockStruct(closestCallSymbol, callLegLotSize, callLegLotSize, callLegTickData, BackTestData.GetOpenPriceAtTime(tick['date'], callLegTickData), INVALID_PRICE)
                    downOrderPositionDetail.append(stock1)
                    downOrderPositionDetail.append(stock2)
                    
                    self.fBackTestOrderManager.OpenedNewPosition(downOrderPositionDetail, tick['date'])
            
            if (upOrderPositionDetail.__len__()>0):
                self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, rootStockTickData[-1]['date'])
                upOrderPositionDetail = []
                
            if (downOrderPositionDetail.__len__()>0):
                self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, rootStockTickData[-1]['date'])
                downOrderPositionDetail = []
                
            # reset close price 
            lastWeekClose = rootStockTickData[-1]['close']
            _fromDateDT += dt.timedelta(days=7)
            
        self.fBackTestOrderManager.DumpFullProfitOrLoss()    
        
        
    def GetFibLevels(self, price):
        # 1 sd formula = annual volatility * price * sqrt(1)/sqrt(365)      // Here 1 is no of days
        _1SD = ANNUALISED_VOLATILITY * price * math.sqrt(7.00/365.00)
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
        