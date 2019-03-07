#from process_tracer import ProcessTracer
import os
import sys
#import hashlib
import re
import getpass
import subprocess
import time
from datetime import datetime
import psutil
from threading import Thread
import socket
import logging

from db import StatsDB
import stats as Stats
from table import Table, Task
import log_processing as LogProcessing

class Statistics:
    procID = -1
    proc = None
    dirLocation = ""
    toolName = None
    outDirName = ""
    outText = None
    ppid = 0
    db = ""
    userID = 0
    isCrashed = False
    params = []
    stats = {}
    rowID = None
    updateMode = False
    waitExitCode = False
    allParamsAndTypes = {'User' : 'integer'
        , 'UserGroup': 'text'
        , 'ToolName': 'text'
        , 'ConfigNumber': 'integer'
        , 'LogFile' : 'text'
        , 'UsageTime': 'float'
        , 'StartTime': 'double'
        , 'EndTime': 'double'
        , 'Platform': 'text'
        , 'CPUs': "integer"
        , 'TotalRAM': 'integer'
        , 'TotalSwap': 'integer'
        , 'MaxRAMUsage': 'float'
        , 'MaxVirtualMemUsage': 'float'
        , 'CPUTime': 'integer'
        , 'ChildrenCPUTime': 'integer'
        , 'RealTime': 'integer'
        , 'ExitCode': 'integer'
        , 'CrashStack': 'text'}


    def __init__(self, helper):
        self.checkUser(helper.skipUsers)
        if helper.output:
            self.outText = helper.output
            if helper.pid:
                self.ppid = helper.pid
        elif helper.runCommand != None:
            self.proc = subprocess.Popen(helper.runCommand)
            self.procID = self.proc.pid
        elif helper.pid:
            if helper.childName:
                self.toolName = helper.childName
                self.ppid = helper.pid
                for i in range(0, 10):
                    try:
                        for p in psutil.Process(self.ppid).children():
                            if p.name() == helper.childName:
                                self.procID = p.pid
                                break
                        if self.procID != -1:
                            break
                        else:
                            time.sleep(1)
                    except:
                        pass
            else:
                self.procID = helper.pid
                self.ppid = psutil.Process(self.procID).parent().pid
            try:
                self.proc = psutil.Process(self.procID)
            except Exception as e:
                logging.error(e)
                logging.info(self.toolName)
                try:
                    pp = psutil.Process(self.ppid)
                    logging.info(pp.children())
                except Exception as exception:
                    logging.exception(exception)
                self.proc = None
        else:
            self.updateMode = True
            self.rowID = helper.updateRowID
            self.columnName = helper.updateColumn
            self.updateValue = helper.updateValue
        self.collectStats = helper.collectStatistics
        self.collectLogs = helper.collectLogs
        self.collectNonCrashedLogs = helper.collectNonCrashedLogs
        self.userID = helper.uid
        self.dirLocation = helper.dirName
        self.db = self.dirLocation + '/data.sqlite'
        self.params = list(self.allParamsAndTypes.keys())
        self.skipParams(helper.params)
        self.addMainColumns()
        self.addCustomColumns(helper)

    def addMainColumns(self):
        Table.preSessionTasks['StartTime']       = Task(Stats.getStartTime, ['pid'], 'integer')
        Table.preSessionTasks['User']            = Task(Stats.getUserId, ['pid'])
        Table.preSessionTasks['UserGroup']       = Task(Stats.getUserGroupId, ['pid'])
        Table.preSessionTasks['ToolName']        = Task(Stats.getProcessName, ['pid'])
        #Table.preSessionTasks['CPUFamily']       = Task(Stats.getCPUFamily, ['pid'])
        Table.preSessionTasks['Platform']        = Task(Stats.getPlatform, ['pid'])
        #Table.preSessionTasks['CPUArchitecture'] = Task(Stats.getCPUArchitecture, ['pid'])
        #Table.preSessionTasks['CPU_MHz']         = Task(Stats.getCPUMHz, [])
        Table.preSessionTasks['CPUs']            = Task(Stats.getCPUs, ['pid'])
        Table.preSessionTasks['TotalSwap']       = Task(Stats.getTotalSwap, ['pid'])
        Table.preSessionTasks['TotalRAM']        = Task(Stats.getTotalRAM, ['pid'])
        #Table.preSessionTasks['DisplayInfo']     = Task(Stats.getDisplayInfo, ['pid'])
        Table.runtimeTasks['CPUTime']            = Task(Stats.getCPUTime, ['pid'], 'float')
        Table.runtimeTasks['ChildrenCPUTime']    = Task(Stats.getChildrenCPUTime, ['pid'], 'float')
        Table.runtimeTasks['MaxRAMUsage']        = Task(Stats.getMaxRAMUsage, ['pid', 'last'], 'float')
        Table.runtimeTasks['MaxVirtualMemUsage'] = Task(Stats.getMaxVirtualMemUsage, ['pid', 'last'], 'float')
        Table.postSessionTasks['EndTime']        = Task(time.time, [], 'double', 0)
        Table.postSessionTasks['RealTime']       = Task(lambda a, b: a - b, ['stats[EndTime]','stats[StartTime]'], 'double', 1)
        Table.postSessionTasks['CrashStack']     = Task(LogProcessing.getStack, [], 'text', 1)
        Table.postSessionTasks['ExitCode']       = Task(LogProcessing.getExitCode, [], 'integer', 1)
        Table.postSessionTasks['ToolVersion']    = Task(LogProcessing.getToolVersion, [], 'text', 1)
        Table.postSessionTasks['UsageTime']      = Task(LogProcessing.getUsageTime, [], 'double', 1)
        Table.postSessionTasks['ConfigNumber']   = Task(LogProcessing.getConfigNumber, [], 'integer', 1)
        Table.postSessionTasks['LogFile']        = Task(LogProcessing.getLogFile, [], 'text', 1)


    def addCustomColumns(self, helper):
        self.execVars = {'pid': self.procID, 'user': self.userID, 'outDir': self.dirLocation, 'crashStatus': self.isCrashed, 'last': ""}
        for cc in helper.customColumns:
            taskString = helper.customColumns[cc]
            if not self.checkIfVarsInVarList(taskString[2:]):
                continue
            if taskString[0] == "runtime":
                Table.runtimeTasks[cc] = Task(taskString[1], taskString[2:])
            elif taskString[0] == "preSession":
                Table.preSessionTasks[cc] = Task(taskString[1], taskString[2:])
            elif taskString[0] == "postSession":
                Table.postSessionTasks[cc] = Task(taskString[1], taskString[2:])

    def checkIfVarsInVarList(self, varlist):
        execVarNames = list(self.execVars.keys())
        for var in varlist:
            if var not in execVarNames and not re.search("stats\[.*\]", var): 
                print("bad var {v}".format(v=var))
                return False
        return True

    def start(self):
        if self.outText:
            self.dumpToFile()
            return
        if self.updateMode == True:
            self.updateStatistics()
            return
        self.checkOutDir()
        self.calculateRuntimeStatistics()
        LogProcessing.parseLog(self.logFile)
        LogProcessing.copyLogs(self)
        Table.processPostSessionTasks(self.execVars)
        if (self.collectStats):
            Table.commitToDB(self.db)

    def dumpToFile(self):
        if self.ppid == 0:
            ppid = os.getppid()
        else:
            ppid = self.ppid
        fileName = self.dirLocation + "/" + str(self.userID) + "." + socket.gethostname() + "." + str(ppid)
        f = open(fileName, 'w')
        f.write(self.outText)
        f.close()
        for i in range(0, 10):
            if os.path.exists(fileName):
                time.sleep(1)
            else:
                return
        # remove if still exist
        os.remove(fileName)

    def updateStatistics(self):
        if self.rowID and self.columnName and self.updateValue:
            self.updateDatabase("rowid", self.rowID, self.columnName, self.updateValue)

    def updateLastRow(self, column, value):
        if self.rowID:
            self.updateDatabase("rowid", self.rowID, column, value)

    def checkOutDir(self):
        if not os.path.isdir(self.dirLocation) or not os.access(self.dirLocation, os.W_OK):
            sys.exit()

    def checkDBFile(self):
        if not os.path.exists(self.db):
            open(self.db, 'w').close()
            os.chmod(self.db, 0o777)
        elif not os.path.isfile(self.db) or not os.access(self.db, os.W_OK):
            raise OSError("Unable to access db file.")

    def skipParams(self, skipParams):
        for skipParam in skipParams:
            try:
                self.params.remove(skipParam)
            except ValueError:
                pass

    def checkUser(self, skipUsers):
        if str(os.getuid()) in skipUsers or getpass.getuser() in skipUsers:
            exit(0)

    def calculateRuntimeStatistics(self):
        self.logFile = Stats.getLogFile(self.procID)

        Table.processPreSessionTasks(self.execVars)

        self.tracingInProcess = True
        t = Thread(target=self.getRuntimeStats)
        t.start()
        # TODO review/remove/update wait process
        try:
            self.proc.wait()
        except:
            pass
        if self.waitExitCode == True:
            self.getExitCodeFromFile()
        ######
        self.tracingInProcess = False
        t.join()

    def getExitCodeFromFile(self):
        fileName = self.dirLocation + "/" + str(self.userID) + "." + socket.gethostname() + "." + str(self.ppid)
        count = 0
        while not os.path.exists(fileName):
            time.sleep(1)
            count += 1
            if count > 30:
                return
        time.sleep(1)
        exitCode=None
        with open(fileName, 'r') as exitFile:
            exitCode = exitFile.read()
        self.stats['ExitCode'] = int(exitCode)
        try:
            os.remove(fileName)
        except:
            pass

    def getRuntimeStats(self):
        proc = psutil.Process(self.procID)
        while self.tracingInProcess:
            try:
                lf = Stats.getLogFile(self.procID)
                if lf != None:
                    self.logFile = lf
                if self.collectStats:
                    Table.processRuntimeTasks(self.execVars)
                time.sleep(1)
            except:
                pass

    def writeToDatabase(self):
        self.checkDBFile()
        db = StatsDB(self.db, self.stats["ToolVersion"])
        db.connect()
        self.rowID = db.write(self.allParamsAndTypes, self.stats)

    def updateDatabase(self, searchCol, searchVal, column, value):
        self.checkDBFile()
        db = StatsDB(self.db, self.stats["ToolVersion"])
        db.connect()
        db.updateAll(searchCol, searchVal, column, value)

