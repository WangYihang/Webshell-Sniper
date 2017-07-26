#!/usr/bin/env python
# encoding: utf-8

import color
import sys

class Log():
    @staticmethod
    def _print(word):
        sys.stdout.write(word + "\n")
        sys.stdout.flush()

    @staticmethod
    def info(word):
        Log._print("[+] %s" % color.lightPurple(word))

    @staticmethod
    def warning(word):
        Log._print("[!] %s" % color.yellow(word))

    @staticmethod
    def error(word):
        Log._print("[-] %s" % color.red(word))

    @staticmethod
    def success(word):
        Log._print("[+] %s" % color.purple(word))

    @staticmethod
    def query(word):
        Log._print("[?] %s" % color.underline(word))
