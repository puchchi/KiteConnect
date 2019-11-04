from os import path
#from source.Utility import *
#from source.backtesting import BackTestData

from KiteConnect.source.Utility import *
from KiteConnect.source.backtesting import BackTestData

REPORT_DIR = path.dirname(path.dirname(path.abspath(__file__)))
REPORT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class OrderManagerStockStruct():
    
    def __init__(self, stockName, quantity, lotSize, tickData, buyingPrice=INVALID_PRICE, sellingPrice=INVALID_PRICE):
        self.fStockName = stockName
        self.fQuantity = quantity
        self.fLotSize = lotSize
        self.fTickData = tickData
        self.fBuyingPrice = buyingPrice
        self.fSellingPrice = sellingPrice
        self.fExersizedLotSize = 0
        if (self.fLotSize != 0):
            self.fExersizedLotSize = self.fQuantity / self.fLotSize
        
    def GetInitialReport(self):
        tempMsgStr = ''
        if (self.IsBoughtContract()):
            tempMsgStr += '\tBought ' + self.fStockName + ', Lot size(' + str(self.fLotSize) + ') :' + str(self.fExersizedLotSize) + 'lots, at price: ' + str(self.fBuyingPrice) +'\n'
            
        elif (self.IsSoldContract()):
            tempMsgStr += '\tSold ' + self.fStockName + ', Lot size(' + str(self.fLotSize) + ') :' + str(self.fExersizedLotSize) + 'lots, at price: ' + str(self.fSellingPrice) + '\n'
        return tempMsgStr

    def ClosePositionAt(self, date):
        tempMsgStr = ''
        if (self.IsBoughtContract()):
            self.fSellingPrice = BackTestData.GetOpenPriceAtTime(date, self.fTickData)
            tempMsgStr += '\tSold(closed) ' + self.fStockName + ', Lot size(' + str(self.fLotSize) + ') :' + str(self.fExersizedLotSize) + 'lots, at price: ' + str(self.fSellingPrice) +'\n'
            
        elif (self.IsSoldContract()):
            self.fBuyingPrice = BackTestData.GetOpenPriceAtTime(date, self.fTickData)
            tempMsgStr += '\tBought(closed) ' + self.fStockName + ', Lot size(' + str(self.fLotSize) + ') :' + str(self.fExersizedLotSize) + 'lots, at price: ' + str(self.fBuyingPrice) +'\n'
            
        return tempMsgStr
    
    def IsBoughtContract(self):
        return self.fBuyingPrice != INVALID_PRICE
    
    def IsSoldContract(self):
        return self.fSellingPrice != INVALID_PRICE

    def GetProfitOrLoss(self):
        return self.fSellingPrice - self.fBuyingPrice
    

class OrderManager():
    
    def __init__(self, reportName, rootStockName):
        self.fProfitLostDateWise = []
        self.fTotalProfitOrLoss = 0
        
        self.fReportName = reportName
        self.fRootStockName = rootStockName
        self.fReportFileName = path.join(REPORT_DIR, reportName + '_' + rootStockName)
        self.fMissedTrigger = 0
        self.fPositiveTrigger = 0
        self.fNegativeTrigger = 0
        
        # Creating report file
        with open(self.fReportFileName, 'w') as fd: 
            pass
        
    def OpenedNewPosition(self, positionDetail, date):
        with open(self.fReportFileName, 'a') as fd: 
            messageString = "\n\n***************************************************\n"
            messageString += "Opened a trade at " + date.strftime(REPORT_TIME_FORMAT) + '\n'
            for stock in positionDetail:
                messageString += str(stock.GetInitialReport())
            fd.write(messageString)
            
            print messageString
            
    def CloseTrade(self, positionalDetail, date):
        messageString = "\tClosing a trade at " + date.strftime(REPORT_TIME_FORMAT) + '\n'
        positionalProfitOrLoss = 0
        for stock in positionalDetail:
            messageString += stock.ClosePositionAt(date)
            profitOrLoss = stock.GetProfitOrLoss()
            positionalProfitOrLoss += profitOrLoss
            
        self.fProfitLostDateWise.append([date, positionalProfitOrLoss])
        self.fTotalProfitOrLoss += positionalProfitOrLoss
        
        if (positionalProfitOrLoss > 0):
            self.fPositiveTrigger += 1
        else:
            self.fNegativeTrigger += 1
            
        messageString += '\n Positional profit/loss: ' + str(positionalProfitOrLoss)
        messageString += '\n Interim total profit/los: ' + str(self.fTotalProfitOrLoss)
        with open(self.fReportFileName, 'a') as fd: 
            fd.write(messageString)
            
        print messageString
            
    def DumpFullProfitOrLoss(self):
        with open(self.fReportFileName, 'a') as fd: 
            messageString = "\n\n***************************************************\n"
            messageString += 'Total profit/loss: ' + str(self.fTotalProfitOrLoss)
            
            messageString += "\n\n***************************************************\n"
            totalTrigger = self.fPositiveTrigger + self.fNegativeTrigger + self.fMissedTrigger
            messageString += 'Total positive trigger: ' + str(self.fPositiveTrigger) + ", in percentage: " + str(self.fPositiveTrigger / totalTrigger * 100) + '\n'
            messageString += 'Total negative trigger: ' + str(self.fNegativeTrigger) + ", in percentage: " + str(self.fNegativeTrigger / totalTrigger * 100) + '\n'
            messageString += 'Total missed trigger: ' + str(self.fMissedTrigger) + ", in percentage: " + str(self.fMissedTrigger / totalTrigger * 100) + '\n'
            fd.write(messageString)
            
            print messageString
            
    def MissedTrigger(self, positionDetail, date):
        with open(self.fReportFileName, 'a') as fd: 
            messageString = "\n\n***************************************************\n"
            messageString += "Missed a trade at " + date.strftime(REPORT_TIME_FORMAT) + '\n'
            for stock in positionDetail:
                messageString += str(stock.GetInitialReport())
            fd.write(messageString)
            
            self.fMissedTrigger += 1
            print messageString
            
            
            
            