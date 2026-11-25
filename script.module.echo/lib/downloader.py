"""
    Copyright (C) 2016 ECHO Wizard

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# Ported to Python 3 (Kodi 19+ / Kodi 22): `from urllib import FancyURLopener`
# was Python 2 only, FancyURLopener was removed entirely in Python 3.14, and
# DialogProgress.create()/update() now take (heading, message)/(percent, message).
import xbmcgui
import time
import sys
import os
import tempfile

PY2 = sys.version_info[0] == 2
_UA = 'python-requests/2.9.1'

if PY2:
    from urllib import FancyURLopener

    class MyOpener(FancyURLopener):
        version = _UA
else:
    import urllib.request

    class MyOpener(object):
        """Same open()/retrieve() interface as FancyURLopener."""
        version = _UA
        blocksize = 1024 * 8

        def open(self, url, data=None):
            return urllib.request.urlopen(urllib.request.Request(url, data=data, headers={'User-Agent': self.version}))

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

myopener = MyOpener()
urlretrieve = MyOpener().retrieve
urlopen = MyOpener().open
AddonTitle = "[COLOR red]XXX-O-DUS[/COLOR]"


def _dp_create(dp, heading, message):
    if PY2: dp.create(heading, message, ' ', ' ')
    else: dp.create(heading, message)


def _dp_update(dp, percent, *lines):
    percent = int(percent)
    if PY2: dp.update(percent, *lines)
    else:
        msg = '\n'.join(l for l in lines if l and l.strip())
        if msg: dp.update(percent, msg)
        else: dp.update(percent)


def download(url, dest, dp=None):
    if not dp:
        dp = xbmcgui.DialogProgress()
        _dp_create(dp, AddonTitle, "Download In Progress")
    dp.update(0)
    start_time = time.time()
    urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(dest, nb, bs, fs, dp, start_time))


def auto(url, dest, dp=None):
    dp = xbmcgui.DialogProgress()
    start_time = time.time()
    urlretrieve(url, dest, lambda nb, bs, fs: _pbhookauto(nb, bs, fs, dp, start_time))


def _pbhookauto(numblocks, blocksize, filesize, url, dp):
    none = 0


def _pbhook(dest, numblocks, blocksize, filesize, dp, start_time):
    try:
        percent = min(numblocks * blocksize * 100 / filesize, 100)
        currently_downloaded = float(numblocks) * blocksize / (1024 * 1024)
        kbps_speed = numblocks * blocksize / (time.time() - start_time)
        if kbps_speed > 0:
            eta = (filesize - numblocks * blocksize) / kbps_speed
        else:
            eta = 0
        kbps_speed = kbps_speed / 1024
        mbps_speed = kbps_speed / 1024
        total = float(filesize) / (1024 * 1024)
        mbs = '[COLOR pink]%.02f MB[/COLOR] of [B]%.02f MB[/B]' % (currently_downloaded, total)
        e = '[COLOR white][B]Speed: [/B][/COLOR][COLOR pink]%.02f Mb/s ' % mbps_speed + '[/COLOR]'
        e += '[COLOR white][B]ETA: [/B][/COLOR][COLOR pink]%02d:%02d' % divmod(eta, 60) + '[/COLOR]'
        _dp_update(dp, percent, mbs, e)
    except:
        percent = 100
        dp.update(percent)
    if dp.iscanceled():
        dialog = xbmcgui.Dialog()
        dp.close()
        sys.exit()
