#
#      Copyright (C) 2014 Sean Poyser
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves.urllib.parse import parse_qs, quote_plus, urlparse, parse_qsl
from six import PY2
import time
import urllib

import sys
if PY2:
    from urllib import FancyURLopener
    class MyOpener(FancyURLopener):
        version = 'TheWizardIsHere'

    myopener = MyOpener()
    urlretrieve = MyOpener().retrieve
    urlopen = MyOpener().open
    AddonTitle="[COLOR ghostwhite]XXXODUS[/COLOR] [COLOR lightsteelblue]Configure[/COLOR]"
else:
    # FancyURLopener was removed in Python 3.14 (Kodi 22); use a compatible replacement.
    from resources.lib.modules.py3opener import Opener as _Opener
    class MyOpener(_Opener):
        version = 'TheWizardIsHere'

    myopener = MyOpener()
    urlretrieve = MyOpener().retrieve
    urlopen = MyOpener().open
    AddonTitle="[COLOR ghostwhite]XXXODUS[/COLOR] [COLOR lightsteelblue]Configure[/COLOR]"

def _dp_update(dp, percent, *lines):
    # Kodi 19+: DialogProgress.update(percent:int, message) - no line2/line3, no floats
    percent = int(percent)
    if PY2: return dp.update(percent, *lines)
    msg = '\n'.join(l for l in lines if l and l.strip())
    if msg: dp.update(percent, msg)
    else: dp.update(percent)

def download(url, dest, dp = None):
    if not dp:
        dp = xbmcgui.DialogProgress()
        if PY2: dp.create(' ',"Download In Progress",' ', ' ')
        else: dp.create(' ',"Download In Progress")  # Kodi 19+: (heading, message)
    dp.update(0)
    start_time=time.time()
    urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp, start_time))

def auto(url, dest, dp = None):
	dp = xbmcgui.DialogProgress()
	start_time=time.time()
	urlretrieve(url, dest, lambda nb, bs, fs: _pbhookauto(nb, bs, fs, dp, start_time))

def _pbhookauto(numblocks, blocksize, filesize, url, dp):
	none = 0

def _pbhook(numblocks, blocksize, filesize, dp, start_time):
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
            mbs = '[COLOR lightskyblue]%.02f MB[/COLOR] of [B]%.02f MB[/B]' % (currently_downloaded, total)
            e = '[COLOR white][B]Speed: [/B][/COLOR][COLOR lightskyblue]%.02f Mb/s ' % mbps_speed  + '[/COLOR]'
            e += '[COLOR white][B]ETA: [/B][/COLOR][COLOR lightskyblue]%02d:%02d' % divmod(eta, 60)  + '[/COLOR]'
            _dp_update(dp, percent, mbs, e)
        except: 
            percent = 100 
            dp.update(percent) 
        if dp.iscanceled():
            dialog = xbmcgui.Dialog()
            dialog.ok(AddonTitle, 'The download was cancelled.')
				
            sys.exit()
            dp.close()