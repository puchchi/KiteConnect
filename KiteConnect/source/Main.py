from kiteconnect import KiteTicker
from kiteconnect import KiteConnect

from InitToken import TokenManager
import Ticker, InstrumentListGenerator
import time, datetime, thread
from datetime import datetime as dt
import Scheduling, Utility

class Main:

    def __init__(self):
        self.taskToTimeList = {}                        # To store when next time given task will execute
        self.taskDataList = {}                          # To store data correspoding to a task
        self.eligibleProcessList = []
        self.coldStart = True                           # we will send coldstart to everyone
    
    def __call__(self):
        self.CreateTaskList()

        while 1:
            now = dt.now().strftime("%d-%m-%Y %H:%M") 
            print "Checking at "+ now

            try:
                self.GetEligibleProcess()
                self.ScheduleNextExecutionTime()
                self.RunEligibleProcess()
                self.Log("Going in sleep!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                self.CleanUp()
                self.coldStart = False
            except Exception as e:
                print e
                print "Exception in __call__ main.py"

            time.sleep(5)

    def CreateTaskList(self):
        tasks = Scheduling.SCHEDULED_TASK
        now = dt.now().strftime("%Y%m%d%H%M")            # '201804290801'
        nowWithoutTime = now[0:-4]                       # '20180429'

        counter = 1
        for task in tasks:
            runTimeList = task[2]
            lowerBound = 0
            upperBound = 0
            gap = 0

            if  runTimeList.__len__()==3:               # (from(HHMM), to(HHMM), gap(in second)
                tempStr = nowWithoutTime + runTimeList[0]
                lowerBound = int(tempStr)

                tempStr = nowWithoutTime + runTimeList[1]
                upperBound = int(tempStr)

                gap = runTimeList[2]
            elif runTimeList.__len__()==1:              # when(HHMM)
                tempStr = nowWithoutTime + runTimeList[0]
                lowerBound = int(tempStr)

                upperBound = 0
                gap = 0

            if (task[1].__len__()>0 and type(task[1][0])==list):
                for i in range (task[1][0].__len__()):
                    tempTaskList = task[1][1:]
                    tempTaskList.insert(0, task[1][0][i])
                    self.taskDataList.update({counter :[task[0], tempTaskList, lowerBound, upperBound, gap]})
                    self.taskToTimeList.update({counter: lowerBound})
                    counter+=1
            else:
                self.taskDataList.update({counter :[task[0], task[1], lowerBound, upperBound, gap]})
                self.taskToTimeList.update({counter: lowerBound})
                counter+=1
            


    def GetEligibleProcess(self):
        now = dt.now().strftime("%Y%m%d%H%M") 
        nowInt = int(now)

        for iter in self.taskToTimeList.iteritems():
            if iter[1] <= nowInt:
                self.eligibleProcessList.append(iter[0])


    def ScheduleNextExecutionTime(self):
        now = dt.now()

        for iter in self.eligibleProcessList:
            oldScheduledTime = self.taskToTimeList[iter]
            oldScheduledTimeDT = dt.strptime(str(oldScheduledTime), "%Y%m%d%H%M")
            newTimeDT = oldScheduledTimeDT

            lowerBound = self.taskDataList[iter][2]
            upperBound = self.taskDataList[iter][3]
            gap = self.taskDataList[iter][4]

            lowerBoundDT = dt.strptime(str(lowerBound), "%Y%m%d%H%M")

            if (upperBound != 0 and gap != 0):
                while (newTimeDT < now):
                    newTimeDT += datetime.timedelta(minutes=gap)

                upperBoundDT = dt.strptime(str(upperBound), "%Y%m%d%H%M")
                # Increase day by one
                if (newTimeDT > upperBoundDT):
                    lowerBoundDT = self.GetNextDay(lowerBoundDT)
                    upperBoundDT = self.GetNextDay(upperBoundDT)
           
                    lowerBound = int(lowerBoundDT.strftime("%Y%m%d%H%M"))
                    upperBound = int(upperBoundDT.strftime("%Y%m%d%H%M"))
                     # Now we will update value in dict
                    self.taskDataList[iter][2] = lowerBound
                    self.taskDataList[iter][3] = upperBound
                    newTimeDT = lowerBoundDT

                newTime = int(newTimeDT.strftime("%Y%m%d%H%M"))
                self.taskToTimeList[iter] = newTime

            elif (upperBound == 0 and gap == 0):
                lowerBoundDT = self.GetNextDay(lowerBoundDT)
           
                lowerBound = int(lowerBoundDT.strftime("%Y%m%d%H%M"))
                    # Now we will update value in dict
                self.taskDataList[iter][2] = lowerBound

                self.taskToTimeList[iter] = lowerBound

    def GetNextDay(self, time):
        newTime = time + datetime.timedelta(days=1)

        #while (Utility.IsWeekday(newTime) != True):
        #    newTime = newTime + datetime.timedelta(days=1)
        return newTime


    def RunEligibleProcess(self):
        for iter in self.eligibleProcessList:
            try:
                task = self.taskDataList[iter][0]
                args = self.taskDataList[iter][1] + [self.coldStart]
                cmd = task.kCommand(args)
                #thread.start_new_thread(cmd.do(), [])
                logInfo = cmd.get_name()
                if (args.__len__()>1):
                    logInfo = logInfo + ": " + args[0]
                self.Log(logInfo)
                
                now = datetime.datetime.now()
                cmd.do()
                after = datetime.datetime.now()
                print "LAST JOB EXECUTION TIME: " + str(after-now)
                print "==========================================\n"
            except Exception as e:
                print e

    def CleanUp(self):
        self.eligibleProcessList = []

    def Log(self, logInfo):
        # do something
        print str(datetime.datetime.now()) + ":" + logInfo

if __name__=="__main__":

    ### Don't run first lintrument gerator lines, they are very time comsuming
    #inst = InstrumentListGenerator.InstrumentListGenerator()
    #inst.CreateNSE500ToZerodhaInstrumentList()

    main = Main()
    main()


