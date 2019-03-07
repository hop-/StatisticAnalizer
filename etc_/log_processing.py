import os, sys
from shutil import copy
import time, random
from log_parser import LogParser
import logging
#import hashlib

outDirLocation = ""
outDirName = "logs"
year = None
month = None
day = None
logParser = None
copyedLogFileLocation = ""

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

def checkDirHierarchy(root, crashed):
    root = checkNCreateDir(root, outDirName)
    setDirHierarchy()
    root = checkNCreateDir(root, year)
    root = checkNCreateDir(root, month)
    root = checkNCreateDir(root, day)
    if not crashed:
        checkNCreateDir(root, "nonCrashed")

def checkNCreateDir(root, dirName):
    if not os.path.isdir(root) or not os.access(root, os.W_OK):
        raise OSError("Unable to access '{path}'".format(path=root))
    root = root + "/" + dirName
    if not os.path.exists(root):
        os.mkdir(root)
        os.chmod(root, 0o777)
    return root

def setOutDir(dirPath, crashed):
    global outDirLocation
    checkDirHierarchy(dirPath, crashed)
    outDirLocation = dirPath + "/" + outDirName + "/" + year + "/" + month + "/" + day
    if not crashed:
        outDirLocation += "/nonCrashed"

def copyFile(src, dest):
    if not os.path.isfile(src):
        return
    cp = dest
    if os.path.isdir(cp):
        cp = cp + "/" + os.path.basename(src)
    if os.path.exists(cp):
        fileName, extension = os.path.splitext(cp)
        cp = fileName + "_" + str(time.time()) + "_" + str(random.randint(1, 10000)) + extension
    copy(src, cp)
    os.chmod(cp, 0o666)

def copyFiles(log):
    dest = outDirLocation + "/"
    if not os.path.isdir(dest):
        raise OSError("{d}: is not a directory".format(d=dest))
    if not os.access(dest, os.W_OK):
        raise OSError("{d}: write permission denied".format(d=dest))
    if not os.path.exists(log):
        raise OSError("{f}: doesn't exist".format(f=log))
    copyFile(log, dest)

def copyLogs(stats):
    global copyedLogFileLocation
    if stats.collectLogs == True and (stats.isCrashed == True or stats.collectNonCrashedLogs == True):
        try:
            setOutDir(stats.dirLocation, stats.isCrashed)
            copyFiles(stats.logFile)
            relativePath = outDirName + "/" + year + "/" + month + "/" + day
            copyedLogFileLocation = "{path}/{logFile}".format(path=relativePath, logFile=os.path.basename(stats.logFile))
        except OSError as e:
            logging.debug(e)

