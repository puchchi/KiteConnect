from source.backtesting import BackTestData, BackTestOrderManager
from source.backtesting.BackTestOrderManager import OrderManagerStockStruct
from source.Utility import *

<<<<<<< HEAD
from KiteConnect.source.backtesting import BackTestData, BackTestOrderManager
from KiteConnect.source.backtesting.BackTestOrderManager import OrderManagerStockStruct
from KiteConnect.source.Utility import *

import matplotlib.dates as mdates
=======
#from KiteConnect.source.backtesting import BackTestData, BackTestOrderManager
#from KiteConnect.source.backtesting.BackTestOrderManager import OrderManagerStockStruct
#from KiteConnect.source.Utility import *
>>>>>>> 5b740e0e15762772fa2f90acfa54ccdd706b243c
import datetime as dt
import math

# DEFS
ROOT_STOCK_NAME = 'NIFTY50Stocks'                                   # We will generate report with this name
ROOT_STOCK = ''                 #'NIFTY19JULFUT'
#ROOT_STOCK_LIST = ['NIFTY BANK',]
ROOT_STOCK_LIST = ["SBIN", "ICICIBANK", "HDFC", "KOTAKBANK", "HDFCBANK", "AXISBANK", "TATASTEEL", "CIPLA", "INFY", "BPCL", "COALINDIA", 
             "NTPC", "POWERGRID", "ONGC", "BAJFINANCE", "INFRATEL", "JSWSTEEL", "TATAMOTORS", "HEROMOTOCO", "SUNPHARMA", "DRREDDY",
             "HCLTECH", "ULTRACEMCO", "HINDUNILVR", "VEDL", "GRASIM", "TECHM","INDUSINDBK", "GAIL","ASIANPAINT", "EICHERMOT",
             "RELIANCE", "BHARTIARTL", "TITAN", "WIPRO", "INFY", "MARUTI", "IBULHSGFIN", "ZEEL", "ADANIPORTS", "UPL", "IOC", "BAJAJFINSV"]
EXCHANGE = 'NSE'
FROM_DATE = '2019-01-01 09:00:00'
TO_DATE = '2019-01-31 16:00:00'
GAPUP_THRESHOLD = 1
GAPUP_TARGETPER = 0.5
GAPUP_STOPLOSSPER = 0.5

GAPDOWN_THRESHOLD = 1
GAPDOWN_TARGETPER = 0.5
GAPDOWN_STOPLOSSPER = 0.5

INTERVAL_MINUTE = 'minute'
INTERVAL_DAY = 'day'
INTERVAL_5MINUTE = '5minute'

TEST_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
REPORT_NAME = 'GapUpDownOpening'



class GapUpDownOpening(BackTestData.BackTest):
    
    #################
    
    def __init__(self):
        BackTestData.BackTest.__init__(self)
        self.fFromDateDT = dt.datetime.strptime(FROM_DATE, TEST_TIME_FORMAT)
        self.fToDateDT = dt.datetime.strptime(TO_DATE, TEST_TIME_FORMAT)
        self.fBackTestOrderManager = BackTestOrderManager.OrderManager(REPORT_NAME ,ROOT_STOCK_NAME)
    
    def __call__(self):
        
        graphDateList = mdates.drange(self.fFromDateDT, self.fToDateDT, dt.timedelta(days=1))
        graphDateListDT = []
        s = self.fFromDateDT
        e = self.fToDateDT
        while (s<=e):
            graphDateListDT.append(s)
            s += dt.timedelta(days=1)
        if (graphDateList.__len__() != graphDateListDT.__len__()):
            print "GraphDateList and DT length mismatch"
            return
        graphDataList = [0,] * graphDateList.__len__()
        
        for stock in ROOT_STOCK_LIST:
            rootStockInstrument, rootLotSize = self.GetInstrumentTokenAndLotSize(stock, EXCHANGE)
            
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
            #print "here"
            # Getting data of root stock
            _fromDate = _fromDateDT.strftime(TEST_TIME_FORMAT)
            _toDate = self.fToDateDT.strftime(TEST_TIME_FORMAT)
            rootStockDayTickData = self.GetHisoricalData(rootStockInstrument, _fromDate, _toDate, INTERVAL_DAY, False)
            tickLen = rootStockDayTickData.__len__()
            index = 0
            while (_fromDateDT < self.fToDateDT and index < tickLen) :
                
                profitOrLoss = 0
                # Getting data of root stock
                #_fromDate = _fromDateDT.strftime(TEST_TIME_FORMAT)
                #_toDate = (_fromDateDT + dt.timedelta(days=1)).strftime(TEST_TIME_FORMAT)
                #rootStockTickData = self.GetHisoricalData(rootStockInstrument, _fromDate, _toDate, INTERVAL_MINUTE, False)
                openPrice = rootStockDayTickData[index]['open']
                #print openPrice
                gapPer = (openPrice - lastDayClose)/lastDayClose * 100
                if (abs(gapPer) < GAPUP_THRESHOLD and abs(gapPer) < GAPDOWN_THRESHOLD):
                    lastDayClose = rootStockDayTickData[index]['close']
                    _fromDateDT += dt.timedelta(days=1)
                    index += 1
                    continue
                
                upOrderPositionDetail = []
                downOrderPositionDetail = []
                
                currentDate = rootStockDayTickData[index]['date']
                _tmpFromDate = currentDate.strftime(TEST_TIME_FORMAT)
                _tmpToDate = (currentDate + dt.timedelta(days=1)).strftime(TEST_TIME_FORMAT)
                
                rootStockMinuteTickData = self.GetHisoricalData(rootStockInstrument, _tmpFromDate, _tmpToDate, INTERVAL_MINUTE, False)
                #if (rootStockDayTickData.__len__()>0):
                #    tempData = rootStockDayTickData[0]
                #    print " ===================\n"
                #    print "Date: " + str(tempData['date'].strftime(TEST_TIME_FORMAT)) + ', Open: ' + str(tempData['open']) + ', High: ' + str(tempData['high'])+ ', Low: ' + str(tempData['low'])+ ', Close: ' + str(tempData['close'])
                
                if (rootStockMinuteTickData.__len__()<=0):
                    lastDayClose = rootStockDayTickData[index]['close']
                    _fromDateDT += dt.timedelta(days=1)
                    index += 1
                    continue
                print (rootStockMinuteTickData[0]['date'])
                targetPrice = 0.0
                stopLoss = 0.0
                if (gapPer > 0):
                    targetPrice = openPrice*(1.0-GAPUP_TARGETPER/100.0)
                    stopLoss = openPrice*(1.0+GAPUP_STOPLOSSPER/100.0)
                    
                    # Getting stock details for current position
                    stock1 = OrderManagerStockStruct(stock, rootLotSize, rootLotSize, rootStockMinuteTickData, INVALID_PRICE, rootStockMinuteTickData[0]['open'])
                    upOrderPositionDetail.append(stock1)
                    
                    
                    self.fBackTestOrderManager.OpenedNewPosition(upOrderPositionDetail, rootStockMinuteTickData[0]['date'])
                        
                else:
                    targetPrice = openPrice*(1.0+GAPDOWN_TARGETPER/100.0)
                    stopLoss = openPrice*(1.0-GAPDOWN_STOPLOSSPER/100.0)
                    
                    stock1 = OrderManagerStockStruct(ROOT_STOCK, rootLotSize, rootLotSize, rootStockMinuteTickData, rootStockMinuteTickData[0]['open'], INVALID_PRICE)
                    downOrderPositionDetail.append(stock1)
                    
                    self.fBackTestOrderManager.OpenedNewPosition(downOrderPositionDetail, rootStockMinuteTickData[0]['date'])
                    
                #print 2
                # Now we walk stock data
                for tick in rootStockMinuteTickData[1:-1]:
                    
                    if (gapPer > 0):
                        if (tick['open'] < targetPrice or tick['open'] > stopLoss ):#or tick['open'] < fibUpperLevels[upTradePriceToWatchIndex][1]):
                            profitOrLoss = self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, tick['date'])
                            upOrderPositionDetail = []
                            break
                            
                    elif (gapPer<0):
                        if (tick['open'] > targetPrice or tick['open'] < stopLoss ):#or tick['open'] > fibLowerLevels[downTradePriceToWatchIndex][1]):
                            profitOrLoss = self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, tick['date'])
                            downOrderPositionDetail = []
                            break
                #print 3
                if (upOrderPositionDetail.__len__()>0):
                    profitOrLoss = self.fBackTestOrderManager.CloseTrade(upOrderPositionDetail, rootStockMinuteTickData[-1]['date'])
                    upOrderPositionDetail = []
                    
                if (downOrderPositionDetail.__len__()>0):
                    profitOrLoss = self.fBackTestOrderManager.CloseTrade(downOrderPositionDetail, rootStockMinuteTickData[-1]['date'])
                    downOrderPositionDetail = []
                    
                # Updating datelist to current date
                dateIndex = 0
                tmpStartDate = graphDateListDT[dateIndex]
                while (dateIndex < graphDateListDT.__len__()):
                    if (tmpStartDate.strftime("%Y%m%d") == rootStockMinuteTickData[0]['date'].strftime("%Y%m%d")):
                        if (profitOrLoss > 0):
                            graphDataList[dateIndex] += 1
                        elif (profitOrLoss < 0):
                            graphDataList[dateIndex] -= 1
                            
                        break
                    dateIndex += 1
                    tmpStartDate = graphDateListDT[dateIndex]
                    
                # reset close price 
                lastDayClose = rootStockDayTickData[index]['close']
                _fromDateDT += dt.timedelta(days=1)
                index += 1
                
            self.fBackTestOrderManager.DumpFullProfitOrLoss() 
        
        totalProfitOrLoss = 0
        for i in range(graphDataList.__len__()):
            graphDataList[i] += totalProfitOrLoss
            totalProfitOrLoss = graphDataList[i]
               
        self.fBackTestOrderManager.PlotGraph(graphDateList, graphDataList)
    
    
if __name__ == '__main__':
    test = GapUpDownOpening()
    test()
        