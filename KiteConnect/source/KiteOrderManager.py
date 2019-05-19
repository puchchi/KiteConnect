from kiteconnect import KiteConnect
from InitToken import TokenManager
from Utility import *

class KiteOrderManager():
    __instance = None

    @staticmethod
    def GetInstance():
        ''' Static access method'''
        if KiteOrderManager.__instance == None:
            KiteOrderManager()
        return KiteOrderManager.__instance
    
    def __init__(self):
        if KiteOrderManager.__instance != None:
            raise Exception ("KiteOrderManager!This class is singleton!")
        else:
            KiteOrderManager.__instance = self

        self.InitialiseKite()
        
        
    def InitialiseKite(self):
        tokenManager = TokenManager.GetInstance()
        apiKey = tokenManager.GetApiKey()
        accessToken = tokenManager.GetAccessToken()
        self.kite = KiteConnect(api_key = apiKey)
        self.kite.set_access_token(accessToken)

    def BuyOrder(self):
        print "Not implemented"

    def SellOrder(self):
        print "Not implemented"

    def BuyBracketOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, quantity):
        orderNo = self.kite.place_order(
                variety=self.kite.VARIETY_BO,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                product=self.kite.PRODUCT_BO,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=tradePrice,
                validity=None,
                disclosed_quantity=None,
                trigger_price=None,
                squareoff=targetPoint,
                stoploss=stoplossPoint,
                trailing_stoploss=None,
                tag=None)

        print "Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo)
        logging.info("Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo))

    def SellBracketOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, quantity):
        orderNo = self.kite.place_order(
                variety=self.kite.VARIETY_BO,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=self.kite.PRODUCT_BO,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=tradePrice,
                validity=None,
                disclosed_quantity=None,
                trigger_price=None,
                squareoff=targetPoint,
                stoploss=stoplossPoint,
                trailing_stoploss=None,
                tag=None)

        print "Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo)
        logging.info("Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo))
