#!/usr/bin/env python3
"""
Build the Kodi repository from the add-on source folders in this repo.

    python3 tools/build_repo.py                       # uses repo.json
    python3 tools/build_repo.py --owner me --repo x   # also updates repo.json

For every top-level folder that contains an addon.xml it writes
    zips/<id>/<id>-<version>.zip   (+ icon/fanart for Kodi's repo browser)
then zips/addons.xml and zips/addons.xml.md5, and copies the repository
add-on zip to the repo root so it can be installed with "Install from zip".
"""
import argparse, hashlib, json, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIPS = os.path.join(ROOT, 'zips')
SKIP_DIRS = {'__pycache__', '.git', '.github', '.idea', '.vscode'}
SKIP_FILES = ('.pyc', '.pyo', '.DS_Store')


def load_cfg(args):
    path = os.path.join(ROOT, 'repo.json')
    cfg = json.load(open(path))
    changed = False
    for k in ('owner', 'repo', 'branch'):
        v = getattr(args, k)
        if v and v != cfg.get(k):
            cfg[k] = v; changed = True
    if changed:
        json.dump(cfg, open(path, 'w'), indent=2); open(path, 'a').write('\n')
    return cfg


def render_repository_addon(cfg):
    tpl = open(os.path.join(ROOT, 'tools', 'repository.addon.xml.in'), encoding='utf-8').read()
    raw = 'https://raw.githubusercontent.com/{owner}/{repo}/{branch}'.format(**cfg)
    xml = tpl.format(raw=raw, **cfg)
    ET.fromstring(xml.encode('utf-8'))  # validate
    d = os.path.join(ROOT, cfg['repository_id'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'addon.xml'), 'w', encoding='utf-8').write(xml)


def addon_info(folder):
    xml = open(os.path.join(folder, 'addon.xml'), 'rb').read()
    root = ET.fromstring(xml)
    if root.tag != 'addon':
        raise SystemExit('%s/addon.xml: root element is not <addon>' % folder)
    return root.get('id'), root.get('version'), root, xml.decode('utf-8')


def make_zip(folder, addon_id, version):
    out_dir = os.path.join(ZIPS, addon_id)
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):          # keep only the current version's zip
        if old.endswith('.zip') and old != '%s-%s.zip' % (addon_id, version):
            os.remove(os.path.join(out_dir, old))
    target = os.path.join(out_dir, '%s-%s.zip' % (addon_id, version))
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(folder):
            dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
            for fn in sorted(fns):
                if fn.endswith(SKIP_FILES):
                    continue
                full = os.path.join(dp, fn)
                arc = os.path.join(addon_id, os.path.relpath(full, folder))
                z.write(full, arc)
    return target


def copy_assets(folder, root, addon_id):
    out_dir = os.path.join(ZIPS, addon_id)
    wanted = set()
    for tag in ('icon', 'fanart'):
        el = root.find('.//assets/%s' % tag)
        if el is not None and el.text:
            wanted.add(el.text.strip())
    for name in ('icon.png', 'fanart.jpg'):
        if os.path.exists(os.path.join(folder, name)):
            wanted.add(name)
    for rel in wanted:
        src = os.path.join(folder, rel)
        if os.path.isfile(src):
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owner'); ap.add_argument('--repo'); ap.add_argument('--branch')
    cfg = load_cfg(ap.parse_args())
    if 'OWNER' in (cfg['owner'], cfg['repo']) or 'REPO' in (cfg['owner'], cfg['repo']):
        print('warning: repo.json still has placeholder owner/repo; URLs will not work until set', file=sys.stderr)
    render_repository_addon(cfg)

    entries = []
    for name in sorted(os.listdir(ROOT)):
        folder = os.path.join(ROOT, name)
        if not os.path.isfile(os.path.join(folder, 'addon.xml')):
            continue
        addon_id, version, root, xml = addon_info(folder)
        if addon_id != name:
            raise SystemExit('folder %s does not match add-on id %s' % (name, addon_id))
        z = make_zip(folder, addon_id, version)
        copy_assets(folder, root, addon_id)
        entries.append(re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml).rstrip())
        print('%-34s %-12s %s' % (addon_id, version, os.path.relpath(z, ROOT)))

    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + '\n\n'.join(entries) + '\n</addons>\n'
    ET.fromstring(addons_xml.encode('utf-8'))  # validate
    os.makedirs(ZIPS, exist_ok=True)
    open(os.path.join(ZIPS, 'addons.xml'), 'w', encoding='utf-8').write(addons_xml)
    md5 = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    open(os.path.join(ZIPS, 'addons.xml.md5'), 'w').write(md5)

    rid, rver = cfg['repository_id'], cfg['repository_version']
    for old in os.listdir(ROOT):
        if old.startswith(rid + '-') and old.endswith('.zip') and old != '%s-%s.zip' % (rid, rver):
            os.remove(os.path.join(ROOT, old))
    shutil.copyfile(os.path.join(ZIPS, rid, '%s-%s.zip' % (rid, rver)), os.path.join(ROOT, '%s-%s.zip' % (rid, rver)))
    print('addons.xml: %d add-ons, md5 %s' % (len(entries), md5))


if __name__ == '__main__':
    main()
