# MrDeepFakes for XXX-O-DUS: site engine carried over from Cum With Me (cwm_engines/Mrdeepfakes.py)
import os
from resources.lib.modules import utils
from cwm_engines import adapter

filename     = os.path.basename(__file__).split('.')[0]
base_domain  = 'https://mrdeepfakes.com'
base_name    = 'MrDeepFakes'
type         = 'video'
menu_mode    = 616
content_mode = 617
player_mode  = 618

search_tag   = 1
search_base  = adapter.SEARCH + '%s'


@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    adapter.menu('Mrdeepfakes', filename, base_name, content_mode)


@utils.url_dispatcher.register('%s' % content_mode, ['url'], ['searched'])
def content(url, searched=False):
    return adapter.content('Mrdeepfakes', filename, base_name, content_mode, player_mode, url, searched)


@utils.url_dispatcher.register('%s' % player_mode, ['url'], ['name', 'iconimage'])
def player(url, name=None, iconimage=None):
    adapter.play('Mrdeepfakes', base_name, url, name, iconimage)
