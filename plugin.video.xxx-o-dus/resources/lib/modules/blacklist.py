from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves.urllib.parse import parse_qs, quote_plus, urlparse, parse_qsl, urljoin

import os,re,time
from six import PY2
if PY2:
    import adultresolver
    import linkfinder
else:
    from resources.lib.modules import adultresolver
    from resources.lib.modules import linkfinder
adultresolver = adultresolver.streamer()
dialog = xbmcgui.Dialog()
def _try(fn, url):
    # a site that is down raised straight out of the player (traceback, no message)
    try:
        fn(url)
    except Exception as e:
        xbmc.log('XXX-O-DUS: could not resolve %s :: %s' % (url, e), xbmc.LOGERROR)
        dialog.notification('XXX-O-DUS', 'Could not reach the site for this video', xbmcgui.NOTIFICATION_ERROR, 4000)


def Blacklistcheck(url):
    dialog.notification('XXX-O-DUS', '[COLOR yellow]Checking For Links Now, Be Patient[/COLOR]', xbmcgui.NOTIFICATION_INFO, 2500)
    if 'hclips.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'xvideos.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'youjizz.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'chaturbate.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'zzcartoon.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'daftporn.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'watchxxxfreeinhd.com' in url:
        _try(linkfinder.find, url)
        quit()
    elif 'youngpornvideos.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'freeomovie.info' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'javhihi.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'xnxx.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'txxx.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'vrsumo.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'anysex.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'pandamovie.info' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'streamingporn.xyz' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif '3movs.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'watchmygf.me' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'vrsmash.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif '4tube.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'justporno.tv' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'spankbang.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'teenpornsite.net' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'watchpornfree.info' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'pornhd.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'hqporner.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'porn.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'porndig.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'youporn.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'tube8.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'pornrox.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'collectionofbestporn.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'ghettotube.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'siska.video' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'overthumbs.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'fapality.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'xxxdan.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'motherless.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'redtube.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    elif 'adult-tv-channels.com' in url:
        _try(adultresolver.resolve, url)
        quit()
    else:
        return url
		