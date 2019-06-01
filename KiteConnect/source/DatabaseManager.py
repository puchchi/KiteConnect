import MySQLdb
from InitToken import TokenManager
from AnnualisedVolatility import AnnualisedVolatility
from Utility import *

class DatabaseManager():
    __instance = None

    @staticmethod
    def GetInstance():
        ''' Static access method'''
        if DatabaseManager.__instance == None:
            DatabaseManager()
        return DatabaseManager.__instance
    
    def __init__(self):
        if DatabaseManager.__instance != None:
            raise Exception ("DatabaseManager!This class is singleton!")
        else:
            DatabaseManager.__instance = self

        self.InitialiseDatabaseMgr()
        
        
    def InitialiseDatabaseMgr(self):
        try:
            self.db = MySQLdb.connect(DATABASE_HOST, DATABASE_USERNAME,
				            DATABASE_PASSWORD, DATABASE_NAME, charset="utf8", use_unicode=True)
            # Cursor will used in executing SQL query
            self.cursor = self.db.cursor()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::InitialiseDatabaseMgr"

    def GetToDoTaskList(self, instrumentToken):
        try:
            SQL = ''' SELECT * from %s where instrumentToken=%s''' %(TODO_TABLENAME, instrumentToken)
            response = self.cursor.execute(SQL)
            return response
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::InitialiseDatabaseMgr"
            return []

    def CreateOneSDLevels(self, instrumentToken, price):
        annualisedVolatility = AnnualisedVolatility(INDEX_FUTURE_DATA[instrumentToken]['underlyingsymbol'], INDEX_FUTURE_DATA[instrumentToken]['expiry'])
        annualVolatility = annualisedVolatility.GetAnnualisedVolatility()
        print "Annualised volatility: " + str(annualVolatility)
        
        # 1 sd formula = annual volatility * price * sqrt(1)/sqrt(365)      // Here 1 is no of days
        _1SD = annualVolatility * price / 19.105 / 100
        fibLevels = [_1SD * i for i in FIB_LEVELS]
        fibUpperLevels = [price + i for i in fibLevels]
        fibLowerLevels = [price - i for i in fibLevels]

        tradingSymbol = INDEX_FUTURE_DATA[instrumentToken]['tradingsymbol']
        # inserting price at 0th index, so that it can used as sl        
        try:
            SQL = ''' INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
            (%s, %s, %s, %s)''' %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, 0, price.__format__('.2f'))
            response = self.cursor.execute(SQL)
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevels"

        #Inserting positive levels
        for i in range(fibUpperLevels.__len__()):
            try:
                SQL = ''' INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, %s, %s, %s)''' %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (i+1), fibUpperLevels[i].__format__('.2f'))
                self.cursor.execute(SQL)
            except Exception as e:
                print e
                print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevels"

        #Inserting negative levels
        for i in range(fibLowerLevels.__len__()):
            try:
                SQL = ''' INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, %s, %s, %s)''' %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (-1)*(i+1), fibLowerLevels[i].__format__('.2f'))
                self.cursor.execute(SQL)
            except Exception as e:
                print e
                print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevels"