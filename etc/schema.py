import os
import subprocess


from db import StatsDB
import stats

class ProcessInfo:
    pid  = None
    type = 'text'
    callback = None
    
    def __init__(self, callback, type = 'text'):
        self.type = type
        self.callback = callback
        
    def getInfo(self, *args):
        if not self.callback:
            raise AttributeError('Error: %s missing callback attribute' % self.name)
        if callable(self.callback):
            return self.callback(*args)
        elif os.path.isfile(str(self.callback)) and os.access(str(self.callback), os.X_OK):
            return subprocess.check_output([str(self.callback), self.id])
        else:
            raise AttributeError('Error: %s callback attribute is not callable' % self.name)
        


class Schema:
    User = ProcessInfo(stats.getUser, 'integer'),
    
    
    
    def __init__(self, dbFileName, tableName):
       self._db = 'AAAAAAAA'
       
    @staticmethodl
    def getFields():
        return [getattr(Schema, attr)[0] for attr in dir(Schema) if not callable(getattr(Schema, attr)) and not attr.startswith("__")]