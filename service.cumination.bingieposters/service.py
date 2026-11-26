# Background service: keeps Cumination's site logos in poster format, including after Cumination updates.
import xbmc
import xbmcaddon

from resources.lib import core

CHECK_EVERY = 30 * 60   # seconds; Cumination updates replace its images folder


class Monitor(xbmc.Monitor):
    def __init__(self):
        super(Monitor, self).__init__()
        self.settings_changed = False

    def onSettingsChanged(self):
        self.settings_changed = True


def enabled():
    return xbmcaddon.Addon('service.cumination.bingieposters').getSetting('enabled') != 'false'


def main():
    monitor = Monitor()
    if monitor.waitForAbort(15):            # let Kodi finish starting up
        return
    last = None
    while not monitor.abortRequested():
        if enabled():
            fp = core.fingerprint()
            if fp and fp != last and fp != core._load_state().get('fingerprint'):
                core.apply(monitor=monitor)
            last = core.fingerprint()
        monitor.settings_changed = False
        if monitor.waitForAbort(CHECK_EVERY):
            break


if __name__ == '__main__':
    main()
