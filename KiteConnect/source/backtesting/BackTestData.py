from KiteConnect.source.KiteOrderManager import KiteOrderManager
import pandas as pd
from KiteConnect.source.Utility import *
from datetime import datetime

class BasicStock():
    
    def __init__(self, stockName, instrumentToken, fromDate, toDate, tpSlList, quantity, sellQuantityList):
        self.fStockName = stockName
        self.fInstrumentToken = instrumentToken
        self.fFromDate = fromDate
        self.fToDate = toDate
        self.fTpSlList = tpSlList             # 2D list to contain target price and respective stop loss (Optional)
        self.fQuantity = quantity     
        self.fSellQuantityList = sellQuantityList     # 2D list to contain target price and sell quantity pair
            
    def SetStockName(self, stockName):
        self.fStockName = stockName
        
    def SetInstrumentToken(self, instrumentToken):
        self.fInstrumentToken = instrumentToken
        
    def SetFromDate(self, fromDate):
        self.fFromDate = fromDate
        
    def SetToDate(self, toDate):
        self.fToDate = toDate
        
    def SetTpSlList(self, tpSlList):
        self.fTpSlList = tpSlList
        
    def SetQuantity(self, quantity):
        self.fQuantity = quantity
        
    def SetSellQuantityList(self, sellQuantityList):
        self.fSellQuantityList = sellQuantityList

class SubStock(BasicStock):
    
    def __init__(self, stockName, instrumentToken, fromDate, toDate, tpSlList, quantity, sellQuantityList, closeWithRootOrder):
        super().__init__(stockName, instrumentToken, fromDate, toDate, tpSlList, quantity, sellQuantityList)
        self.fCloseWithRootOrder = closeWithRootOrder        # Do we want to close this stock with it's root stock
        
    def SetCloseWithRootOrder(self, closeWithRootOrder):
        self.fCloseWithRootOrder = closeWithRootOrder 

class RootStock(BasicStock):
    
    def __init__(self, stockName, instrumentToken, fromDate, toDate, tpSlList, subStockList, quantity, sellQuantityList, buyTriggerPrice, sellTriggerPrice):
        super().__init__(stockName, instrumentToken, fromDate, toDate, tpSlList, quantity, sellQuantityList)
        self.fSubStockList = subStockList                # List to contain other stock object of current trade
        self.fBuyTriggerPrice = buyTriggerPrice
        self.fSellTriggerPrice = sellTriggerPrice
        
    def SetSubStockList(self, subStockList):
        self.fSubStockList = subStockList 
        
    def SetBuyTriggerPrice(self, buyTriggerPrice):
        self.fBuyTriggerPrice = buyTriggerPrice
        
    def SetSellTriggerPrice(self, sellTriggerPrice):
        self.fSellTriggerPrice = sellTriggerPrice
        
class BackTest():
    
    def __init__(self):
        self.fDesiredExchange = 'NSE'
        self.fZerodhaInstrumentDF = pd.read_csv(DATA_LOCATION + ZERODHA_INSTRUMENT_LIST_FILENAME)
        
    def GetHisoricalData(self, instruemenToken, fromData, toData, interval, continuous):
        kite = KiteOrderManager.GetInstance()
        return kite.GetHistoricalData(instruemenToken, fromData, toData, interval, continuous)
    
    def GetInstrumentTokenAndLotSize(self, symbol):
        for j in range(self.fZerodhaInstrumentDF["tradingsymbol"].__len__()):
            if symbol == self.fZerodhaInstrumentDF["tradingsymbol"][j] and self.fZerodhaInstrumentDF["exchange"][j] == self.fDesiredExchange:
                instrumentToken = self.fZerodhaInstrumentDF["instrument_token"]
                lotSize = self.fZerodhaInstrumentDF["lot_size"]
                return [instrumentToken, lotSize]
    
    
def GetOpenPriceAtTime(date, tickData):
    # We will try to find exact time in tick data,
    # if we couldn't find exact time, then we will find closest time 
    
    if (tickData.__len__() == 0):
        print ("No data found in BackTestData::GetOpenPriceAtTime!!!")
        return 
    
    lastTickIndex = 0
    for tick in tickData:
        if (date == tick['date']):
            return tick['open']
        
        if (date < tick['date']):
            if ( date - tickData[lastTickIndex]['date'] > tick['date'] - date):
                return tick['date']
            else:
                tickData[lastTickIndex]['open']
        lastTickIndex += 1
        
        
        