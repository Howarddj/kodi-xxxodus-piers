# -*- coding: utf-8 -*-
"""
Cum With Me as a normal Kodi list add-on (Kodi 22 / 23).

The original was a full-screen pyxbmct window with its own artwork, a chat room and online
counters served from Stream Army's pinsystem.co.uk. This version lists everything as ordinary
Kodi folders and items, so the skin decides the look (views, fonts, colours, artwork), and it
makes no connection to Stream Army servers: only the video sites themselves are contacted.
"""
import os
import re
import sys
import sqlite3
from urllib.parse import urlencode, parse_qsl, quote_plus, urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import requests
from bs4 import BeautifulSoup
import resolveurl

from resources.libs import net  # default timeout for every request

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = 'Cum With Me'
BASE = sys.argv[0]
HANDLE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].lstrip('-').isdigit() else -1
ICON = xbmcvfs.translatePath('special://home/addons/%s/icon.png' % ADDON_ID)
# no fanart on list items: the skin's own background shows, as in XXX-O-DUS

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.82'}
LIVE_URL = 'https://adult-tv-channels.com/'
LIVE_BASE = 'https://adult-tv-channels.com'
MOVIE_URL = 'https://pandamovies.pw/movies'
CAM_URL = 'https://chaturbate.com/api/ts/roomlist/room-list/?enable_recommendations=false&limit=100&offset=0'
CAM_TAGS_URL = 'https://chaturbate.com/api/ts/hashtags/tag-table-data/?sort=-vc&page=1&g=&limit=100'

DB_DIR = xbmcvfs.translatePath('special://profile/addon_data/%s/databases' % ADDON_ID)
DB = os.path.join(DB_DIR, 'cwm.db')

_TAGS = re.compile(r'\[/?(?:COLOR[^\]]*|B|I|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)\]', re.I)


def plain(text):
    """Text colour and weight are the skin's job: drop any [COLOR]/[B]/[I] tags."""
    return _TAGS.sub('', text).strip() if isinstance(text, str) else text


def log(msg, level=xbmc.LOGINFO):
    xbmc.log('[%s] %s' % (ADDON_ID, msg), level)


def notify(msg, icon=ICON, ms=3500):
    xbmcgui.Dialog().notification(ADDON_NAME, msg, icon, ms)


def build_url(**query):
    return BASE + '?' + urlencode({k: v for k, v in query.items() if v is not None})


def get(url, referer=None):
    h = dict(HEADERS)
    if referer: h['Referer'] = referer
    return requests.get(url, headers=h)


# ---------------------------------------------------------------------------- listing helpers

def add_folder(label, query, icon=None, plot='', context=None):
    li = xbmcgui.ListItem(plain(label), offscreen=True)
    li.setArt({'icon': icon or ICON, 'thumb': icon or ICON, 'poster': icon or ICON})
    if plot:
        li.getVideoInfoTag().setPlot(plain(plot))
    if context: li.addContextMenuItems(context)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(**query), li, isFolder=True)


def add_video(label, query, thumb=None, plot='', context=None):
    li = xbmcgui.ListItem(plain(label), offscreen=True)
    art = thumb or ICON
    li.setArt({'icon': art, 'thumb': art, 'poster': art})
    tag = li.getVideoInfoTag()
    tag.setTitle(plain(label))
    tag.setMediaType('video')
    if plot: tag.setPlot(plain(plot))
    li.setProperty('IsPlayable', 'true')
    if context: li.addContextMenuItems(context)
    xbmcplugin.addDirectoryItem(HANDLE, build_url(**query), li, isFolder=False)


def add_action(label, query, icon=None, plot=''):
    """A row that runs something (settings, notices) instead of opening a folder or playing."""
    li = xbmcgui.ListItem(plain(label), offscreen=True)
    li.setArt({'icon': icon or ICON, 'thumb': icon or ICON})
    if plot: li.getVideoInfoTag().setPlot(plain(plot))
    xbmcplugin.addDirectoryItem(HANDLE, build_url(**query), li, isFolder=False)


def end(content='files', ok=True, cache=True):
    xbmcplugin.setContent(HANDLE, content)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=ok, cacheToDisc=cache)


def next_page(query):
    add_folder('Next Page', query, plot='Load more')


# ------------------------------------------------------------------------------------ playback

def play(stream, thumb=None, title=None):
    """Resolve hosted links with ResolveURL; play direct streams as they are."""
    hmf = resolveurl.HostedMediaFile(stream)
    if hmf.valid_url():
        link = hmf.resolve()
        if not link:
            raise RuntimeError('ResolveURL could not resolve %s' % stream)
    else:
        link = stream
    li = xbmcgui.ListItem(plain(title or ADDON_NAME), path=link, offscreen=True)
    if thumb: li.setArt({'thumb': thumb, 'icon': thumb})
    if '.m3u8' in link.split('|')[0]:
        li.setMimeType('application/vnd.apple.mpegurl')
        li.setContentLookup(False)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def choose(links, heading='Choose a source'):
    """links: list of (label, url). One link plays straight away."""
    if not links:
        notify('Sorry, no links found')
        return None
    if len(links) == 1:
        return links[0][1]
    pick = xbmcgui.Dialog().select(heading, [plain(n) for n, _ in links])
    return links[pick][1] if pick >= 0 else None


# ------------------------------------------------------------------------------------- menus

def root():
    add_folder('Live XXX Channels', {'mode': 'live'}, plot='Live adult TV channels')
    add_folder('Live XXX Cams', {'mode': 'cams'}, plot='Live cams from Chaturbate, with favourites and online alerts')
    add_folder('XXX Movies', {'mode': 'movies'}, plot='Full-length movies')
    add_folder('XXX Sites', {'mode': 'sites'}, plot='Videos from %d sites, or search them all' % len(_sources()))
    add_action('Cum With Me Settings', {'mode': 'settings'}, plot='Performer online alerts')
    end('files')


# ------------------------------------------------------------------------------- live channels

def _page_url(url, page, slash=True):
    url = re.sub(r'/page/\d+/?$', '', url.rstrip('/'))
    return '%s/page/%d%s' % (url, page, '/' if slash else '')


def live(url=None, page=1):
    soup = BeautifulSoup(get(url or LIVE_URL).text, 'html.parser')
    found = 0
    for fig in soup.find_all('figure', class_={'entry-item-thumb'}):
        if not (fig.a and fig.img): continue
        href = fig.a['href']
        name = fig.img.get('alt') or fig.a.get('title') or href.rstrip('/').split('/')[-1].replace('-', ' ').title()
        add_video(name, {'mode': 'play_live', 'url': href, 'thumb': fig.img.get('src', '')}, fig.img.get('src'))
        found += 1
    if found:
        next_page({'mode': 'live', 'url': _page_url(LIVE_URL, page + 1), 'page': page + 1})
    end('videos')


def play_live(url, thumb=None):
    soup = BeautifulSoup(get(url).text, 'html.parser')
    iframe = soup.find('iframe')['src']
    if not iframe.startswith('http'): iframe = LIVE_BASE + iframe
    source = re.findall(r'''file:['"](.*?)['"]''', get(iframe, referer=url).text)[0]
    play('%s|Referer=%s' % (source, iframe), thumb)


# -------------------------------------------------------------------------------------- movies

def movies(url=None, page=1):
    base = url or MOVIE_URL
    if page == 1 and not url:
        add_folder('Studios', {'mode': 'movie_studios'}, plot='Browse by studio')
    page_url = base if page == 1 else _page_url(base, page)
    soup = BeautifulSoup(get(page_url).text, 'html.parser')
    found = 0
    for item in soup.find_all('div', class_={'ml-item'}):
        if not (item.a and item.img): continue
        href = item.a['href']
        img = item.img.get('data-lazy-src') or item.img.get('src', '')
        desc_tag = item.find('p', class_={'f-desc'})
        desc = desc_tag.text.strip() if desc_tag else ''
        title_tag = item.find(['h2', 'h3'])
        name = (item.a.get('title') or item.a.get('oldtitle') or (title_tag.text.strip() if title_tag else '')
                or item.img.get('alt') or href.rstrip('/').split('/')[-1].replace('-', ' ').title())
        add_video(name, {'mode': 'play_movie', 'url': href, 'thumb': img}, img, desc)
        found += 1
    if found:
        next_page({'mode': 'movies', 'url': url, 'page': page + 1})
    end('movies' if found else 'videos')


def movie_studios():
    soup = BeautifulSoup(get(MOVIE_URL).text, 'html.parser')
    menu = soup.find('li', id={'menu-item-23'})
    for a in (menu.find_all('a') if menu else []):
        if '#' not in a.get('href', '#'):
            add_folder(a.text.strip(), {'mode': 'movies', 'url': a['href']})
    end('files')


def play_movie(url, thumb=None):
    soup = BeautifulSoup(get(url).text, 'html.parser')
    tabs = soup.find('div', id={'pettabs'})
    links = []
    for a in (tabs.find_all('a') if tabs else []):
        href = a.get('href', '')
        if href and resolveurl.HostedMediaFile(href).valid_url():
            links.append(('Link %d  (%s)' % (len(links) + 1, urlparse(href).netloc), href))
    stream = choose(links)
    if not stream:
        return cancel()
    play(stream, thumb)


# ---------------------------------------------------------------------------------------- cams

def _db():
    if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
    conn = sqlite3.connect(DB)
    conn.execute('CREATE TABLE IF NOT EXISTS chaturbate (name, url, image)')
    return conn


def _cam_context(name, url, image, fav):
    if fav:
        return [('Remove from favourites', 'RunPlugin(%s)' % build_url(mode='cam_unfav', url=url, name=name))]
    return [('Add to favourites', 'RunPlugin(%s)' % build_url(mode='cam_fav', url=url, name=name, thumb=image))]


def cams(url=None):
    first = not url
    url = url or CAM_URL
    if first:
        add_folder('Favourites', {'mode': 'cam_favs'}, plot='Your favourite performers and whether they are online')
        add_folder('Tags', {'mode': 'cam_tags'}, plot='Browse cams by tag')
        alerts = 'on' if ADDON.getSetting('Monitor') == 'true' else 'off'
        add_action('Performer online alerts: %s' % alerts, {'mode': 'settings'},
                   plot='Get a notification when a favourite performer comes online. Change in settings.')
    rooms = get(url).json().get('rooms', [])
    for r in rooms:
        user = r.get('username', '')
        if not user: continue
        age = r.get('display_age') or '?'
        if len(str(age)) >= 3: age = '?'
        href = 'https://chaturbate.com/%s/' % user
        plot = 'Age: %s\nViewers: %s\n\n%s' % (age, r.get('num_users', '?'), r.get('subject', ''))
        add_video(user.title(), {'mode': 'play_cam', 'url': href, 'thumb': r.get('img', '')}, r.get('img'), plot,
                  _cam_context(user.title(), href, r.get('img', ''), False))
    if len(rooms) >= 100:
        m = re.search(r'offset=(\d+)', url)
        nxt = re.sub(r'offset=\d+', 'offset=%d' % (int(m.group(1)) + 100), url) if m else url + '&offset=100'
        next_page({'mode': 'cams', 'url': nxt})
    end('videos', cache=False)


def cam_tags():
    data = get(CAM_TAGS_URL).json()
    for t in data.get('hashtags', []):
        tag = t.get('hashtag', '')
        if not tag: continue
        add_folder('%s  (%s viewers)' % (tag.title(), t.get('viewer_count', '?')),
                   {'mode': 'cams', 'url': 'https://chaturbate.com/api/ts/roomlist/room-list/?enable_recommendations=false'
                                           '&hashtags=%s&limit=100&offset=0' % quote_plus(tag)})
    end('files')


def _cam_stream(url):
    found = re.findall(r'''hls_source.+?(http.*?m3u8)''', get(url).text, flags=re.DOTALL)
    return found[0].replace('u002D', '-').replace('\\-', '-').replace('\\u002D', '-').replace('\\', '') if found else None


def cam_favs():
    conn = _db()
    rows = conn.execute('SELECT name, url, image FROM chaturbate').fetchall()
    conn.close()
    if not rows:
        add_action('No favourites yet', {'mode': 'noop'},
                   plot='Open the context menu on a performer in Live XXX Cams and choose Add to favourites.')
    for name, url, image in rows:
        try:
            online = _cam_stream(url) is not None
        except Exception as e:
            log('favourite %s: %s' % (name, e)); online = None
        state = {True: 'online', False: 'offline', None: 'unknown'}[online]
        add_video('%s  (%s)' % (name, state), {'mode': 'play_cam', 'url': url, 'thumb': image}, image,
                  'Currently %s' % state, _cam_context(name, url, image, True))
    end('videos', cache=False)


def cam_fav(url, name, thumb):
    conn = _db()
    if not conn.execute('SELECT 1 FROM chaturbate WHERE url = ?', (url,)).fetchone():
        conn.execute('INSERT INTO chaturbate VALUES (?,?,?)', (name, url, thumb or ''))
        conn.commit()
    conn.close()
    notify('%s added to favourites' % name, thumb or ICON)


def cam_unfav(url, name):
    conn = _db()
    conn.execute('DELETE FROM chaturbate WHERE url = ?', (url,))
    conn.commit(); conn.close()
    notify('%s removed from favourites' % name)
    xbmc.executebuiltin('Container.Refresh')


def play_cam(url, thumb=None):
    stream = _cam_stream(url)
    if not stream:
        notify('This performer is offline')
        return cancel()
    play(stream, thumb)


# --------------------------------------------------------------------------------------- sites

_SOURCES = None


def _sources():
    global _SOURCES
    if _SOURCES is None:
        from scrapers import sources
        _SOURCES = sources()
    return _SOURCES


def _scraper(name):
    for n, s in _sources():
        if n.lower() == name.lower(): return s
    raise KeyError('scraper %s not found' % name)


def sites():
    add_folder('Search All Sites', {'mode': 'search'}, plot='Search every site at once')
    for name, _ in _sources():
        add_folder(name.title(), {'mode': 'site', 'site': name}, plot='Videos from %s' % name.title())
    end('files')


def _video_rows(items, site):
    count = 0
    for info in items or []:
        if not info.get('url'):       # 'Content From X' header rows
            continue
        img = info.get('image') or ICON
        add_video(info.get('name', ''), {'mode': 'play_site', 'site': site, 'url': info['url'], 'thumb': img}, img)
        count += 1
    return count


def site(name, url=''):
    if not url:
        add_folder('Categories', {'mode': 'site_cats', 'site': name}, plot='Browse %s by category' % name.title())
    found = _video_rows(_scraper(name).MainContent(url), name)
    if found:
        try:
            nxt = _scraper(name).GetNextPage(url)
            if nxt: next_page({'mode': 'site', 'site': name, 'url': nxt})
        except Exception as e:
            log('%s next page: %s' % (name, e))
    end('videos')


def site_cats(name):
    for c in _scraper(name).GetCats() or []:
        if c.get('url'):
            add_folder(c.get('name', ''), {'mode': 'site', 'site': name, 'url': c['url']})
    end('files')


def search(query=None):
    if not query:
        query = xbmcgui.Dialog().input('Search all sites')
        if not query or len(query.strip()) < 2:
            return end('videos', ok=False)
        # show the results under their own URL so Back doesn't ask again
        xbmc.executebuiltin('Container.Update(%s)' % build_url(mode='search', q=query.strip()))
        return end('videos', ok=False)
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, 'Searching for %s...' % query)
    total, found = len(_sources()), 0
    for i, (name, scraper) in enumerate(_sources(), 1):
        if progress.iscanceled(): break
        try:
            found += _video_rows(scraper.SearchSite(query), name)
        except Exception as e:
            log('search %s: %s' % (name, e))
        progress.update(int(i * 100 / total), 'Searching %s\nVideos found: %d  |  Sites searched: %d of %d' % (name.title(), found, i, total))
    progress.close()
    if not found: notify('Nothing found for %s' % query)
    end('videos')


def play_site(name, url, thumb=None):
    scrapers = [(_scraper(name))] if name else [s for n, s in _sources() if n.lower() in url.lower()]
    links = []
    for s in scrapers:
        for l in s.ResolveLink(url) or []:
            if l.get('url'): links.append((l.get('name', 'Link'), l['url']))
    stream = choose(links)
    if not stream:
        return cancel()
    play(stream, thumb)


# --------------------------------------------------------------------------------------- router

def cancel():
    if HANDLE >= 0:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem(offscreen=True))


PLAY_MODES = {'play_live', 'play_movie', 'play_cam', 'play_site'}


def router(params):
    mode = params.get('mode')
    url = params.get('url') or None
    thumb = params.get('thumb') or None
    page = int(params.get('page') or 1)
    if mode is None: return root()
    if mode == 'live': return live(url, page)
    if mode == 'play_live': return play_live(url, thumb)
    if mode == 'movies': return movies(url, page)
    if mode == 'movie_studios': return movie_studios()
    if mode == 'play_movie': return play_movie(url, thumb)
    if mode == 'cams': return cams(url)
    if mode == 'cam_tags': return cam_tags()
    if mode == 'cam_favs': return cam_favs()
    if mode == 'cam_fav': return cam_fav(url, params.get('name', ''), thumb)
    if mode == 'cam_unfav': return cam_unfav(url, params.get('name', ''))
    if mode == 'play_cam': return play_cam(url, thumb)
    if mode == 'sites': return sites()
    if mode == 'site': return site(params['site'], url or '')
    if mode == 'site_cats': return site_cats(params['site'])
    if mode == 'search': return search(params.get('q'))
    if mode == 'play_site': return play_site(params.get('site', ''), url, thumb)
    if mode == 'settings': return ADDON.openSettings()
    if mode == 'noop': return
    log('unknown mode %s' % mode, xbmc.LOGWARNING)
    end(ok=False)


def main():
    params = dict(parse_qsl(sys.argv[2][1:] if len(sys.argv) > 2 else ''))
    try:
        router(params)
    except Exception as e:
        log('%s failed :: %s: %s' % (params.get('mode') or 'root', type(e).__name__, e), xbmc.LOGERROR)
        notify('Could not load this right now (site down or changed)')
        if HANDLE >= 0:
            if params.get('mode') in PLAY_MODES:
                cancel()
            else:
                xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)


if __name__ == '__main__':
    main()
