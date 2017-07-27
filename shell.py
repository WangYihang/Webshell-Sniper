#!/usr/bin/env python
# encoding: utf-8

from core.webshell import WebShell
from core.shell import Shell
from core.log import Log

import sys

def show_help():
    print "Usage : "
    print "        python %s [URL] [METHOD] [PASSWORD]" % (sys.argv[0])
    print "Example : "
    print "        python %s http://127.0.0.1/c.php POST c" % (sys.argv[0])
    print "Author : "
    print "        WangYihang <wangyihanger@gmail.com>"

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
    shell = Shell(webshell)
    shell.interactive()


if __name__ == "__main__":
    main()
