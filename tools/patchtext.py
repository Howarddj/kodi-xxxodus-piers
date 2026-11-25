"""Exact-text patcher: each (old, new, count) must match exactly `count` times or the file is left untouched."""
def apply(path, edits):
    raw = open(path, 'rb').read()
    crlf = b'\r\n' in raw
    s = raw.decode('utf-8', 'surrogateescape').replace('\r\n', '\n')
    for old, new, count in edits:
        n = s.count(old)
        if n != count:
            raise SystemExit(f'{path}: expected {count} match(es), found {n}:\n{old[:300]}')
        s = s.replace(old, new)
    if crlf: s = s.replace('\n', '\r\n')
    open(path, 'wb').write(s.encode('utf-8', 'surrogateescape'))
    print(f'patched {path} ({len(edits)} edit(s))')
