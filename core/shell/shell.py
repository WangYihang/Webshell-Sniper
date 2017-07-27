#!/usr/bin/env python
# encoding: utf-8

from core.log import Log
import string

class Shell():
    # TODO 命令执行添加 token , 以保证命令的正确执行
    def __init__(self, webshell):
        self.webshell = webshell

    def interactive(self):
        Log.info("Starting interactive shell...")
        while True:
            Log.context("sniper")
            Log.context("shell")
            command = raw_input("$ ")
            if string.lower(command) == "exit":
                Log.info("Exiting shell...")
                break
            result = self.webshell.auto_exec(command)
            if result[0]:
                Log._print(result[1])
            else:
                Log.error(result[1])
