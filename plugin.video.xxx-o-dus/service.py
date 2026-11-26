from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves.urllib.parse import parse_qs, quote_plus, urlparse, parse_qsl, unquote_plus
from six import PY2
import  re, os, time, urllib
import requests  # was used below but never imported
import sqlite3
translatePath = xbmc.translatePath if PY2 else xbmcvfs.translatePath

try:
    addon = xbmcaddon.Addon()
    get_setting = addon.getSetting
    databases = translatePath(os.path.join('special://profile/addon_data/plugin.video.xxx-o-dus', 'databases'))
    chaturbatedb = translatePath(os.path.join(databases, 'chaturbate.db'))

    xbmc.log('Starting XXX-O-DUS Service', xbmc.LOGINFO)

    if ( not os.path.exists(databases)): os.makedirs(databases)
    conn = sqlite3.connect(chaturbatedb)
    c = conn.cursor()
    try:
        c.executescript("CREATE TABLE IF NOT EXISTS chaturbate (name, url, image);")
    except:
        pass
    conn.close()

    i = 0
    j = 0

    chat_on_off = 'false'
    chat_on_off  = get_setting("chaturbate_start")

    if ( chat_on_off ) != 'true': 
        xbmc.log('Exiting XXX-O-DUS Service', xbmc.LOGINFO)
        quit()

    time.sleep(10)

    lst = []

    xbmc.log('Starting XXX-O-DUS Chaturbate Monitoring', xbmc.LOGINFO)

    monitor = xbmc.Monitor()  # xbmc.abortRequested was removed in Kodi 19
    while not monitor.abortRequested():

        if not i:
            #xbmc.log('Getting Chaturbate Monitored Performers from XXX-O-DUS', xbmc.LOGINFO)
            conn = sqlite3.connect(chaturbatedb)
            conn.text_factory = str
            c = conn.cursor()
            c.execute("SELECT * FROM chaturbate")
            e = [u for u in c.fetchall()]
            conn.close()
            if len(e) < 1:
                # nobody monitored yet: keep running so performers added later are still checked
                if monitor.waitForAbort(60): break
                continue
            for (title, link, iconimage) in e:
                if (not title in str(lst) ):
                    #xbmc.log('XXX-O-DUS: Checking %s' % title, xbmc.LOGINFO)
                    try:
                        r = requests.get(link, timeout=15).text
                        # req = urllib2.Request(link)
                        # response = urllib2.urlopen(req, timeout = 10)
                        # r=response.read()
                        # response.close()
                        if '.m3u8' in r:
                            # the room subject is optional: a missing one used to cancel the alert
                            subj = re.compile('default_subject:\\s\"([^,]+)",').findall(r)
                            content = unquote_plus(subj[0]) if subj else 'is online now'
                            try: content=content.encode('utf-8') if PY2 else content
                            except: content=content
                            xbmcgui.Dialog().notification(title + ' online!',content, iconimage, 7500, True)
                            lst.append(title)
                            xbmc.sleep(3500)
                    except: pass

        if monitor.waitForAbort(5): break

        if j >= 2879:   # was 'i', which only counts to 59: alerts never re-armed
            lst = []
            xbmc.log('XXX-O-DUS: Reseting Checked List', xbmc.LOGINFO)
        i = (i + 1) % 60
        j = (j + 1) % 2880
except: pass