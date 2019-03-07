import os
import sys
from optparse import OptionParser
from optparse import SUPPRESS_HELP
import ConfigParser

class Helper:
    '''
    
    This class gets some data from ENV and arglist for further usage in Statistics

    Methods
    =======

      * Constructor/Destructor:
        
        - __init__(self, args): constructs an object

      * Functions used for construction:

        - getIDs():         sets pid an uid
        - setDirName():     sets directory name using CC_STATE_LOCATION env variable
        - setSkipParams():  sets params which should be skipped using CC_SKIP_COLUMNS
        - setSkipUsers():   sets users which should be skipped using CC_SKIP_USERS
        
      * Attributes:
        - dirName:      Location of directory where to output
        - pid:          Process id
        - uid:          user id
        - params:       skip param list
        - skipUsers:    skip user list
    
    '''
    dirName = ""
    configFile = None
    pid = 0
    runCommand = None
    uid = ""
    params = []
    skipUsers = []
    allParams = ""
    output = None
    customColumns = {}

    def __init__(self, args):
        if len(args) < 1:
            sys.exit("Wrong number of argument")
        self.parseOptions(args)
        self.setDefaultConfigurations()
        self.setDirName()
        if self.configFile == None:
            self.initConfigFileWithEnv()
        self.readConfigFile()
        self.uid = str(os.getuid())

    def parseOptions(self, args):
        oParser = OptionParser()
        oParser.add_option("-r", "--run"
                , dest="command"
                , type="string"
                , help="Command to execute and monitor")
        oParser.add_option("-p", "--pid"
                , dest="pid"
                , type="int"
                , help="Existing pid to monitor")
        oParser.add_option("--ptrace"
                , dest="ptrace"
                , action="store_true"
                , default="False"
#, help="Run utility in Ptrace mode (use with -p option)")
                , help=SUPPRESS_HELP)
        oParser.add_option("--child"
                , dest="child"
                , type="string"
                , help="command name of child (use with -p opetion)")
        oParser.add_option("-c", "--config"
                , dest="config"
                , type="string"
                , help="config file path (syntax json)")
        oParser.add_option("-o"
                , dest="output"
                , type="string"
                , help=SUPPRESS_HELP)
        oParser.add_option("-u", "--update"
                , dest="update"
                , type="int"
#, help="Update existing data with specified ID in database")
                , help=SUPPRESS_HELP)
        oParser.add_option("--column"
                , dest="column"
                , type="string"
#, help="Specific column to update (use with -u option)")
                , help=SUPPRESS_HELP)
        oParser.add_option("--value"
                , dest="value"
                , type="string"
#, help="Specific value to update (use with -u option)")
                , help=SUPPRESS_HELP)
        (opts, a) = oParser.parse_args(args)
        if opts.output:
            self.output = opts.output
            if opts.pid:
                self.pid = opts.pid
        elif opts.command != None:
            self.runCommand = opts.command
            if opts.pid != None:
                print("Skipping --pid: --run has higher priority")
            if opts.update != None:
                print("Skipping --update: --run has higher priority")
        elif opts.pid != None:
            self.pid = opts.pid
            if opts.update != None:
                print("Skipping --update: --pid has higher priority")
            self.ptraceMode = opts.ptrace
            self.childName = opts.child
        elif opts.update != None:
            self.updateRowID = opts.update
            if opts.column == None or opts.value == None:
                sys.exit("The following options are required for --update mode: --column and --value")
            self.updateColumn = opts.column
            self.updateValue = opts.value
        else:
            sys.exit("One of those three options is required: --run, --pid or --update")
        self.configFile = opts.config

    def setDefaultConfigurations(self):
        self.dirName = ""
        self.collectLogs = False
        self.collectNonCrashedLogs = False
        self.collectStatistics = True
        self.allParams = []
        self.skipUsers = []

    def readConfigFile(self):
        conf = ConfigParser.ConfigParser()
        if not os.path.isfile(self.configFile):
            return
        conf.read(self.configFile)
        section = "Watchdog"
        try:
            self.dirName = conf.get(section, "outputDirectory")
        except:
            pass
        try:
            self.collectStatistics = conf.getboolean(section, "collectStatistics")
            try:
                self.allParams = conf.get(section, "skipColumns")
            except:
                pass
            try:
                self.skipUsers = conf.get(section, "skipUsers").split()
            except:
                pass
        except:
               pass
        try:
            self.collectLogs = conf.getboolean(section, "collectLogs")
            try:
                self.collectNonCrashedLogs = conf.getboolean(section, "collectNonCrashLogs")
            except:
                pass
        except:
            pass
        customColumnsSection = "Custom Columns"
        if not customColumnsSection in conf.sections():
            return
        cc = dict(conf.items(customColumnsSection))
        for columnName in cc:
            task = cc[columnName].split(" ")
            if self.checkCustomColumnSyntax(task):
                for i in range(2, len(task)):
                    task[i] = task[i][1:]
                self.customColumns[columnName] = task

    def checkCustomColumnSyntax(self, cc):
        if (cc[0] != "runtime" and cc[0] != "postSession" and cc[0] != "preSession") or len(cc) < 2:
            print("bad callback type '{t}' in '{c}'".format(t = cc[0], c = " ".join(cc)))
            return False
        for attr in cc[2:]:
            if not attr.startswith("%") or len(attr) < 2:
                print("bad attr '{a}'".format(a=attr))
                return False
        return True

        

    def initConfigFileWithEnv(self):
        self.configFile = self.dirName + "/watchdog.cfg"
    
    def setDirName(self):
        try:
            self.dirName = str(os.environ['SYNOPSYS_CUSTOM_WATCHDOG_DIR'])
        except KeyError:
            pass
        try:
            self.configFile = str(os.environ['SYNOPSYS_CUSTOM_WATCHDOG_CONFIG'])
        except KeyError:
            pass

    def setSkipParams(self):
        allParams = ""
        try:
            allParams = os.environ['CC_SKIP_COLUMNS']
        except KeyError:
            pass
        self.params = allParams.split()

    def setSkipUsers(self):
        try:
            self.skipUsers = os.environ['CC_SKIP_USERS'].split()
        except KeyError:
            pass
            
