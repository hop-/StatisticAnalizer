import sqlite3
import time
import logging
import re
import os

class StatsDB:
    fileName=""
    conn = None
    cur = None
    tableName = ""

    def __init__(self, dbFileName, release):
        self.fileName = dbFileName
        self.testDBFile()
        self.tableName = str(release)
        if self.tableName == "":
            self.tableName = "unknown"
        else:
            reg = re.search("^(.*)-\d\d+$", self.tableName)
            if reg:
                self.tableName = reg.group(1)
            self.tableName = re.sub(r"\.|\-", "_", self.tableName)

    def __del__(self):
        if not self.conn is None:
            self.conn.close()

    def testDBFile(self):
        if not os.path.exists(self.fileName):
            open(self.fileName, 'w').close()
            os.chmod(self.fileName, 0o777)
        elif not os.path.isfile(self.fileName) or not os.access(self.fileName, os.W_OK):
            raise OSError("Unable to access db file - {filePath}.".format(filePath=self.fileName))

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.fileName)
            self.cur = self.conn.cursor()

    def write(self, header, values):
        if self.conn == None:
            return
        if not self.tableIsExist():
            self.createTable(header)
        else:
            self.updateTable(header)
        return self.addRow(header, values)

    def updateAll(self, searchColumn, searchValue, updateColumn, updateValue):
        if self.conn == None or not self.tableIsExist():
            return
        tryCount = 0
        while True:
            try:
                self.cur.execute("update '{tn}' set {uc}='{uv}' where {c}='{v}'"\
                        .format(tn=self.tableName, uc=updateColumn, uv=updateValue, c=searchColumn, v=searchValue))
                break
            except:
                tryCount += 1
                if tryCount > 10:
                    logging.debug("Faild to update database")
                    break
                time.sleep(1)
        self.commit()

    def tableIsExist(self):
        self.cur.execute("select count(*) from sqlite_master where type='table' and name='{tn}'"\
                .format(tn=self.tableName))
        if self.cur.fetchone()[0] != 0:
            return True
        return False


    def getColumns(self):
        desc = self.cur.execute("select * from '{tn}' where 1=2".format(tn=self.tableName))
        return [description[0] for description in desc.description]

    def updateTable(self, headerDictionary):
        columns = self.getColumns()
        for key in headerDictionary.keys():
            name = str(key)
            type = str(headerDictionary[key])
            
            if (name not in columns):
                self.conn.execute("alter table '{tn}' add '{name}' {type}".format(tn=self.tableName, name=name, type=type))
            
    def createTable(self, headerDictionary):
        header = []
        for key in headerDictionary.keys():
            column = str(key) + " " + str(headerDictionary[key])
            header.append(column)
        strHeader = ", ".join(header)
        self.conn.execute("create table if not exists '{tn}' ({h})"\
                .format(tn=self.tableName, h=strHeader))

    def addRow(self, header, values):
        columns = list(header.keys())
        existColumns = list(values.keys())
        realColumns = []
        valueList = []
        rowID = None
        for column in existColumns:
            if not column in columns:
                continue
            realColumns.append(str(column))
            valueList.append("'" + str(values[column]) + "'")
        if (len(realColumns)) == 0:
            return
        tryCount = 0
        while True:
            try:
                self.cur.execute("insert into '{tn}' ({cs}) values ({vs})"\
                        .format(tn=self.tableName, cs=", ".join(realColumns), vs=", ".join(valueList)))
                rowID = self.cur.lastrowid
                break
            except:
                tryCount += 1
                if tryCount > 10:
                    logging.debug("Faild to insert a row into database")
                    break
                time.sleep(1)
        self.commit()
        return rowID

    def commit(self):
        tryCount = 0
        while True:
            try:
                self.conn.commit()
                break
            except:
                tryCount += 1
                if tryCount > 10:
                    logging.debug("Faild to commit to database")
                    break
                time.sleep(1)
