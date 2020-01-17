import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
sys.path.append( path.dirname( path.dirname( path.dirname(path.abspath(__file__)) ) ) )

import MySQLdb
from Utility import *

class kCommand:

    def __init__(self, *args):
        try:
            self.db = MySQLdb.connect(DATABASE_HOST, DATABASE_USERNAME,
				            DATABASE_PASSWORD, DATABASE_NAME, charset="utf8", use_unicode=True)
            # Cursor will used in executing SQL query
            self.cursor = self.db.cursor()
        except Exception as e:
            self.DumpExceptionInfo(e, "__init__")


    def do(self):
        levelTableName = LEVELS_TABLENAME

        try:
            dropTableSQL = """ DROP TABLE %s;""" %(levelTableName)
            self.cursor.execute(dropTableSQL)
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

        try:
            SQL = """ CREATE TABLE %s (InstrumentToken INT NOT NULL, Symbol VARCHAR(20), LevelType INT NOT NULL, 
                    LevelPrice FLOAT NOT NULL, PRIMARY KEY (InstrumentToken, LevelType)); """ % (levelTableName)
            self.cursor.execute(SQL)
            print "Complete!!! Levels table"
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

        todoTableName = TODO_TABLENAME
        try:
            dropTableSQL = """ DROP TABLE %s;""" %(todoTableName)
            self.cursor.execute(dropTableSQL)
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

        try:
            SQL = """ CREATE TABLE %s (InstrumentToken INT NOT NULL, Symbol VARCHAR(20), TPLevelType INT NOT NULL, 
                    LevelPrice FLOAT NOT NULL, TargetPrice FLOAT NOT NULL, StopLoss FLOAT NOT NULL, TaskType VARCHAR(20),
                   LevelCrossType VARCHAR(20), OrderID VARCHAR(30), PRIMARY KEY (InstrumentToken, TaskType, LevelCrossType)); """ % (todoTableName)
            self.cursor.execute(SQL)
            print "Complete!!! Todo table"
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

        gapOpenTableName = GAP_OPEN_TABLENAME
        try:
            dropTableSQL = """ DROP TABLE %s;""" %(gapOpenTableName)
            self.cursor.execute(dropTableSQL)
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

        try:
            SQL = """ CREATE TABLE %s (Symbol VARCHAR(30), OpenPrice FLOAT NOT NULL, 
                    TaskType VARCHAR(2), Status VARCHAR(10), PRIMARY KEY (Symbol)); """ % (gapOpenTableName)
            self.cursor.execute(SQL)
            print "Complete!!! Gap open table"
        except Exception as e:
            self.DumpExceptionInfo(e, "do")

    def get_name(self):
        return "Cleaning & creating DB table Command"

    def DumpExceptionInfo(self, e, funcName):
        logging.error("Error in CleanNCreateDBTables::" + funcName, exc_info=True)
        print e
        print "Error in CleanNCreateDBTables::" + funcName