# XXX-O-DUS and Cum With Me for Kodi 22 "Piers"

A Kodi repository with XXX-O-DUS, Cum With Me and every non-official add-on they depend on, patched to run on Kodi 22 / 23 (Python 3.14).

## Install

1. In Kodi go to **Settings → File manager → Add source** and enter
   `https://raw.githubusercontent.com/Howarddj/kodi-xxxodus-piers/main/`
   (or download `repository.xxxodus.piers-1.0.0.zip` from this repo).
2. **Add-ons → Install from zip file** → pick `repository.xxxodus.piers-1.0.0.zip`.
3. **Add-ons → Install from repository → XXX-O-DUS Piers Repository → Video add-ons → XXX-O-DUS**.
   Kodi installs all dependencies automatically.
   Cum With Me is in the same place: **Video add-ons → Cum With Me**.

If you already installed an earlier patched build, step 3 shows XXX-O-DUS 99.00.036 as an update.

## What's in the repository

| Add-on | Version | Source | Changes |
|---|---|---|---|
| `plugin.video.xxx-o-dus` | 99.00.036 | Stream Army 5.00.028 | Patched (see below) |
| `script.module.echo` | 99.00.002 | Stream Army 5.00.000 | Patched |
| `script.xxxodus.scrapers` | 99.00.022 | Stream Army 5.00.020 | Patched |
| `script.module.nemzzy` | 99.00.000 | Stream Army 12.00.000 | Patched |
| `script.xxxodus.artwork` | 99.00.002 | Stream Army 5.00.001 | Icons restyled (smaller, centred, rounded) |
| `plugin.video.cwm` (Cum With Me) | 99.01.000 | Stream Army 2.00.000 | Rebuilt as a Kodi list add-on (see below) |
| `script.cwm.scrapers` | 99.00.016 | Stream Army 1.00.014 | Patched |
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
* **Found by a sandbox test run** (a stub Kodi 23 on Python 3.14 that opens every menu, search and tool, with sites down and with sites returning blank pages):
  * listings that stopped with `quit()` after a site error now tell Kodi the listing failed, so Kodi returns to the previous screen instead of a spinner and a blank list
  * `echo`'s `client.request()` ignored every option (`output='headers'`, `geturl`, `cookie`, `referer`, custom headers), so downloads and some resolvers always failed
  * Watch History was never written for sites that play straight from the resolver
  * the Chaturbate monitor database was written to `plugin.video.XXX-O-DUS`, a different folder from the one it is read from on Linux
  * SQL deletes built by string formatting failed on names containing an apostrophe
  * the default download folder was a Windows path
  * `XBMC.`-prefixed built-ins, which Kodi 19+ ignores
* **Kept:** the first-run 18+ confirmation and the optional parental-control lock.
* **Readable source:** the obfuscated `default.py`, `menus.py` and `lover.py` were replaced with readable source.

`patches/xxx-o-dus-all-changes.diff` has every change; for formerly obfuscated files it compares against the decoded originals.

## Cum With Me changes

Cum With Me 99.01.000 is a rebuild of Stream Army's 2.00.000 as a **normal Kodi list add-on**. The original was a full-screen pyxbmct window with its own artwork. Now every screen is an ordinary folder listing, so your skin controls the views, fonts, colours, artwork and background, as with any other video add-on.

* **Menus:**
  * **Live XXX Channels**
  * **Live XXX Cams:** Favourites, Tags, and an alerts on/off row; add or remove favourites from the context menu
  * **XXX Movies:** plus Studios
  * **XXX Sites:** 20 sites, each with Categories, plus Search All Sites
  * **Settings**
* Every list has a Next Page item; videos play through Kodi's normal `setResolvedUrl`, and a source picker appears when a video has several links.
* **No Stream Army servers are contacted.**
  * Removed: the `pinsystem.co.uk` PIN gate, user-ID registration, chat room, notice text, "online" counters and online version check.
  * The scrapers' default thumbnail was loaded from Stream Army's GitHub; it is now the add-on's own icon.
  * `script.module.nemzzy` is no longer a requirement (Cum With Me never used it).
  * The only hosts contacted are the video sites themselves (and the hosts ResolveURL resolves).
* **Kept:** favourite performers and the optional "performer is online" alert service, which checks Chaturbate only.
* **Fixes carried over from 99.00.001:**
  * scraper loader for Python 3.12+ (0 of 20 sites loaded before)
  * timeouts on every request
  * site errors show a message and Kodi goes back instead of hanging
  * parameterised SQL
  * debug pop-ups removed from scrapers
  * `[COLOR]`/`[B]`/`[I]` tags stripped from all text

`patches/cum-with-me-all-changes.diff` has every code change, compared against the decoded originals.

## Rebuilding

After editing an add-on, bump its version in `addon.xml`, then run:

```
python3 tools/build_repo.py
```

This regenerates `zips/`, `zips/addons.xml`, `zips/addons.xml.md5` and the repository zip in the root. Repo owner, name and branch live in `repo.json` (`python3 tools/build_repo.py --owner NAME --repo REPO` updates them).

## Licence

The add-ons are GPL-3.0 (see `LICENSE` and each add-on's own licence file).
