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
            print e
            print "Error in connecting Mysql db in CleanNCreateDBTables.py"


    def do(self):
        levelTableName = LEVELS_TABLENAME

        try:
            dropTableSQL = """ DROP TABLE %s;""" %(levelTableName)
            self.cursor.execute(dropTableSQL)
        except Exception as e:
            print "Error in dropping table Call function in CleanNCreateDBTables.py."
            print e

        try:
            SQL = """ CREATE TABLE %s (InstrumentToken INT NOT NULL, Symbol VARCHAR(20), LevelType INT NOT NULL, 
                    LevelPrice FLOAT NOT NULL, PRIMARY KEY (InstrumentToken, LevelType)); """ % (levelTableName)
            self.cursor.execute(SQL)
            print "Complete!!! Levels table"
        except Exception as e:
            print "Error in creating table Call function in CleanNCreateDBTables.py."
            print e

        todoTableName = TODO_TABLENAME
        try:
            dropTableSQL = """ DROP TABLE %s;""" %(todoTableName)
            self.cursor.execute(dropTableSQL)
        except Exception as e:
            print "Error in dropping table Call function in CleanNCreateDBTables.py."
            print e

        try:
            SQL = """ CREATE TABLE %s (InstrumentToken INT NOT NULL, Symbol VARCHAR(20), TPLevelType INT NOT NULL, 
                    LevelPrice FLOAT NOT NULL, TargetPrice FLOAT NOT NULL, StopLoss FLOAT NOT NULL, TaskType VARCHAR(20),
                   LevelCrossType VARCHAR(20), OrderID INT, PRIMARY KEY (InstrumentToken, TaskType)); """ % (todoTableName)
            self.cursor.execute(SQL)
            print "Complete!!! Todo table"
        except Exception as e:
            print "Error in creating table Call function in CleanNCreateDBTables.py."
            print e

    def get_name(self):
        return "Cleaning & creating DB table Command"
