# Cliphunter for XXX-O-DUS: site engine carried over from Cum With Me (cwm_engines/Cliphunter.py)
import os
from resources.lib.modules import utils
from cwm_engines import adapter

filename     = os.path.basename(__file__).split('.')[0]
base_domain  = 'https://www.cliphunter.com'
base_name    = 'Cliphunter'
type         = 'video'
menu_mode    = 604
content_mode = 605
player_mode  = 606

search_tag   = 1
search_base  = adapter.SEARCH + '%s'


@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    adapter.menu('Cliphunter', filename, base_name, content_mode)


@utils.url_dispatcher.register('%s' % content_mode, ['url'], ['searched'])
def content(url, searched=False):
    return adapter.content('Cliphunter', filename, base_name, content_mode, player_mode, url, searched)


@utils.url_dispatcher.register('%s' % player_mode, ['url'], ['name', 'iconimage'])
def player(url, name=None, iconimage=None):
    adapter.play('Cliphunter', base_name, url, name, iconimage)
