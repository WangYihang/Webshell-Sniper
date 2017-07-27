#!/usr/bin/env python
# encoding: utf-8

def list2string(l, prefix, suffix):
    result = ""
    for i in l:
        result += prefix + i + suffix
    return result
