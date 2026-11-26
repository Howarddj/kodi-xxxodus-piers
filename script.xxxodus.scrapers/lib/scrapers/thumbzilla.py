# Thumbzilla for XXX-O-DUS: site engine carried over from Cum With Me (cwm_engines/Thumbzilla.py)
import os
from resources.lib.modules import utils
from cwm_engines import adapter

filename     = os.path.basename(__file__).split('.')[0]
base_domain  = 'https://www.thumbzilla.com'
base_name    = 'Thumbzilla'
type         = 'video'
menu_mode    = 636
content_mode = 637
player_mode  = 638

search_tag   = 1
search_base  = adapter.SEARCH + '%s'


@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    adapter.menu('Thumbzilla', filename, base_name, content_mode)


@utils.url_dispatcher.register('%s' % content_mode, ['url'], ['searched'])
def content(url, searched=False):
    return adapter.content('Thumbzilla', filename, base_name, content_mode, player_mode, url, searched)


@utils.url_dispatcher.register('%s' % player_mode, ['url'], ['name', 'iconimage'])
def player(url, name=None, iconimage=None):
    adapter.play('Thumbzilla', base_name, url, name, iconimage)
