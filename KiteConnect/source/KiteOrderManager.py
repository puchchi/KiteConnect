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

        print "Kite order manager statring..."
        self.InitialiseKite()
        print "Kite order manager complete..."
        
        
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

    def BuyOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity):
        if ORDER_TYPE =='BO':
            return self.BuyBracketOrder(symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity)
        elif ORDER_TYPE == 'MIS':
            return self.BuyMISOrder(symbol, tradePrice, targetPoint, stoplossPoint, quantity)

    def SellOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity):
        if ORDER_TYPE =='BO':
            return self.SellBracketOrder(symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity)
        elif ORDER_TYPE == 'MIS':
            return self.SellMISOrder(symbol, tradePrice, targetPoint, stoplossPoint, quantity)

    def BuyBracketOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity):
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
        return orderNo

    def BuyMISOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, quantity):
        orderNo = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET,
                #price=tradePrice,
                validity=None,
                disclosed_quantity=None,
                trigger_price=None,
                #squareoff=targetPoint,
                #stoploss=stoplossPoint,
                trailing_stoploss=None,
                tag=None)

        print "Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo)
        logging.info("Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo))
        return orderNo

    def SellBracketOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, trailingSL, quantity):
        
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
        return orderNo

    def SellMISOrder(self, symbol, tradePrice, targetPoint, stoplossPoint, quantity):
        orderNo = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET,
                #price=tradePrice,
                validity=None,
                disclosed_quantity=None,
                trigger_price=None,
                #squareoff=targetPoint,
                #stoploss=stoplossPoint,
                trailing_stoploss=None,
                tag=None)

        print "Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo)
        logging.info("Order for symol: "+ symbol + " for quantity " + str(quantity) + " placed at price " + str(tradePrice) + " .Order no is:" + str(orderNo))
        return orderNo

    def GetOrderHistory(self, orderNo):
        orderHistory = self.kite.order_history(orderNo)
        return orderHistory

    def GetOrders(self):
        return self.kite.orders()

    def ModifyBOTpOrder(self, orderId, price):
        self.kite.modify_order(variety='bo', order_id=orderId, price=price)

    def ModifyBOSlOrder(self, orderId, triggerPrice):
        self.kite.modify_order(variety='bo', order_id=orderId, trigger_price=triggerPrice)
