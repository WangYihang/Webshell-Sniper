#!/usr/bin/env python
# encoding: utf-8

import urllib

def url_encode(word):
    return urllib.quote(word)

def url_decode(word):
    return urllib.unquote(word)

def build_url(url, params):
    if not url.endswith("?"):
        url += "?"
    for key,value in params.items():
        url += "%s=%s&" % (key, url_encode(value))
    return url[0:-1]
