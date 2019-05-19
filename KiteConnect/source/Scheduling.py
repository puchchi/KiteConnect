import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
sys.path.append( path.dirname( path.abspath(__file__) ) )

import Ticker, TradableStockCal, CleanUp
from Utility import *

# Date format from here: 01-Jan-2018

SCHEDULED_TASK=(
    #(Module, expected arugument, ((from(HHMM), to(HHMM), timedelta(in minute)) or (when(HHMM))))
    # argument (symbol/list of symbol, [args], type, tableName)

     # Start ticker, every day once
    (CleanUp, [], ["0910"], ),         #0900
    (Ticker, [], ["0915"], ),             #0915
    (TradableStockCal, [], ["0918"], ),     #0918
    )

