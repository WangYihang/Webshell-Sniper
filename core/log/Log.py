#!/usr/bin/env python
# encoding: utf-8

import color
import sys

class Log():
    def _print(self, word):
        sys.stdout.write(word + "\n")
        sys.stdout.flush()

    @staticmethod
    def info(self, word):
        self._print("[+] %s" % color.gray(word))

    @staticmethod
    def warning(self, word):
        self._print("[!] %s" % color.yellow(word))

    @staticmethod
    def error(self, word):
        self._print("[-] %s" % color.red(word))

    @staticmethod
    def success(self, word):
        self._print("[~] %s" % color.green(word))

    @staticmethod
    def query(self, word):
        self._print("[?] %s" % color.underline(word))
