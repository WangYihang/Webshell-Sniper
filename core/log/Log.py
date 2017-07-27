#!/usr/bin/env python
# encoding: utf-8

import color
import sys

class Log():
    @staticmethod
    def _print(word):
        sys.stdout.write(word)
        sys.stdout.flush()

    @staticmethod
    def info(word):
        Log._print("[+] %s\n" % color.lightPurple(word))

    @staticmethod
    def warning(word):
        Log._print("[!] %s\n" % color.yellow(word))

    @staticmethod
    def error(word):
        Log._print("[-] %s\n" % color.red(word))

    @staticmethod
    def success(word):
        Log._print("[+] %s\n" % color.purple(word))

    @staticmethod
    def query(word):
        Log._print("[?] %s\n" % color.underline(word))

    @staticmethod
    def context(context):
        Log._print("[%s]" % (color.red(context)))
