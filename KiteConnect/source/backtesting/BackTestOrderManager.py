from os import path
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
        
    def GetInitialReport(self):
        tempMsgStr = ''
        if (self.IsBoughtContract()):
            tempMsgStr += '\tBought ' + self.fStockName + ', Lot size(' + self.fLotSize + ') :' + str(self.fQuantity/self.fLotSize) + 'lots, at price: ' + str(self.fBuyingPrice) +'\n'
            
        elif (self.IsSoldContract()):
            tempMsgStr += '\tSold ' + self.fStockName + ', Lot size(' + self.fLotSize + ') :' + str(self.fQuantity/self.fLotSize) + 'lots, at price: ' + str(self.fSellingPrice) + '\n'
            
    def ClosePositionAt(self, date):
        tempMsgStr = ''
        if (self.IsBoughtContract()):
            self.fSellingPrice = BackTestData.GetOpenPriceAtTime(date, self.fTickData)
            tempMsgStr += '\tSold(closed) ' + self.fStockName + ', Lot size(' + self.fLotSize + ') :' + str(self.fQuantity/self.fLotSize) + 'lots, at price: ' + str(self.fSellingPrice) +'\n'
            
        elif (self.IsSoldContract()):
            self.fBuyingPrice = BackTestData.GetOpenPriceAtTime(date, self.fTickData)
            tempMsgStr += '\tBought(closed) ' + self.fStockName + ', Lot size(' + self.fLotSize + ') :' + str(self.fQuantity/self.fLotSize) + 'lots, at price: ' + str(self.fBuyingPrice) +'\n'
            
        return tempMsgStr
    
    def IsBoughtContract(self):
        return self.fBuyingPrice != INVALID_PRICE
    
    def IsSoldContract(self):
        return self.fSellingPrice != INVALID_PRICE

    def GetProfitOrLoss(self):
        return self.fBuyingPrice - self.fSellingPrice
    

class OrderManager():
    
    def __init__(self, reportName, rootStockName):
        self.fProfitLostDateWise = []
        self.fTotalProfitOrLoss = 0
        
        self.fReportName = reportName
        self.fRootStockName = rootStockName
        self.fReportFileName = path.join(REPORT_DIR, reportName + '_' + rootStockName)
        
        # Creating report file
        with open(self.fReportFileName, 'w') as fd: 
            pass
        
    def OpenedNewPosition(self, positionDetail, date):
        with open(self.fReportFileName, 'a') as fd: 
            messageString = "\n\n***************************************************"
            messageString += "Opened a trade at " + date.strftime(REPORT_TIME_FORMAT) + '\n'
            for stock in positionDetail:
                messageString += stock.GetInitialReport()
            fd.write(messageString)
            
            print messageString
            
    def CloseTrade(self, positionalDetail, date):
        messageString = "\tClosing a trade at " + date.strftime(REPORT_TIME_FORMAT) + '\n'
        positionalProfitOrLoss = 0
        for stock in positionalDetail:
            messageString += stock.ClosePositionAt(date)
            profitOrLoss = stock.GetProfitOrLoss()
            positionalProfitOrLoss += profitOrLoss
            
        self.fProfitLostDateWise.append[[date, positionalProfitOrLoss]]
        self.fTotalProfitOrLoss += positionalProfitOrLoss
        
        messageString += '\n Positional profit/loss: ' + str(positionalProfitOrLoss)
        with open(self.fReportFileName, 'a') as fd: 
            fd.write(messageString)
            
        print messageString
            
    def DumpFullProfitOrLoss(self):
        with open(self.fReportFileName, 'a') as fd: 
            messageString = "\n\n***************************************************"
            messageString += 'Total profit/loss: ' + str(self.fTotalProfitOrLoss)
            fd.write(messageString)
            
            print messageString
            
            