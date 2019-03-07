import os, sys
from shutil import copy
import time, random
from log_parser import LogParser
import logging
#import hashlib

outDirName = "logs"
year = None
month = None
day = None
logParser = None
copyedLogFileLocation = ""
copyedErrFileLocation = ""

def parseLog(logFile):
    global logParser
    logParser = LogParser(logFile)
    logParser.parse()
    return len(logParser.stack) != 0 or logParser.signalNumber != 0

def getStack():
    global logParser
    return md5Hashing(logParser.stack)

def getExitCode():
    global logParser
    return  logParser.signalNumber

def getToolVersion():
    global logParser
    return  logParser.toolVersion

def getUsageTime():
    global logParser
    return  logParser.sessionUsageTime

def getConfigNumber():
    global logParser
    return  logParser.config

def getLogFile():
    global copyedLogFileLocation
    return copyedLogFileLocation

def getErrFile():
    global copyedErrFileLocation
    return copyedErrFileLocation

def md5Hashing(text):
    return " ".join(text)
    #m = hashlib.new("md5")
    #for line in text:
    #    m.update(line.encode('utf-8'))
    #return m.hexdigest()

def setDirHierarchy():
    global year, month, day
    year = time.strftime("%Y")
    month = time.strftime("%b")
    day = time.strftime("%d")

def checkNCreateDir(root, dirName):
    if not os.path.isdir(root) or not os.access(root, os.W_OK):
        raise OSError("Unable to access '{path}'".format(path=root))
    root = root + "/" + dirName
    if not os.path.exists(root):
        os.mkdir(root)
        os.chmod(root, 0o777)
    return root

def createOutDir(dirPath, logTypeDir):
    global outDirName
    root = checkNCreateDir(dirPath, outDirName)
    root = checkNCreateDir(root, logTypeDir)
    setDirHierarchy()
    root = checkNCreateDir(root, year)
    root = checkNCreateDir(root, month)
    root = checkNCreateDir(root, day)
    return root

def copyFile(src, dest):
    if not os.path.isfile(src):
        return ""
    cp = dest
    if os.path.isdir(cp):
        cp = cp + "/" + os.path.basename(src)
    if os.path.exists(cp):
        fileName, extension = os.path.splitext(cp)
        cp = fileName + "_" + str(time.time()) + "_" + str(random.randint(1, 10000)) + extension
    copy(src, cp)
    os.chmod(cp, 0o666)
    return cp

def copyFiles(log, dest):
    if not os.path.isdir(dest):
        raise OSError("{d}: is not a directory".format(d=dest))
    if not os.access(dest, os.W_OK):
        raise OSError("{d}: write permission denied".format(d=dest))
    if not os.path.exists(log):
        raise OSError("{f}: doesn't exist".format(f=log))
    return copyFile(log, dest)

def copyLogs(stats):
    global copyedLogFileLocation
    global copyedErrFileLocation
    if stats.collectLogs == True and (stats.isCrashed == True or stats.collectNonCrashedLogs == True):
        try:
            if stats.isCrashed:
                logDir = "crashed"
            else:
                logDir = "not_crashed"
            outDir = createOutDir(stats.dirLocation, logDir)
            dest = copyFiles(stats.logFile, outDir)
            copyedLogFileLocation = dest[len(stats.dirLocation) + 1:]
            # copy of stderr log file
            if (os.stat(stats.errFile).st_size != 0) :
                outDir = createOutDir(stats.dirLocation, "stdErrors")
                dest = copyFiles(stats.errFile, outDir)
                copyedErrFileLocation = dest[len(stats.dirLocation) + 1:]
        except OSError as e:
            logging.debug(e)

