# Background service: checks Cumination's site logos once when Kodi starts and once each time Cumination is
# opened (that is when a Cumination update will have replaced them). Between those it only watches which
# add-on the current list belongs to, which costs nothing.
import xbmc

from resources.lib import core

START_DELAY = 10        # seconds: let Kodi finish starting up
WATCH_EVERY = 1         # seconds between looks at Container.PluginName


class Monitor(xbmc.Monitor):
    def __init__(self):
        super(Monitor, self).__init__()
        self.settings_changed = False

    def onSettingsChanged(self):
        self.settings_changed = True


def check(monitor, refresh=False):
    """Make posters if Cumination's images changed since our last run."""
    if not core.enabled():
        return
    fp = core.fingerprint()
    if not fp or fp == core._load_state().get('fingerprint'):
        return
    if not core.acquire():
        return                                  # the settings action is already doing it
    try:
        made = core.apply(monitor=monitor)[0]
    except Exception as e:
        core.log('apply failed: %s' % e, xbmc.LOGERROR)
        made = 0
    finally:
        core.release()
    if made and refresh and xbmc.getInfoLabel('Container.PluginName') == core.TARGET_ID:
        xbmc.executebuiltin('Container.Refresh')   # show the new posters in the list that's open


def main():
    monitor = Monitor()
    if monitor.waitForAbort(START_DELAY):
        return
    check(monitor)
    was_enabled = core.enabled()
    inside = False
    while not monitor.waitForAbort(WATCH_EVERY):
        if monitor.settings_changed:            # turned back on: catch up straight away
            monitor.settings_changed = False
            now_enabled = core.enabled()
            if now_enabled and not was_enabled:
                check(monitor)
            was_enabled = now_enabled
        opened = xbmc.getInfoLabel('Container.PluginName') == core.TARGET_ID
        if opened and not inside:
            check(monitor, refresh=True)
        inside = opened


if __name__ == '__main__':
    main()
