# Runs a Cum With Me site engine (MainContent / GetCats / SearchSite / GetNextPage / ResolveLink)
# inside XXX-O-DUS: same list items, Next Page, search, favourites and Watch History as native sites.
import importlib
import os
import re

import xbmc
import xbmcvfs
import resolveurl

import kodi
import log_utils
from resources.lib.modules import utils
from resources.lib.modules import helper

buildDirectory = utils.buildDir
SEARCH = 'search::'
LATEST = 'latest'


def _engine(name):
    return importlib.import_module('cwm_engines.%s' % name).Scraper()


def _art(filename, kind):
    return xbmcvfs.translatePath(os.path.join('special://home/addons/script.xxxodus.artwork', 'resources/art/%s/%s' % (filename, kind)))


def menu(engine, filename, base_name, content_mode):
    dirlst = [{'name': 'Latest Videos', 'url': LATEST, 'mode': content_mode, 'icon': _art(filename, 'icon.png'),
               'fanart': _art(filename, 'fanart.jpg'), 'description': 'Newest videos on %s' % base_name, 'folder': True}]
    try:
        for c in _engine(engine).GetCats() or []:
            if c.get('url'):
                dirlst.append({'name': c.get('name', ''), 'url': c['url'], 'mode': content_mode, 'icon': _art(filename, 'icon.png'),
                               'fanart': _art(filename, 'fanart.jpg'), 'description': c.get('name', ''), 'folder': True})
    except Exception as e:
        log_utils.log('Could not load categories for %s :: %s' % (base_name, e), log_utils.LOGERROR)
        kodi.notify(msg='Categories unavailable, showing latest videos only')
    buildDirectory(dirlst)


def content(engine, filename, base_name, content_mode, player_mode, url, searched=False):
    try:
        eng = _engine(engine)
        if url.startswith(SEARCH):
            items = eng.SearchSite(url[len(SEARCH):])
        else:
            items = eng.MainContent('' if url in (LATEST, 'None', None) else url)
    except Exception as e:
        if searched: return '0'
        log_utils.log('Fatal Error in %s:: Error: %s' % (base_name, e), log_utils.LOGERROR)
        kodi.notify(msg='Fatal Error', duration=4000, sound=True)
        quit()

    dirlst = []
    for i in items or []:
        if not i.get('url'):      # 'Content From X' header rows
            continue
        dirlst.append({'name': re.sub(r'\[/?(?:COLOR[^\]]*|B|I)\]', '', i.get('name', '')), 'url': i['url'], 'mode': player_mode,
                       'icon': i.get('image') or _art(filename, 'icon.png'), 'fanart': _art(filename, 'fanart.jpg'), 'folder': False})

    if searched:
        if dirlst: buildDirectory(dirlst, stopend=True, isVideo=True)
        return str(len(dirlst))
    if not dirlst:
        kodi.notify(msg='No Content Found')
        quit()

    nxt = None
    if not url.startswith(SEARCH):
        try: nxt = eng.GetNextPage('' if url == LATEST else url)
        except Exception as e: log_utils.log('Error getting next page for %s :: %s' % (base_name, e), log_utils.LOGERROR)
    if nxt:
        buildDirectory(dirlst, stopend=True, isVideo=True)
        helper.scraper().get_next_page(content_mode, nxt + '|GOT_URL', None, filename)
    else:
        buildDirectory(dirlst, isVideo=True)


def play(engine, base_name, url, name=None, iconimage=None):
    from resources.lib.modules import player
    try:
        links = [l for l in (_engine(engine).ResolveLink(url) or []) if l.get('url')]
    except Exception as e:
        log_utils.log('Could not get links from %s :: %s' % (base_name, e), log_utils.LOGERROR)
        links = []
    if not links:
        kodi.notify(msg='Sorry, no links found')
        return
    if len(links) == 1:
        stream = links[0]['url']
    else:
        pick = kodi.dialog.select(name or base_name, [re.sub(r'\[/?(?:COLOR[^\]]*|B|I)\]', '', l.get('name', 'Link')) for l in links])
        if pick < 0: return
        stream = links[pick]['url']
    hmf = resolveurl.HostedMediaFile(stream)
    if hmf.valid_url():
        stream = hmf.resolve()
        if not stream:
            kodi.notify(msg='Link could not be resolved')
            return
    # XXX-O-DUS's player: records Watch History and plays
    player.play(stream, name or base_name, iconimage, ref=url, site=base_name)
