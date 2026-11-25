# -*- coding: utf-8 -*-
"""Nemzzy startup service: one-time AdMaven leftover cleanup (update checks and ping removed)."""

import os
import re
import shutil
import stat

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

pattern = r'''<addon\sid=['"](plugin.*?)['"]'''
releasedaddons = []
app_version = "11.01.000"
addon_id = 'script.module.nemzzy'
selfAddon = xbmcaddon.Addon(id=addon_id)
dialog = xbmcgui.Dialog()


def platform_check():
    if xbmc.getCondVisibility('system.platform.android'):
        return 'Android'
    if xbmc.getCondVisibility('system.platform.linux'):
        return 'Linux'
    if xbmc.getCondVisibility('system.platform.tvos'):
        return 'TV OS'
    if xbmc.getCondVisibility('system.platform.windows'):
        return 'Windows'
    if xbmc.getCondVisibility('system.platform.osx'):
        return 'OSX'
    if xbmc.getCondVisibility('system.platform.atv2'):
        return 'AppleTv'
    if xbmc.getCondVisibility('system.platform.xbox'):
        return 'Xbox'
    if xbmc.getCondVisibility('system.platform.ios'):
        return 'IOS'
    if xbmc.getCondVisibility('system.platform.darwin'):
        return 'IOS'
    return 'Unknown Device'


def _force_remove(path):
    try:
        if not os.path.exists(path):
            return
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.chmod(path, stat.S_IWRITE)
            except Exception:
                pass
            os.remove(path)
        xbmc.log("nemzzy cleanup: removed %s" % path, xbmc.LOGINFO)
    except Exception as e:
        xbmc.log("nemzzy cleanup: failed to remove %s: %s" % (path, e), xbmc.LOGWARNING)


def _is_valid_android_package(package_name):
    return bool(re.match(r'^([a-z][a-z0-9_]*\.)+[a-z][a-z0-9_]*$', package_name or ''))


def _android_package_name():
    addon_path = selfAddon.getAddonInfo('path') or ''
    parts = addon_path.split(os.sep)
    try:
        if 'Android' in parts:
            idx = parts.index('Android')
            if len(parts) > idx + 2 and parts[idx + 1].lower() == 'data':
                candidate = parts[idx + 2]
                if _is_valid_android_package(candidate):
                    return candidate
        if 'data' in parts:
            idx = parts.index('data')
            if len(parts) > idx + 1:
                candidate = parts[idx + 1]
                if _is_valid_android_package(candidate):
                    return candidate
    except Exception:
        pass
    if 'org.xbmc.kodi' in addon_path:
        return 'org.xbmc.kodi'
    if 'wizard.red.the' in addon_path:
        return 'wizard.red.the'
    return None


def _android_files_path(package):
    try:
        user_id = os.getuid() // 100000
    except Exception:
        user_id = 0
    primary = '/data/user/%s/%s/files/' % (user_id, package)
    if os.path.exists(primary):
        return primary
    return '/data/data/%s/files/' % package


def _stop_windows_sdk_if_present(dll_path):
    """Best-effort stop of a previously loaded AdMaven DLL before deleting it."""
    if not os.path.exists(dll_path):
        return
    try:
        import ctypes
        from ctypes import wintypes

        lib = ctypes.CDLL(dll_path)
        if hasattr(lib, 'stopNeuNative'):
            lib.stopNeuNative()
        kernel32 = ctypes.WinDLL('kernel32.dll')
        free_library = kernel32.FreeLibrary
        free_library.argtypes = [wintypes.HMODULE]
        free_library.restype = ctypes.c_bool
        free_library(ctypes.cast(lib._handle, wintypes.HMODULE))
    except Exception as e:
        xbmc.log("nemzzy cleanup: stop SDK skipped: %s" % e, xbmc.LOGINFO)


def _delete_windows_reg_key(root, subkey):
    """Recursively delete a Windows registry key (best-effort)."""
    try:
        import winreg

        try:
            handle = winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        except OSError:
            return
        while True:
            try:
                child = winreg.EnumKey(handle, 0)
            except OSError:
                break
            _delete_windows_reg_key(root, subkey + '\\' + child)
        winreg.CloseKey(handle)
        winreg.DeleteKey(root, subkey)
        xbmc.log("nemzzy cleanup: removed registry %s" % subkey, xbmc.LOGINFO)
    except Exception as e:
        xbmc.log("nemzzy cleanup: registry cleanup failed (%s): %s" % (subkey, e), xbmc.LOGWARNING)


def _cleanup_windows_run_values():
    """Remove HKCU Run entries that point at NeuNative / AdMaven leftovers."""
    try:
        import winreg

        run_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            to_delete = []
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                except OSError:
                    break
                blob = ('%s %s' % (name, value)).lower()
                if any(token in blob for token in ('neunative', 'admaven', 'neupop', 'pwack')):
                    to_delete.append(name)
                i += 1
            for name in to_delete:
                try:
                    winreg.DeleteValue(key, name)
                    xbmc.log("nemzzy cleanup: removed Run value %s" % name, xbmc.LOGINFO)
                except OSError as e:
                    xbmc.log("nemzzy cleanup: failed removing Run value %s: %s" % (name, e), xbmc.LOGWARNING)
    except Exception as e:
        xbmc.log("nemzzy cleanup: Run key scan failed: %s" % e, xbmc.LOGWARNING)


def cleanup_admaven_leftovers():
    """Remove files/registry previous AdMaven/NeuNative builds left on the device."""
    try:
        # Addon-profile settings written by the old SDK helpers
        profile = xbmcvfs.translatePath(selfAddon.getAddonInfo('profile'))
        _force_remove(os.path.join(profile, 'settings.json'))

        if xbmc.getCondVisibility('system.platform.windows'):
            import winreg

            localappdata = os.getenv('LOCALAPPDATA') or os.path.expanduser('~')
            appdata = os.getenv('APPDATA') or localappdata
            tempdir = os.getenv('TEMP') or os.getenv('TMP') or ''

            # Primary install dir used by this addon + SDK config/log files
            neunative_dir = os.path.join(localappdata, 'Neunative')
            dll_path = os.path.join(neunative_dir, 'NeunativeWin.dll')
            _stop_windows_sdk_if_present(dll_path)
            for name in (
                'NeunativeWin.dll',
                'NeunativeWinNew.dll',
                'neupop.log',
                'NeuNative.log',
                'neunative.txt',
            ):
                _force_remove(os.path.join(neunative_dir, name))
            _force_remove(neunative_dir)

            # Related NeuNative-M style installs (same family; not from this addon,
            # but safe to clear if present so devices are fully cleaned).
            for base in (localappdata, appdata):
                _force_remove(os.path.join(base, 'neunative-m'))
                _force_remove(os.path.join(base, 'Neunative-m'))

            if tempdir:
                _force_remove(os.path.join(tempdir, 'NeuNative.log'))
                _force_remove(os.path.join(tempdir, 'neunative.txt'))

            # Device UUID / enrollment state written by the SDK
            _delete_windows_reg_key(winreg.HKEY_CURRENT_USER, r'Software\Neunative')
            _delete_windows_reg_key(winreg.HKEY_CURRENT_USER, r'Software\NeuNative')
            _cleanup_windows_run_values()

        if xbmc.getCondVisibility('system.platform.android'):
            package = _android_package_name()
            if package:
                files_path = _android_files_path(package)
                try:
                    for name in os.listdir(files_path):
                        lower = name.lower()
                        if (
                            (name.startswith('libnativesdk-') and name.endswith('.so'))
                            or lower in ('neunative.txt', 'neunative.log')
                            or 'neunative' in lower
                        ):
                            _force_remove(os.path.join(files_path, name))
                except Exception as e:
                    xbmc.log("nemzzy cleanup: android list failed: %s" % e, xbmc.LOGWARNING)
                _force_remove(os.path.join(files_path, addon_id))
                # Also clear any Neunative-named data dirs under app files
                _force_remove(os.path.join(files_path, 'Neunative'))
                _force_remove(os.path.join(files_path, 'neunative'))
    except Exception as e:
        xbmc.log("nemzzy cleanup: unexpected error: %s" % e, xbmc.LOGWARNING)


def nemzzy():
    cleanup_admaven_leftovers()
    # Removed: per-start version check against the Stream Army repo index ("Addon X Needs
    # Updating" notifications) and the pincheck registration / usage ping to streamarmy.co.uk.


if __name__ == "__main__":
    nemzzy()
