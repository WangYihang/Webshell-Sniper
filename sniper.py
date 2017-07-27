#!/usr/bin/env python
# encoding: utf-8

from core.webshell import WebShell
from core.shell import Shell
from core.log import Log

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
    print "        1. h : show this help"
    print "        2. sh : start an interactive shell"
    print "        3. rsh : start an reverse shell"
    print "                rsh [IP] [PORT]"
    print "        4. q : quit"

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

    while True:
        Log.context("sniper")
        context = raw_input("=>")
        if string.lower(context) == "h":
            main_help()
        elif string.lower(context) == "sh":
            shell = Shell(webshell)
            shell.interactive()
        elif string.lower(context) == "rsh":
            Log.warning("Developing...")
        elif string.lower(context) == "q":
            break
        else:
            Log.error("Unsupported command!")
            main_help()

if __name__ == "__main__":
    main()
