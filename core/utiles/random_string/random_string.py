#!/usr/bin/env python
# encoding: utf-8

from random import choice

def random_string(length, random_range):
    result = ""
    for i in range(length):
        result += choice(random_range)
    return result

