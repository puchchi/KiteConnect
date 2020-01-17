import MySQLdb
from InitToken import TokenManager
from AnnualisedVolatility import AnnualisedVolatility
from Utility import *
import logging

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
        logging.info("Database manager starting...")
        try:
            self.db = MySQLdb.connect(DATABASE_HOST, DATABASE_USERNAME,
				            DATABASE_PASSWORD, DATABASE_NAME, charset="utf8", use_unicode=True)
            #self.cursor = self.db.cursor()
        except Exception as e:
            self.DumpExceptionInfo(e, "InitialiseDatabaseMgr")

        logging.info("Database manager complete...")

    def GetToDoTaskList(self, instrumentToken):
        try:
            SQL = ''' SELECT * from %s where instrumentToken=%s''' %(TODO_TABLENAME, instrumentToken)
            cursor = self.db.cursor()
            cursor.execute(SQL)
            data = cursor.fetchall()
            #cursor.close()
            return [True, data]
        except Exception as e:
            self.DumpExceptionInfo(e, "GetToDoTaskList")
        #finally:
            #cursor.close()
            return [False, []]

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
        
        cursor = self.db.cursor()
        try:
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
            (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, 0, price.__format__('.2f'))
            cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "CreateOneSDLevelsAndSetupInitialTask")
            
        #Inserting positive levels
        for i in range(fibUpperLevels.__len__()):
            try:
                SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (i+1), fibUpperLevels[i].__format__('.2f'))
                cursor.execute(SQL)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                self.DumpExceptionInfo(e, "CreateOneSDLevelsAndSetupInitialTask")

        #Inserting negative levels
        for i in range(fibLowerLevels.__len__()):
            try:
                SQL = """ INSERT INTO %s (InstrumentToken, Symbol, LevelType, LevelPrice) VALUES
                (%s, '%s', %s, %s)""" %(LEVELS_TABLENAME, instrumentToken, tradingSymbol, (-1)*(i+1), fibLowerLevels[i].__format__('.2f'))
                cursor.execute(SQL)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                self.DumpExceptionInfo(e, "CreateOneSDLevelsAndSetupInitialTask")

        print "Complete!!!Levels table population for symbol: " + tradingSymbol 
        #cursor.close()

        # Now setting up first buy & sell order
        self.SetupInitialTask(instrumentToken, fibLowerLevels, fibUpperLevels, price)

    def SetupInitialTask(self, instrumentToken, fibLowerLevels, fibUpperLevels, price):
        tradingSymbol = INDEX_FUTURE_DATA[instrumentToken]['tradingsymbol']
        print "Start!!!Todo table population(buy n sell) for symbol: " + tradingSymbol 
        logging.info("Start!!!Todo table population(buy n sell) for symbol: " + tradingSymbol)

        buyLevelType = 2
        buyValues = "(%s, '%s', %s, %s, %s, %s, '%s', '%s')" %(instrumentToken, tradingSymbol, buyLevelType, fibUpperLevels[buyLevelType-2]*(1+PRICE_PADDING), fibUpperLevels[buyLevelType-1], price, TASK_TYPE_ENUM[0], LEVEL_CROSS_TYPE_ENUM[0])

        sellLevelType = -2
        sellValues = "(%s, '%s', %s, %s, %s, %s, '%s', '%s')"  %(instrumentToken, tradingSymbol, sellLevelType, fibLowerLevels[abs(sellLevelType)-2]*(1-PRICE_PADDING), fibLowerLevels[abs(sellLevelType)-1], price, TASK_TYPE_ENUM[1], LEVEL_CROSS_TYPE_ENUM[1])
        # setting buy & sell order
        try:
            cursor = self.db.cursor()
            levelType = 2       # Level type shows level of target price in DB
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, TPLevelType, LevelPrice, TargetPrice, StopLoss, TaskType, LevelCrossType)
            VALUES %s, %s""" %(TODO_TABLENAME, buyValues, sellValues)
            cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "SetupInitialTask")

        #cursor.close()
        print "Complete!!!Todo table population(buy n sell) for symbol: " + tradingSymbol 

    def DeleteToDoTask(self, task):
        # todo table index [0:InstrumentToken, 1:symbol, 2:TPLevelType, 3:LevelPrice, 4:TP, 5:SL, 6:TaskType, 7:LevelCrossType, 8:OrderNo(Null)
        try:
            cursor = self.db.cursor()
            logging.info("Task deletion: "+ str(task))
            SQL = """delete from %s where instrumenttoken=%s and tasktype='%s' and levelcrosstype='%s'""" %(TODO_TABLENAME, task[0], task[6], task[7])
            noRowAffected = cursor.execute(SQL)
            self.db.commit()
            cursor.close()
            return noRowAffected
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "DeleteToDoTask")
        #finally:
            #cursor.close()

            return 0

    def GetNextLevel(self, instrumentToken, levelType):
        nextLevelType = levelType + 1
        if levelType < 0:
            nextLevelType = levelType - 1
        try:
            cursor = self.db.cursor()
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s """ %(LEVELS_TABLENAME, instrumentToken, nextLevelType)
            cursor.execute(SQL)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            self.DumpExceptionInfo(e, "GetNextLevel")
        #finally:
            #cursor.close()
            return []

    def GetCurrentLevel(self, instrumentToken, levelType):

        try:
            cursor = self.db.cursor()
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s""" %(LEVELS_TABLENAME, instrumentToken, levelType)
            cursor.execute(SQL)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            self.DumpExceptionInfo(e, "GetCurrentLevel")
        #finally:
            #cursor.close()
            return []

    def GetPrevLevel(self, instrumentToken, levelType):
        prevLevelType = levelType - 1
        if levelType < 0:
            prevLevelType = levelType + 1
        try:
            cursor = self.db.cursor()
            SQL = """SELECT levelType, LevelPrice from %s where InstrumentToken=%s and levelType=%s""" %(LEVELS_TABLENAME, instrumentToken, prevLevelType)
            cursor.execute(SQL)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            self.DumpExceptionInfo(e, "GetPrevLevel")
        #finally:
            #cursor.close()
            return []

    def CreateNewTask(self, instrumentToken, symbol, TPLevelType, levelPrice, tp, sl, taskType, levelCrossType, orderID):
        try:
            cursor = self.db.cursor()
            SQL = """ INSERT INTO %s (InstrumentToken, Symbol, TPLevelType, LevelPrice, TargetPrice, StopLoss, TaskType, 
            LevelCrossType, OrderID) VALUES (%s, '%s', %s, %s, %s, %s, '%s', '%s', %s)
            """ %(TODO_TABLENAME, instrumentToken, symbol, TPLevelType, levelPrice, tp, sl, taskType, levelCrossType, orderID)
            cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "CreateNewTask")
        #finally:
            #cursor.close()

    def CreateNewGapOpenTask(self, symbol, openPrice, tasktype):
        try:
            cursor = self.db.cursor()
            SQL = """ INSERT INTO %s (Symbol, OpenPrice, TaskType, Status) VALUES ('%s', %s, '%s', '%s')
            """ %(GAP_OPEN_TABLENAME, symbol, openPrice, tasktype, 'open')
            cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "CreateNewGapOpenTask")

    def GetOpenGapOpenTask(self):
        try:
            cursor = self.db.cursor()
            SQL = """SELECT Symbol, OpenPrice, TaskType from %s where Status='%s' 
            """ %(GAP_OPEN_TABLENAME, 'open')
            cursor.execute(SQL)
            data = cursor.fetchall()
            cursor.close()
            return data
        except Exception as e:
            self.DumpExceptionInfo(e, "GetPrevLevel")
        #finally:
            #cursor.close()
            return []

    def MarkGapOpenTaskDone(self, symbol):
        try:
            cursor = self.db.cursor()
            SQL = """ UPDATE %s SET status='%s' WHERE symbol='%s'
            """ %(GAP_OPEN_TABLENAME, 'done', symbol)
            cursor.execute(SQL)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.DumpExceptionInfo(e, "MarkGapOpenTaskDone")

    def DumpExceptionInfo(self, e, funcName):
        logging.error("Error in DatabaseManager::" + funcName, exc_info=True)
        print e
        print "Error in DatabaseManager::" + funcName

        try: 
            if str(e).find("OperationalError") != -1 or str(e).find("2006") != -1:
                print "Trying to reconnect database..."
                logging.info("Trying to reconnect database...")
                self.InitialiseDatabaseMgr()
        except Exception as e:
            print e