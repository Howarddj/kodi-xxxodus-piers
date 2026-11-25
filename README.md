# XXX-O-DUS for Kodi 22 "Piers"

A Kodi repository with XXX-O-DUS and every non-official add-on it depends on, patched to run on Kodi 22 (Python 3.14).

## Install

1. In Kodi go to **Settings → File manager → Add source** and enter
   `https://raw.githubusercontent.com/Howarddj/kodi-xxxodus-piers/main/`
   (or download `repository.xxxodus.piers-1.0.0.zip` from this repo).
2. **Add-ons → Install from zip file** → pick `repository.xxxodus.piers-1.0.0.zip`.
3. **Add-ons → Install from repository → XXX-O-DUS Piers Repository → Video add-ons → XXX-O-DUS**.
   Kodi installs all dependencies automatically.

If you already installed an earlier patched build, step 3 shows XXX-O-DUS 99.00.030 as an update.

## What's in the repository

| Add-on | Version | Source | Changes |
|---|---|---|---|
| `plugin.video.xxx-o-dus` | 99.00.030 | Stream Army 5.00.028 | Patched (see below) |
| `script.module.echo` | 99.00.001 | Stream Army 5.00.000 | Patched |
| `script.xxxodus.scrapers` | 99.00.021 | Stream Army 5.00.020 | Patched |
| `script.module.nemzzy` | 99.00.000 | Stream Army 12.00.000 | Patched |
| `script.xxxodus.artwork` | 5.00.001 | Stream Army | Unchanged |
| `script.module.resolveurl` | 5.1.214 | Gujal00 | Unchanged |
| `script.module.resolveurl.xxx` | 2.1.44 | Gujal00 | Unchanged |
| `repository.xxxodus.piers` | 1.0.0 | — | This repository |

The repository add-on also points at Gujal00's upstream ResolveURL repository, so ResolveURL and ResolveURL-XXX keep updating.
The other required modules (`requests`, `six`, `kodi-six`, `beautifulsoup4`, `html5lib`, `pyxbmct`, `inputstreamhelper`, `pyqrcode`) come from Kodi's official repository.

The patched add-ons use version 99 so Stream Army releases never replace them, and XXX-O-DUS requires those minimum versions so Kodi always uses the patched modules.

## Changes

* **Kodi 22 / Python 3.14:** replaced `urllib.request.FancyURLopener`, which Python 3.14 removed and which crashed the add-on at start-up.
* **Python 3 / Kodi 19+ bugs** that were already breaking parts of the add-on on Kodi 19–21:
  * HTML entity decoding in every scraper (`HTMLParser().unescape`)
  * the cache (`hashlib` on `str`, `xbmc.translatePath`)
  * downloads (progress-dialog signatures and float percentages)
  * parental-control passwords (`hashlib` on `str`)
  * the Chaturbate monitor service (`xbmc.abortRequested`, `LOGNOTICE`, a missing `requests` import)
  * the scraper loader (`find_module` was removed in Python 3.12)
  * `ListItem(iconImage=…)`
  * `Dialog().ok()` with three lines
  * the Python 2-only `extract`, `downloader`, `githubissues` and `plugintools` modules
* **Removed:**
  * the `pinsystem.co.uk` PIN gate
  * the per-scraper online version check that quit on a mismatch
  * the start-up prompt to install `repository.StreamArmy`
  * the Stream Army registration and usage ping, and the update notifications, in `script.module.nemzzy`
  * the online part of the "Check XXX-O-DUS Health" screen, which now only shows installed versions
* **Kept:** the first-run 18+ confirmation and the optional parental-control lock.
* **Readable source:** the obfuscated `default.py`, `menus.py` and `lover.py` were replaced with readable source.

`patches/xxx-o-dus-all-changes.diff` has every change; for formerly obfuscated files it compares against the decoded originals.

## Rebuilding

After editing an add-on, bump its version in `addon.xml`, then run:

```
python3 tools/build_repo.py
```

This regenerates `zips/`, `zips/addons.xml`, `zips/addons.xml.md5` and the repository zip in the root. Repo owner, name and branch live in `repo.json` (`python3 tools/build_repo.py --owner NAME --repo REPO` updates them).

## Licence

The add-ons are GPL-3.0 (see `LICENSE` and each add-on's own licence file).
