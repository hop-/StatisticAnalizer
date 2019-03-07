#!/bin/env python

import sqlite3
import sys, os
import datetime
from optparse import OptionParser


def print_formatted (name, value):
    print("\t{0:20} : {1}".format(name, value))


oParser = OptionParser()
oParser.add_option("-d", "--database"
    , dest="db"
    , type="string"
    , help="Path to sqlite3 database file")
oParser.add_option("-r", "--release"
    , dest="release"
    , type="string"
    , help="Release name to get statistics for")


(opts, a) = oParser.parse_args(sys.argv)

if opts.db is None:
    print("Error: -d/--database options is required")
    exit(1)

if not os.path.isfile(opts.db):
    print("Error: database file '%s' doesn't exist" % opts.db)
    exit(1)

conn = sqlite3.connect(opts.db)
cur = conn.cursor()

releases = cur.execute("SELECT name FROM sqlite_master WHERE type='table' order by name asc;").fetchall()
releases = [str(r[0]) for r in releases]

if opts.release is not None:
    if opts.release in releases:
        releases = [opts.release] 
    else:
        print("Error: no release name '%s' in db '%s'" % (opts.release, opts.db))
        print("Available releases are: %s" % ", ".join(releases))
        exit(1)

if __name__ == "__main__":
    
    for r in releases:
        try:
            totalLogs      = cur.execute("SELECT count(*) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            crashLogs      = cur.execute("SELECT count(*) FROM `%s` WHERE ExitCode<>'None' and ExitCode>0 or CrashStack <> '';" % r).fetchall()[0][0]
            uniqueCrashLogs = cur.execute("SELECT count(*) FROM `%s` WHERE ExitCode<>'None' and ExitCode>0 or CrashStack <> '' group by CrashStack;" % r).fetchall()
            totalUsage     = cur.execute("SELECT sum(UsageTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            cpuUsage     = cur.execute("SELECT sum(CPUTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            realUsage     = cur.execute("SELECT sum(RealTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            maxUsage     = cur.execute("SELECT max(UsageTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            maxUsageCrashed    = cur.execute("SELECT max(UsageTime) FROM `%s` WHERE ExitCode<>'None' and ExitCode>0 or CrashStack <> '';" % r).fetchall()[0][0]
            minUsage     = cur.execute("SELECT min(UsageTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            minUsageCrashed    = cur.execute("SELECT min(UsageTime) FROM `%s` WHERE ExitCode<>'None' and ExitCode>0 or CrashStack <> '';" % r).fetchall()[0][0]
            avgUsage     = cur.execute("SELECT avg(UsageTime) FROM `%s` WHERE 1=1;" % r).fetchall()[0][0]
            avgUsageCrashed    = cur.execute("SELECT avg(UsageTime) FROM `%s` WHERE ExitCode<>'None' and ExitCode>0 or CrashStack <> '';" % r).fetchall()[0][0]
            
            if maxUsage is None:
                maxUsage = 0
            if maxUsageCrashed is None:
                maxUsageCrashed = 0
            
            if minUsage is None:
                minUsage = 0
            if minUsageCrashed is None:
                minUsageCrashed = 0
            
            if avgUsage is None:
                avgUsage = 0
            if avgUsageCrashed is None:
                avgUsageCrashed = 0
            
            usersCount      = cur.execute("SELECT User FROM `%s` GROUP by User;" % r).fetchall()
    
            mtbc=0
            if crashLogs > 0:
              mtbc = totalUsage / crashLogs
    
            print("%s"%r)
            
            print_formatted('Total Sessions', totalLogs)
            print_formatted('Crashed Sessions', crashLogs)
            print_formatted('Unique Crashes', len(uniqueCrashLogs))
            print_formatted('Users', len(usersCount))
            print ("");
            
            print_formatted('CPU Time',        "%s hours of cpu usage" % "{0:0.3f}".format(cpuUsage / 3600))
            print_formatted('Elapsed Time',    "%s hours tool was up" % "{0:0.3f}".format(realUsage / 3600))
            print_formatted("Usage Time",      "%s hours tool activly used" % "{0:0.3f}".format(totalUsage / 3600))
            print_formatted("MTBC",        "%s hours (Usage Time / Crashed Sessions)" % "{0:0.3f}".format(mtbc / 3600))
            
            print ("");
            print_formatted("Longest Session", "%s hours across all sessions" % "{0:0.3f}".format(maxUsage/3600))
            print_formatted("",            "%s hours across crashed sessions" % "{0:0.3f}".format(maxUsageCrashed/3600))
            print_formatted("Shortest Session","%s hours across all sessions" % "{0:0.3f}".format(minUsage/3600))
            print_formatted("",                "%s hours across crashed sessions" % "{0:0.3f}".format(minUsageCrashed/3600))
            print_formatted("Average Session", "%s hours across all sessions" % "{0:0.3f}".format(avgUsage/3600))
            print_formatted("",                "%s hours across crashed sessions" % "{0:0.3f}".format(avgUsageCrashed/3600))
            
            print ("")
        except sqlite3.OperationalError:
            pass

    print ("")
    conn.close()


