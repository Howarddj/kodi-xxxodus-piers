# Swap Cumination's wide site logos for 2:3 posters, keep the originals, and redo it after Cumination updates.
# PNG logos stay PNG and JPEG logos stay JPEG (Kodi picks its image decoder from the file extension).
import hashlib
import json
import os
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib import jpeg, png, poster

ADDON_ID = 'service.cumination.bingieposters'
TARGET_ID = 'plugin.video.cumination'
IMG_DIR = xbmcvfs.translatePath('special://home/addons/%s/resources/images' % TARGET_ID)
DATA = xbmcvfs.translatePath('special://profile/addon_data/service.cumination.bingieposters')
BACKUP = os.path.join(DATA, 'originals')
STATE = os.path.join(DATA, 'state.json')
MAX_PIXELS = 4000 * 4000                       # site logos are tiny; refuse anything absurd
BUSY = ADDON_ID + '.busy'                      # home-window property: one run at a time (service vs settings)


def enabled():
    return xbmcaddon.Addon(ADDON_ID).getSetting('enabled') != 'false'


def acquire():
    home = xbmcgui.Window(10000)
    if home.getProperty(BUSY):
        return False
    home.setProperty(BUSY, 'true')
    return True


def release():
    xbmcgui.Window(10000).clearProperty(BUSY)


def _codec(data):
    if data.startswith(png.SIG):
        return png
    if data.startswith(jpeg.SIG):
        return jpeg
    return None


def _write(path, data):
    tmp = path + '.bingie.tmp'
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, path)


def log(msg, level=xbmc.LOGINFO):
    xbmc.log('[Cumination Bingie posters] %s' % msg, level)


def _md5(data):
    return hashlib.md5(data).hexdigest()


def _load_state():
    try:
        with open(STATE) as fh:
            return json.load(fh)
    except (IOError, OSError, ValueError):
        return {'files': {}}


def _save_state(state):
    if not os.path.isdir(DATA):
        os.makedirs(DATA)
    tmp = STATE + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(state, fh, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def cumination_version():
    try:
        return xbmcaddon.Addon(TARGET_ID).getAddonInfo('version')
    except Exception:
        return None


def fingerprint():
    """Cheap change check: Cumination's version plus the images folder's listing and mtimes."""
    if not os.path.isdir(IMG_DIR):
        return None
    parts = [cumination_version() or '']
    for f in sorted(os.listdir(IMG_DIR)):
        try:
            parts.append('%s:%d' % (f, int(os.path.getmtime(os.path.join(IMG_DIR, f)))))
        except OSError:
            pass
    return _md5('|'.join(parts).encode())


def _clear_textures():
    """Make Kodi forget its cached copies of Cumination's images (JSON-RPC Textures API)."""
    req = {'jsonrpc': '2.0', 'id': 1, 'method': 'Textures.GetTextures',
           'params': {'properties': ['url'], 'filter': {'field': 'url', 'operator': 'contains', 'value': TARGET_ID}}}
    try:
        res = json.loads(xbmc.executeJSONRPC(json.dumps(req)))
        textures = (res.get('result') or {}).get('textures') or []
    except Exception as e:
        log('could not list cached textures: %s' % e, xbmc.LOGWARNING)
        return 0
    textures = [t for t in textures                  # Windows paths use backslashes
                if 'resources/images' in (t.get('url') or '').replace('\\', '/')]
    for t in textures:
        xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Textures.RemoveTexture',
                                        'params': {'textureid': t['textureid']}}))
    return len(textures)


def apply(force=False, monitor=None):
    """Poster-ise every PNG/JPEG logo that isn't one of ours yet. Returns (made, kept, skipped)."""
    if not os.path.isdir(IMG_DIR):
        log('Cumination is not installed (%s missing)' % IMG_DIR)
        return 0, 0, 0
    state = _load_state()
    files = state.setdefault('files', {})
    try:
        if not os.path.isdir(BACKUP):
            os.makedirs(BACKUP)
    except OSError as e:
        log('cannot create %s: %s' % (BACKUP, e), xbmc.LOGERROR)
        return 0, 0, 0
    made = kept = skipped = 0
    started = time.time()
    for name in sorted(os.listdir(IMG_DIR)):
        if monitor is not None and monitor.abortRequested():
            break
        path = os.path.join(IMG_DIR, name)
        if not os.path.isfile(path) or name.endswith('.bingie.tmp'):
            continue
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
        except (IOError, OSError) as e:
            skipped += 1
            log('%s: cannot read (%s)' % (name, e), xbmc.LOGWARNING)
            continue
        digest = _md5(data)
        entry = files.get(name, {})
        if not force and digest == entry.get('poster_md5'):
            kept += 1                                   # already our poster
            continue
        if _codec(data) is None:
            skipped += 1                                # GIF/WebP: no pure-Python decoder here
            files[name] = {'skipped': 'not a PNG or JPEG'}
            continue
        if force and digest == entry.get('poster_md5'):
            try:
                with open(os.path.join(BACKUP, name), 'rb') as fh:
                    data = fh.read()                    # rebuild from the backed-up original
                digest = _md5(data)
            except (IOError, OSError):
                kept += 1
                continue
        codec = _codec(data)
        try:
            if codec is None:
                raise ValueError('backup is not a PNG or JPEG')
            w, h, px = codec.read(data)
            if w * h > MAX_PIXELS:
                raise ValueError('too large (%dx%d)' % (w, h))
            cw, ch, rgb = poster.make(w, h, px)
            out = codec.write_rgb(cw, ch, rgb)
        except Exception as e:
            skipped += 1
            files[name] = {'skipped': str(e)}
            log('%s: left as is (%s)' % (name, e))
            continue
        try:
            _write(os.path.join(BACKUP, name), data)    # original first, so restore always works
            _write(path, out)
        except (IOError, OSError) as e:
            skipped += 1
            log('%s: cannot write (%s)' % (name, e), xbmc.LOGWARNING)
            continue
        files[name] = {'orig_md5': digest, 'poster_md5': _md5(out), 'size': [cw, ch]}
        made += 1
    state['cumination_version'] = cumination_version()
    state['fingerprint'] = fingerprint()
    try:
        _save_state(state)
    except (IOError, OSError) as e:
        log('cannot save state: %s' % e, xbmc.LOGERROR)
    cleared = _clear_textures() if made else 0
    log('posters made: %d, already done: %d, left as is: %d, cached thumbnails cleared: %d (%.1fs)'
        % (made, kept, skipped, cleared, time.time() - started))
    return made, kept, skipped


def restore():
    """Put Cumination's original images back."""
    state = _load_state()
    restored = 0
    for name, entry in state.get('files', {}).items():
        src, dst = os.path.join(BACKUP, name), os.path.join(IMG_DIR, name)
        if 'poster_md5' not in entry or not os.path.isfile(src) or not os.path.isfile(dst):
            continue
        try:
            with open(dst, 'rb') as fh:
                if _md5(fh.read()) != entry['poster_md5']:
                    continue                            # Cumination replaced it since: leave theirs
            with open(src, 'rb') as fh:
                _write(dst, fh.read())
            restored += 1
        except (IOError, OSError) as e:
            log('%s: cannot restore (%s)' % (name, e), xbmc.LOGWARNING)
    try:
        _save_state({'files': {}})
    except (IOError, OSError) as e:
        log('cannot save state: %s' % e, xbmc.LOGERROR)
    cleared = _clear_textures()
    log('restored %d original images, cleared %d cached thumbnails' % (restored, cleared))
    return restored
