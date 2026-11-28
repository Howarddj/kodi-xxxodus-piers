# XXX-O-DUS for Kodi 22 "Piers"

A Kodi repository with XXX-O-DUS and every non-official add-on it depends on, patched to run on Kodi 22 / 23 (Python 3.14).

## Install

1. In Kodi go to **Settings → File manager → Add source** and enter
   `https://raw.githubusercontent.com/Howarddj/kodi-xxxodus-piers/main/`
   (or download `repository.xxxodus.piers-1.0.0.zip` from this repo).
2. **Add-ons → Install from zip file** → pick `repository.xxxodus.piers-1.0.0.zip`.
3. **Add-ons → Install from repository → XXX-O-DUS Piers Repository → Video add-ons → XXX-O-DUS**.
   Kodi installs all dependencies automatically.

If you already installed an earlier patched build, step 3 shows XXX-O-DUS 99.00.036 as an update.

## What's in the repository

| Add-on | Version | Source | Changes |
|---|---|---|---|
| `plugin.video.xxx-o-dus` | 99.00.038 | Stream Army 5.00.028 | Patched (see below) |
| `script.module.echo` | 99.00.003 | Stream Army 5.00.000 | Patched |
| `script.xxxodus.scrapers` | 99.00.024 | Stream Army 5.00.020 | Patched; 11 sites added from Cum With Me |
| `script.module.nemzzy` | 99.00.000 | Stream Army 12.00.000 | Patched |
| `script.xxxodus.artwork` | 99.00.003 | Stream Army 5.00.001 | Icons restyled (smaller, centred, rounded) |
| `script.module.resolveurl` | 5.1.214 | Gujal00 | Unchanged |
| `script.module.resolveurl.xxx` | 2.1.44 | Gujal00 | Unchanged |
| `service.cumination.bingieposters` | 1.1.0 | New | Fixes Cumination site logos in Bingie poster views |
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
* **Found by a sandbox test run** (a stub Kodi 23 on Python 3.14 that opens every menu, search and tool, with sites down and with sites returning blank pages):
  * listings that stopped with `quit()` after a site error now tell Kodi the listing failed, so Kodi returns to the previous screen instead of a spinner and a blank list
  * `echo`'s `client.request()` ignored every option (`output='headers'`, `geturl`, `cookie`, `referer`, custom headers), so downloads and some resolvers always failed
  * Watch History was never written for sites that play straight from the resolver
  * the Chaturbate monitor database was written to `plugin.video.XXX-O-DUS`, a different folder from the one it is read from on Linux
  * SQL deletes built by string formatting failed on names containing an apostrophe
  * the default download folder was a Windows path
  * `XBMC.`-prefixed built-ins, which Kodi 19+ ignores
* **99.00.037:**
  * 11 sites merged from Cum With Me (see below)
  * Monitored Performers and its online alerts fixed
  * the first-run `bit.ly` install counter removed, along with three unused links to outside servers
  * the only outside list still fetched is the "sexmovies" section's own pastebin page
* **99.00.038** (from a user's kodi.log):
  * Live XXX Channels, Pandamovies (now `.pw`), Watchpornfree (now `.info`), Freeomovie Next Page and the Chaturbate menus fixed
  * pages that are UK age-verification gates or Cloudflare country blocks are recognised and reported as such, and are no longer written to the log in full
  * in the UK, Aylo's sites (Pornhub, Pornhub Gay, YouPorn, Redtube, Tube8, Thumbzilla) refuse visitors without an account verified before 2 February 2026; no add-on change can get round that
* **Kept:** the first-run 18+ confirmation and the optional parental-control lock.
* **Readable source:** the obfuscated `default.py`, `menus.py` and `lover.py` were replaced with readable source.

`patches/xxx-o-dus-all-changes.diff` has every change; for formerly obfuscated files it compares against the decoded originals.

## Cum With Me (merged and removed)

Cum With Me was added in this repository's history and later dropped. Its 11 sites that XXX-O-DUS lacked are now XXX-O-DUS Tubes, with their site code in `script.xxxodus.scrapers/lib/cwm_engines/`. Its other sources (the live-channel site, Chaturbate, Pandamovies and 9 tube sites) were already in XXX-O-DUS, and so was its main feature, favourite performers with online alerts (Live Cams → Monitored Performers). If you installed it, uninstall it from **Video add-ons**: it will receive no further updates.

## Cumination Bingie posters

`service.cumination.bingieposters` (Program add-ons → Cumination Bingie posters) fixes how Cumination's site logos look in Bingie's poster views. The logos are wide banners, and the poster views stretch or crop them into a 2:3 frame. The add-on turns each PNG and JPEG logo in your installed Cumination into a 2:3 poster: the logo is centred without distortion on a card matching its background, and small logos are enlarged smoothly.

- It checks once when Kodi starts and once each time you open Cumination, so it re-applies after Cumination updates (and refreshes the open list when it does). Otherwise it does nothing.
- It clears Kodi's cached thumbnails for those images, so the new posters show at once.
- Your original images are backed up to the add-on's data folder. Settings has **Apply now**, **Rebuild all** and **Restore original logos**. Restore also turns the add-on off.
- PNG logos stay PNG and JPEG logos stay JPEG; the one GIF and two WebP logos are left as they are.
- Cumination itself is not modified apart from its image files, and it comes from its own repository (dobbelina).

## Rebuilding

After editing an add-on, bump its version in `addon.xml`, then run:

```
python3 tools/build_repo.py
```

This regenerates `zips/`, `zips/addons.xml`, `zips/addons.xml.md5` and the repository zip in the root. Repo owner, name and branch live in `repo.json` (`python3 tools/build_repo.py --owner NAME --repo REPO` updates them).

## Licence

The add-ons are GPL-3.0 (see `LICENSE` and each add-on's own licence file).
