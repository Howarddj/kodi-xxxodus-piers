# Settings actions: RunScript(service.cumination.bingieposters, apply|rebuild|restore)
import sys

import xbmcaddon
import xbmcgui

from resources.lib import core

NAME = 'Cumination Bingie posters'
action = sys.argv[1] if len(sys.argv) > 1 else 'apply'
dialog = xbmcgui.Dialog()

if action == 'restore':
    n = core.restore()
    xbmcaddon.Addon('service.cumination.bingieposters').setSetting('enabled', 'false')
    dialog.notification(NAME, 'Restored %d original logos (automatic posters turned off)' % n)
else:
    if not core.cumination_version():
        dialog.ok(NAME, 'Cumination is not installed.')
    else:
        progress = xbmcgui.DialogProgressBG()
        progress.create(NAME, 'Building posters...')
        made, kept, skipped = core.apply(force=(action == 'rebuild'))
        progress.close()
        dialog.notification(NAME, 'Posters made: %d, already done: %d, left as is: %d' % (made, kept, skipped))
