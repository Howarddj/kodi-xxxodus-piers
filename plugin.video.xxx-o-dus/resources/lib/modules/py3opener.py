# -*- coding: utf-8 -*-
"""
Drop-in replacement for urllib.request.FancyURLopener.

Python 3.14 (bundled with Kodi 22 "Piers") removed URLopener and
FancyURLopener from urllib.request. The add-on subclassed FancyURLopener at
import time, so on Kodi 22 it crashed with
    AttributeError: module 'urllib.request' has no attribute 'FancyURLopener'
before any menu was drawn.

This class keeps the two methods the add-on uses, open() and retrieve(),
including the reporthook(blocknum, blocksize, totalsize) progress callback,
and works on every Python 3 version.
"""
import os
import tempfile
import urllib.request


class Opener(object):
    version = 'Python-urllib'
    blocksize = 1024 * 8

    def __init__(self, user_agent=None):
        if user_agent:
            self.version = user_agent

    def _request(self, url, data=None):
        return urllib.request.Request(url, data=data, headers={'User-Agent': self.version})

    def open(self, url, data=None):
        return urllib.request.urlopen(self._request(url, data))

    def retrieve(self, url, filename=None, reporthook=None, data=None):
        with self.open(url, data) as fp:
            headers = fp.info()
            if filename:
                out = open(filename, 'wb')
            else:
                fd, filename = tempfile.mkstemp()
                out = os.fdopen(fd, 'wb')
            with out:
                try:
                    size = int(headers.get('Content-Length', -1))
                except (TypeError, ValueError):
                    size = -1
                blocknum = 0
                if reporthook:
                    reporthook(blocknum, self.blocksize, size)
                while True:
                    block = fp.read(self.blocksize)
                    if not block:
                        break
                    out.write(block)
                    blocknum += 1
                    if reporthook:
                        reporthook(blocknum, self.blocksize, size)
        return filename, headers
