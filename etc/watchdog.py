#!/bin/env python
from helper import Helper
from statistics import Statistics
import log_processing as LogProcessing
import sys, signal
import logging
import os, time, random

def trapSignals():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)

def configureLogging():
    try:
        dirName = str(os.environ['SYNOPSYS_CUSTOM_WATCHDOG_LOGDIR'])
        logName = str(os.getuid()) + "_" + str(time.time()) + "_" + str(random.randint(1, 10000)) + ".log"
        log = dirName + "/" + logName
        logging.basicConfig(filename=log, level=logging.DEBUG)
        os.chmod(log, 0o777)
    except:
        logging.basicConfig(level=logging.CRITICAL)


def main(argv):
    helper = Helper(argv)
    stats = Statistics(helper)
    stats.start()
    return 0

if __name__ == "__main__":
    configureLogging()
    trapSignals()
    try:
        main(sys.argv[1:])
    except Exception as e:
        logging.exception(e)
