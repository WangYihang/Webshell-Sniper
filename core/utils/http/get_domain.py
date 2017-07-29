#!/usr/bin/env python
# encoding: utf-8

def get_domain(url):
    # http://127.0.0.1/c.php
    return url.split("://")[1].split("/")[0]
