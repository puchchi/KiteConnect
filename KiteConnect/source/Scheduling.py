import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
sys.path.append( path.dirname( path.abspath(__file__) ) )

import Ticker, TradableStockCal, CleanUp, CleanNCreateDBTables
import Utility
from datetime import datetime

# Date format from here: 01-Jan-2018

SCHEDULED_TASK=(
    #(Module, expected arugument, ((from(HHMM), to(HHMM), timedelta(in minute)) or (when(HHMM))))
    # argument (symbol/list of symbol, [args], type, tableName)

     # Start ticker, every day once
    (CleanUp, [], ["0910"], ),         #0900
    (CleanNCreateDBTables, [], ["1534"], ),
    (Ticker, [], [datetime.strptime(str(Utility.TICKERSTART), '%H%M%S').strftime('%H%M')], ),             #0915
 #   (TradableStockCal, [], [datetime.strptime(str(Utility.TRADABLESTOCKSTART), '%H%M%S').strftime('%H%M')], ),     #0918
    )

