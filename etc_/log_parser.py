import re
import time

class LogParser:
    logFile = None
    toolVersion = "unknown"
    config = None
    lastCommandTime = 0
    lastCommandHour = 0
    previousCommandTime = 0
    previousCommandHour = 0
    sessionUsageTime = 0
    commandMaxInterval = 300
    signalNumber = 0
    stack = []
    isStackExists = False
    commands = {}
    cmdCount = 0
    days = 0

    def __init__(self, logFile):
        self.logFile = logFile

    def parse(self):
        log = open(self.logFile, 'r')
        self.getToolVersion(log)
        self.readBody(log)
        log.close()

    def getToolVersion(self, log):
        for line in log:
            versionLine = re.search("\/c\s*Version\s+(\S+)", line)
            if versionLine:
                self.toolVersion = versionLine.group(1)
                break
        for line in log:
            reg = re.search("Build\s*\S*\s*Config\s+(\d+)", line)
            if reg:
                self.config = reg.group(1)
                break

    def readBody(self, log):
        for line in log:
            self.parseCommandLine(line)
            if self.isStackExists:
                break
        if not self.isStackExists:
            return
        for line in log:
            self.getStack(line)
        self.cleanStack()

    def parseCommandLine(self, line):
        reg = re.search("^(\[\S+\])?\s+/(\w)\s+(.*)", line)
        if not reg:
            return
        commandType = reg.group(2)
        commandLine = reg.group(3)
        if commandType == "o":
            self.checkSignalNumber(commandLine)
            return
        elif commandType == "c":
            if self.signalNumber == 0:
                self.checkSignalNumber(commandLine)
            self.checkForStack(commandLine)
            return
        elif commandType != "i":
            return
        self.getCommandTime(line)
        self.cmdCount += 1
        if self.deltaTimeBetweenCommands < self.commandMaxInterval and self.deltaTimeBetweenCommands > 0:
            self.sessionUsageTime += self.deltaTimeBetweenCommands
        #TODO add command frequency logger

    def checkSignalNumber(self, line):
        reg = re.search("^signal number\s*=\s*(\d+)", line)
        if reg:
            self.signalNumber = reg.group(1)

    def checkForStack(self, line):
        reg = re.search("^Stack Dump: VERSION", line)
        if reg:
            self.isStackExists = True

    def getStack(self, line):
        reg = re.search("(Frame) \d+(.*)", line)
        if reg:
            self.stack.append("{f} X{sl}".format(f=reg.group(1), sl=reg.group(2)))

    def cleanStack(self):
        pattern = "\S+::\S*"
        for line in self.stack:
            if re.search("SNPSee", line):
                pattern = "SNPSee"
                break
        i = 0
        while i < len(self.stack):
            if not re.search(pattern, self.stack[i]):
                self.stack.pop(i)
            else:
                i += 1
            
    def getCommandTime(self, line):
        reg = re.search("^\[((\d\d):\d\d:\d\d)\.(\d\d)\]", line)
        if not reg:
            return False
        self.previousCommandHour = self.lastCommandHour
        self.lastCommandHour = int(reg.group(2))
        if self.lastCommandHour < self.previousCommandHour:
            self.days += 1
        self.previousCommandTime = self.lastCommandTime
        self.lastCommandTime = time.mktime(time.strptime(reg.group(1), "%H:%M:%S")) + self.days * 86400 + float(reg.group(3)) / 100
        self.deltaTimeBetweenCommands = self.lastCommandTime - self.previousCommandTime
        return True
