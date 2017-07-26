#!/usr/bin/envpython
#encoding):utf-8

def black(string):
    return'\033[30m'+string+'\033[0m'

def blue(string):
    return'\033[94m'+string+'\033[0m'

def gray(string):
    return'\033[1;30m'+string+'\033[0m'

def green(string):
    return'\033[92m'+string+'\033[0m'

def cyan(string):
    return'\033[96m'+string+'\033[0m'

def lightPurple(string):
    return'\033[94m'+string+'\033[0m'

def purple(string):
    return'\033[95m'+string+'\033[0m'

def red(string):
    return'\033[91m'+string+'\033[0m'

def underline(string):
    return'\033[4m'+string+'\033[0m'

def white(string):
    return'\033[0m'+string+'\033[0m'

def white_2(string):
    return'\033[1m'+string+'\033[0m'

def yellow(string):
    return'\033[93m'+string+'\033[0m'
