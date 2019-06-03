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

        print "Database manager starting..."
        self.InitialiseDatabaseMgr()
        print "Database manager complete..."
        
        
    def InitialiseDatabaseMgr(self):
        try:
            self.db = MySQLdb.connect(DATABASE_HOST, DATABASE_USERNAME,
				            DATABASE_PASSWORD, DATABASE_NAME, charset="utf8", use_unicode=True)
            self.cursor = self.db.cursor()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::InitialiseDatabaseMgr"

    def GetToDoTaskList(self, instrumentToken):
        try:
            SQL = ''' SELECT * from %s where instrumentToken=%s''' %(TODO_TABLENAME, instrumentToken)

            self.cursor.execute(SQL)
            return self.cursor.fetchall()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::InitialiseDatabaseMgr"
            return []

    def CreateOneSDLevelsAndSetupInitialTask(self, instrumentToken, price):

        annualisedVolatility = AnnualisedVolatility(INDEX_FUTURE_DATA[instrumentToken]['underlyingsymbol'], INDEX_FUTURE_DATA[instrumentToken]['expiry'])
        annualVolatility = annualisedVolatility.GetAnnualisedVolatility()
        print "Annualised volatility: " + str(annualVolatility)
        
        # 1 sd formula = annual volatility * price * sqrt(1)/sqrt(365)      // Here 1 is no of days
        _1SD = annualVolatility * price / 19.105 / 100
        fibLevels = [_1SD * i for i in FIB_LEVELS]
        fibUpperLevels = [price + i for i in fibLevels]
        fibLowerLevels = [price - i for i in fibLevels]
        
        tradingSymbol = INDEX_FUTURE_DATA[instrumentToken]['tradingsymbol']
        print "Start!!!Levels table population for symbol: " + tradingSymbol 
        # inserting price at 0th index, so that it can used as sl  
        
        try:
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
            (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, 0, price.__format__('.2f'))
            self.cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print e
            print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevelsAndSetupInitialTask"

        #Inserting positive levels
        for i in range(fibUpperLevels.__len__()):
            try:
                SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (i+1), fibUpperLevels[i].__format__('.2f'))
                self.cursor.execute(SQL)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print e
                print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevelsAndSetupInitialTask"

        #Inserting negative levels
        for i in range(fibLowerLevels.__len__()):
            try:
                SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (-1)*(i+1), fibLowerLevels[i].__format__('.2f'))
                self.cursor.execute(SQL)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print e
                print "Error in connecting Mysql db in DatabaseManager::CreateOneSDLevelsAndSetupInitialTask"

        print "Complete!!!Levels table population for symbol: " + tradingSymbol 

        # Now setting up first buy & sell order
        self.SetupInitialTask(instrumentToken, fibLowerLevels, fibUpperLevels, price)

    def SetupInitialTask(self, instrumentToken, fibLowerLevels, fibUpperLevels, price):
        tradingSymbol = INDEX_FUTURE_DATA[instrumentToken]['tradingsymbol']
        print "Start!!!Todo table population(buy n sell) for symbol: " + tradingSymbol 

        # setting buy order
        try:
            levelType = 2       # Level type shows level of target price in DB
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, TPLevelType, LevelPrice, TargetPrice, StopLoss, TaskType, LevelCrossType)
            VALUES (%s, '%s', %s, %s, %s, %s, '%s', '%s')""" %(TODO_TABLENAME, instrumentToken, tradingSymbol, levelType, fibUpperLevels[levelType-2]*(1+PRICE_PADDING), fibUpperLevels[levelType-1], price, TASK_TYPE_ENUM[0], LEVEL_CROSS_TYPE_ENUM[0])
            self.cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print e
            print "Error in connecting Mysql db in DatabaseManager::SetupInitialTask"

        # setting sell order
        try:
            levelType = -2       # Level type shows level of target price in DB
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, TPLevelType, LevelPrice, TargetPrice, StopLoss, TaskType, LevelCrossType)
            VALUES (%s, '%s', %s, %s, %s, %s, '%s', '%s')""" %(TODO_TABLENAME, instrumentToken, tradingSymbol, levelType, fibLowerLevels[abs(levelType)-2]*(1-PRICE_PADDING), fibLowerLevels[abs(levelType)-1], price, TASK_TYPE_ENUM[1], LEVEL_CROSS_TYPE_ENUM[1])
            self.cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print e
            print "Error in connecting Mysql db in DatabaseManager::SetupInitialTask"

        print "Complete!!!Todo table population(buy n sell) for symbol: " + tradingSymbol 

    def DeleteToDoTask(self, task):
        # todo table index [0:InstrumentToken, 1:symbol, 2:TPLevelType, 3:LevelPrice, 4:TP, 5:SL, 6:TaskType, 7:LevelCrossType, 8:OrderNo(Null)
        try:
            SQL = """delete from %s where instrumenttoken=%s and tasktype='%s' and levelcrosstype='%s'""" %(TODO_TABLENAME, task[0], task[6], task[7])
            noRowAffected = self.cursor.execute(SQL)
            self.db.commit()
            return noRowAffected
        except Exception as e:
            self.db.rollback()
            print e
            print "Error in connecting Mysql db in DatabaseManager::DeleteToDoTask"

        return 0

    def GetNextLevel(self, instrumentToken, levelType):
        nextLevelType = levelType + 1
        if levelType < 0:
            nextLevelType = levelType - 1
        try:
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s """ %(LEVELS_TABLENAME, instrumentToken, nextLevelType)
            self.cursor.execute(SQL)
            return self.cursor.fetchall()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::GetNextLevel"
        return []

    def GetCurrentLevel(self, instrumentToken, levelType):

        try:
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s""" %(LEVELS_TABLENAME, instrumentToken, levelType)
            self.cursor.execute(SQL)
            return self.cursor.fetchall()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::GetCurrentLevel"
        return []

    def GetPrevLevel(self, instrumentToken, levelType):
        prevLevelType = levelType - 1
        if levelType < 0:
            prevLevelType = levelType + 1
        try:
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s""" %(LEVELS_TABLENAME, instrumentToken, prevLevelType)
            self.cursor.execute(SQL)
            return self.cursor.fetchall()
        except Exception as e:
            print e
            print "Error in connecting Mysql db in DatabaseManager::GetPrevLevel"
        return []

    def CreateNewTask(self, instrumentToken, symbol, TPLevelType, levelPrice, tp, sl, taskType, levelCrossType, orderID):
        try:
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, TPLevelType, LevelPrice, TargetPrice, StopLoss, TaskType, 
            LevelCrossType, OrderID) VALUES (%s, '%s', %s, %s, %s, %s, '%s', '%s', %s)
            """ %(TODO_TABLENAME, instrumentToken, symbol, TPLevelType, levelPrice, tp, sl, taskType, levelCrossType, orderID)
            self.cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print e
            print "Error in connecting Mysql db in DatabaseManager::CreateNewTask"