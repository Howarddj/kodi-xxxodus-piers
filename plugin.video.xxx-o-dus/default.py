from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves.urllib.parse import parse_qs, quote_plus, urlparse, parse_qsl
from six import PY2
import sys
import kodi
import re
import urllib
import os
import shutil
import base64
import time
import requests
from resources.lib.modules import downloaderrepo as tools
from resources.lib.modules import extract
from resources.lib.modules import utils
from resources.lib.modules import menus
from resources.lib.modules import parental
from resources.lib.modules import firstStart
from resources.lib.modules import addon_able

# De-obfuscated from the Hyperion-packed original (5.00.028).
# Removed: the pinsystem.co.uk PIN requirement (CheckParent), the unused
# Python 2-only get_pin() helper, and the start-up prompt that downloaded and
# installed repository.StreamArmy from streamarmy.co.uk when it was missing.

translatePath = xbmc.translatePath if PY2 else xbmcvfs.translatePath
parentalCheck = parental.parentalCheck
addon_id = 'plugin.video.xxx-o-dus'
AddonTitle = '[COLOR pink][B]XXX-O-DUS[/B][/COLOR]'
dialog = xbmcgui.Dialog()
settingsxml = translatePath(os.path.join('special://home/userdata/addon_data/' + addon_id, 'settings.xml'))
settingsxml_default = translatePath(os.path.join('special://home/addons/' + addon_id, 'resources/settings_default.xml'))
firstrun = translatePath(os.path.join('special://home/userdata/addon_data/' + addon_id, 'firstrun.txt'))
setupfolders = translatePath(os.path.join('special://home/userdata/addon_data/plugin.video.xxx-o-dus/downloads/'))


def main(argv=None):
    if sys.argv:
        argv = sys.argv
    queries = utils.parse_query(sys.argv[2])
    mode = queries.get('mode', None)
    utils.url_dispatcher.dispatch(mode, queries)
    if kodi.get_setting('dev_debug') == 'true':
        utils.url_dispatcher.showmodes()


if __name__ == '__main__':
    firstStart.run()
    parentalCheck()
    sys.exit(main())
