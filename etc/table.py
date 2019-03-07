import subprocess
import os
from db import StatsDB
import re

class Task:
    def __init__(self, execute, varList, type = 'text', priority = 10):
        self.callback = execute
        self.type = type
        self.priority = priority
        self.varList = varList

    def execute(self, variables):
        args = []
        for var in self.varList:
            try:
                args.append(variables[var])
            except KeyError:
                r = re.search("stats\[(.*)\]", var)
                if r:
                    args.append(Table.getData(r.group(1)))
                else:
                    raise AttributeError('Unreslvable attribute {a} of {t}.'.format(a=var, t=name))
        if not self.callback:
            raise AttributeError('Missing callbeck attribute.')
        elif callable(self.callback):
            return self.callback(*args)
        elif os.path.isfile(str(self.callback)) and os.access(str(self.callback), os.X_OK):
            command = [str(self.callback)]
            for arg in args:
                command.append(str(arg))
            return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        else:
            raise AttributeError('Unable to execute callback.')

class Table:
    runtimeTasks = {}
    preSessionTasks = {}
    postSessionTasks = {}
    headers = None
    data = {}

    @staticmethod
    def getHeaders():
        if Table.headers != None:
            return Table.headers
        Table.headers = {}
        for header in Table.runtimeTasks:
            Table.headers[header] = Table.runtimeTasks[header].type
        for header in Table.postSessionTasks:
            Table.headers[header] = Table.postSessionTasks[header].type
        for header in Table.preSessionTasks:
            Table.headers[header] = Table.preSessionTasks[header].type
        return Table.headers

    @staticmethod
    def getData(name):
        try:
            return Table.data[name]
        except KeyError:
            taskType = Table.getHeaders()[name]
            if taskType == 'integer' or taskType == 'double' or taskType == 'float':
                return 0
            else:
                return ""

    @staticmethod
    def processRuntimeTasks(variables):
        for task, v in sorted(Table.runtimeTasks.items(), key = lambda k: k[1].priority):
            variables['last'] = Table.getData(task)
            Table.data[task] = Table.runtimeTasks[task].execute(variables)

    @staticmethod
    def processPreSessionTasks(variables):
        for task, v in sorted(Table.preSessionTasks.items(), key = lambda k: k[1].priority):
            variables['last'] = Table.getData(task)
            Table.data[task] = Table.preSessionTasks[task].execute(variables)

    @staticmethod
    def processPostSessionTasks(variables):
        for task, v in sorted(Table.postSessionTasks.items(), key = lambda k: k[1].priority):
            variables['last'] = Table.getData(task)
            Table.data[task] = Table.postSessionTasks[task].execute(variables)

    @staticmethod
    def commitToDB(dbFile):
        db = StatsDB(dbFile, Table.data["ToolVersion"])
        db.connect()
        Table.rowID = db.write(Table.getHeaders(), Table.data)
