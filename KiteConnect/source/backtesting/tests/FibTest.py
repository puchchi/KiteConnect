from KiteConnect.source.backtesting import BackTestData


# DEFS
ROOT_STOCK_LIST = ['NIFTY19JULFUT']
SUB_STOCK_LIST = {'NIFTY19JULFUT':['NIFTY19JUL12000CE', 'NIFTY19JUL11900PE']}

class FibTest(BackTestData.BackTest):
    
    def __init__(self):
        pass
    
    def __call__(self):
        rootStockData = self.GetRootStockData()

    def GetRootStockData(self):
        pass