import os
from Utility import *
from multiprocessing import Process, Queue
from datetime import datetime

def CleanUp():
    
    now = int(datetime.now().strftime("%H%M%S"))
    # Dont cleanup after 9:15am
    if now >= TICKERSTART:
        return

    print "Clean up starts..."
    logging.info("Clean up starts...")
    DeleteAllFiles(SHORTLISTED_STOCK_LOCATION)
    DeleteAllFiles(TRADABLE_STOCK_LOCATION)

    print "Clean up ends..."
    logging.info("Clean up ends...")

def DeleteAllFiles(dir):
    files = os.listdir(dir)
    for file in files:
        try:
            os.remove(os.path.join(dir, file))
        except Exception as e:
            print "Exception in cleanup"
            logging.error("Exception ocurred!", exc_info=True)

class kCommand:

    def __init__(self, *args):
        self.args = args

    def run_job(self, queue, args):
        try:
            CleanUp()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    def do(self):

        queue = Queue()
        process = Process(target=self.run_job, args=(queue, self.args))
        process.start()
        result = queue.get()
        process.join()

        if result is not None:
            raise result

    def get_name(self):
        return "Clean up command"

