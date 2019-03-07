import psutil
import platform
import time

"""
Get Process User ID
"""
def getUserId(pid):
    return psutil.Process(pid).uids().real
    
"""
Get Process User Group ID
"""
def getUserGroupId(pid):
    return psutil.Process(pid).gids().real
    

def  getStartTime(pid):
    starttime = time
    try:
       starttime = psutil.Process(pid).create_time()
       
    except:
       pass
       
    return starttime
    
def getProcessName(pid):
    return psutil.Process(pid).name()
    
def getCPUFamily(pid):
    return "TODO"
    
def getPlatform(pid):
    return platform.platform()
    
def getCPUArchitecture(pid):
    return "TODO"
    
def getCPUMHz(pid):
    return "TODO"

def getCPUs(pid):
    return str(psutil.cpu_count(False)) + "/" + str(psutil.cpu_count())

def getTotalSwap(pid):
    return psutil.swap_memory().total >> 20

def getTotalRAM(pid):
    return psutil.virtual_memory().total >> 20


def getCPUTime(pid):
    proc = psutil.Process(pid)
    return proc.cpu_times().user
    
def getChildrenCPUTime(pid):
    proc = psutil.Process(pid)
    return proc.cpu_times().children_user
    

def getMaxRAMUsage(pid, prevRAMUsage = 0):
    proc = psutil.Process(pid)
    return max(prevRAMUsage, proc.memory_info().rss >> 20)

def getMaxVirtualMemUsage(pid, prevVirtualMemUsage = 0):
    proc = psutil.Process(pid)
    return max(prevVirtualMemUsage, proc.memory_info().vms >> 20)


def getDisplayInfo(pid):
    return "TODO"


def getLogFile(pid):
    proc = psutil.Process(pid)
    
    logFile = None
    id = None
    
    # We consider first opened *.log file as a log file
    for fd in proc.open_files():
        if fd.path.endswith(".log"):
            if id is None or id > fd.fd:
                logFile = fd.path
                id = fd.fd
            
    return logFile