from kiteconnect import KiteTicker
from kiteconnect import KiteConnect

from InitToken import TokenManager
import Ticker, InstrumentListGenerator


if __name__=='__main__':

    ### Don't run first lintrument gerator lines, they are very time comsuming
    inst = InstrumentListGenerator.InstrumentListGenerator()
    inst.CreateNSE500ToZerodhaInstrumentList()

    # Initiating token manger
    TokenManager()
    
    Ticker.StartTicker()

    # Infinite loop
    while(1):
        None

