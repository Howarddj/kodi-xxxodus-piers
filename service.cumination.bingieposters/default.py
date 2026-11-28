# Settings actions: RunScript(service.cumination.bingieposters, apply|rebuild|restore)
import sys

import xbmcaddon
import xbmcgui

from resources.lib import core

NAME = 'Cumination Bingie posters'


def main(action):
    dialog = xbmcgui.Dialog()
    if not core.cumination_version():
        dialog.ok(NAME, 'Cumination is not installed.')
        return
    if not core.acquire():
        dialog.notification(NAME, 'Already working, try again in a moment')
        return
    try:
        if action == 'restore':
            n = core.restore()
            xbmcaddon.Addon(core.ADDON_ID).setSetting('enabled', 'false')
            dialog.notification(NAME, 'Restored %d original logos (automatic posters turned off)' % n)
            return
        progress = xbmcgui.DialogProgressBG()
        progress.create(NAME, 'Building posters...')
        try:
            made, kept, skipped = core.apply(force=(action == 'rebuild'))
        finally:
            progress.close()
        dialog.notification(NAME, 'Posters made: %d, already done: %d, left as is: %d' % (made, kept, skipped))
    finally:
        core.release()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'apply')
