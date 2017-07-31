#!/usr/bin/env python
# encoding: utf-8

import hashlib

def get_md5(content):
    return hashlib.md5(content).hexdigest()

def hash_file(filename):
    with open(filename, "r") as f:
        return get_md5(f.read())

if __name__ == "__main__":
    print hash_file("/etc/passwd")
