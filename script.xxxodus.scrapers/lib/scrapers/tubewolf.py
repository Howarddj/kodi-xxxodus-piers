# TubeWolf for XXX-O-DUS: site engine carried over from Cum With Me (cwm_engines/Tubewolf.py)
import os
from resources.lib.modules import utils
from cwm_engines import adapter

filename     = os.path.basename(__file__).split('.')[0]
base_domain  = 'https://www.tubewolf.com'
base_name    = 'TubeWolf'
type         = 'video'
menu_mode    = 640
content_mode = 641
player_mode  = 642

search_tag   = 1
search_base  = adapter.SEARCH + '%s'


@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    adapter.menu('Tubewolf', filename, base_name, content_mode)


@utils.url_dispatcher.register('%s' % content_mode, ['url'], ['searched'])
def content(url, searched=False):
    return adapter.content('Tubewolf', filename, base_name, content_mode, player_mode, url, searched)


@utils.url_dispatcher.register('%s' % player_mode, ['url'], ['name', 'iconimage'])
def player(url, name=None, iconimage=None):
    adapter.play('Tubewolf', base_name, url, name, iconimage)
