# Cumlouder for XXX-O-DUS: site engine carried over from Cum With Me (cwm_engines/Cumlouder.py)
import os
from resources.lib.modules import utils
from cwm_engines import adapter

filename     = os.path.basename(__file__).split('.')[0]
base_domain  = 'https://www.cumlouder.com'
base_name    = 'Cumlouder'
type         = 'video'
menu_mode    = 608
content_mode = 609
player_mode  = 610

search_tag   = 1
search_base  = adapter.SEARCH + '%s'


@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    adapter.menu('Cumlouder', filename, base_name, content_mode)


@utils.url_dispatcher.register('%s' % content_mode, ['url'], ['searched'])
def content(url, searched=False):
    return adapter.content('Cumlouder', filename, base_name, content_mode, player_mode, url, searched)


@utils.url_dispatcher.register('%s' % player_mode, ['url'], ['name', 'iconimage'])
def player(url, name=None, iconimage=None):
    adapter.play('Cumlouder', base_name, url, name, iconimage)
