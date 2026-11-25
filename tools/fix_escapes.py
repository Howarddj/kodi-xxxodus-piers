#!/usr/bin/env python3
"""
Fix "SyntaxWarning: invalid escape sequence" (Python 3.12+) without changing behaviour.

An unknown escape such as "\\s" or "\\/" in a normal (non-raw) string literal is kept by
Python as a backslash followed by the character. Doubling that backslash produces the exact
same string value, so this only touches unknown escapes and leaves valid ones (\\n, \\t,
\\x41, \\u00e9, ...) and raw strings alone.

Every rewritten file is verified: its AST must be identical before and after, and it must
compile with SyntaxWarning turned into an error. Files that fail verification are not written.

    python3 tools/fix_escapes.py DIR_OR_FILE [...]
"""
import ast, io, os, sys, tokenize, warnings

STR_ESCAPES = set('\n\\\'"abfnrtv01234567xNuU')
BYTES_ESCAPES = set('\n\\\'"abfnrtv01234567x')


def fix_body(body, is_bytes):
    valid = BYTES_ESCAPES if is_bytes else STR_ESCAPES
    out, i, changed = [], 0, 0
    while i < len(body):
        ch = body[i]
        if ch == '\\' and i + 1 < len(body):
            nxt = body[i + 1]
            if nxt in valid or nxt == '\r':
                out.append(body[i:i + 2]); i += 2; continue
            out.append('\\\\'); i += 1; changed += 1; continue   # unknown escape: keep it literal
        out.append(ch); i += 1
    return ''.join(out), changed


def fix_string_token(tok):
    s = tok
    j = 0
    while j < len(s) and s[j] not in '\'"':
        j += 1
    prefix, rest = s[:j], s[j:]
    p = prefix.lower()
    if 'r' in p or 'f' in p or 't' in p:          # raw strings are fine; f/t-strings handled by FSTRING tokens
        return tok, 0
    q = rest[:3] if rest[:3] in ('"""', "'''") else rest[0]
    body = rest[len(q):-len(q)]
    new_body, n = fix_body(body, 'b' in p)
    return prefix + q + new_body + q, n


def fix_source(src):
    lines = src.splitlines(keepends=True)
    offsets = [0]
    for ln in lines:
        offsets.append(offsets[-1] + len(ln))
    edits, count = [], 0
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    in_raw_f = []
    for t in toks:
        if t.type == tokenize.STRING:
            new, n = fix_string_token(t.string)
            if n:
                a = offsets[t.start[0] - 1] + t.start[1]; b = offsets[t.end[0] - 1] + t.end[1]
                edits.append((a, b, new)); count += n
        elif getattr(tokenize, 'FSTRING_START', None) is not None and t.type == tokenize.FSTRING_START:
            in_raw_f.append('r' in t.string.lower())
        elif getattr(tokenize, 'FSTRING_END', None) is not None and t.type == tokenize.FSTRING_END:
            if in_raw_f: in_raw_f.pop()
        elif getattr(tokenize, 'FSTRING_MIDDLE', None) is not None and t.type == tokenize.FSTRING_MIDDLE:
            if in_raw_f and not in_raw_f[-1]:
                a = offsets[t.start[0] - 1] + t.start[1]; b = offsets[t.end[0] - 1] + t.end[1]
                seg = src[a:b]                    # raw source slice keeps {{ }} intact
                new, n = fix_body(seg, False)
                if n: edits.append((a, b, new)); count += n
    for a, b, new in sorted(edits, reverse=True):
        src = src[:a] + new + src[b:]
    return src, count


def compiles_cleanly(src, path):
    with warnings.catch_warnings():
        warnings.simplefilter('error', SyntaxWarning)
        compile(src, path, 'exec')


def process(path):
    raw = open(path, 'rb').read()
    try:
        src = raw.decode('utf-8')
    except UnicodeDecodeError:
        src = raw.decode('latin-1')
    try:
        ast.parse(src)
    except SyntaxError:
        return 'skip-py2', 0
    newline = '\r\n' if '\r\n' in src else None
    work = src.replace('\r\n', '\n') if newline else src
    try:
        new, n = fix_source(work)
    except (tokenize.TokenError, IndentationError, SyntaxError) as e:
        return 'skip-tokenize: %s' % e, 0
    if not n:
        try:
            compiles_cleanly(work, path); return 'clean', 0
        except SyntaxWarning as w:
            return 'WARN-UNFIXED: %s' % w, 0
    if ast.dump(ast.parse(work)) != ast.dump(ast.parse(new)):
        return 'REFUSED (AST changed)', 0
    try:
        compiles_cleanly(new, path)
    except SyntaxWarning as w:
        return 'WARN-REMAINS: %s' % w, n
    if newline: new = new.replace('\n', newline)
    enc = 'utf-8'
    try: new.encode('utf-8')
    except UnicodeEncodeError: enc = 'latin-1'
    open(path, 'wb').write(new.encode(enc))
    return 'fixed', n


def main():
    total_files = total = 0
    problems = []
    for root in sys.argv[1:]:
        paths = [root] if root.endswith('.py') else [os.path.join(dp, f) for dp, _, fs in os.walk(root) for f in fs if f.endswith('.py')]
        for p in sorted(paths):
            status, n = process(p)
            if status == 'fixed':
                total_files += 1; total += n
            elif status not in ('clean', 'skip-py2'):
                problems.append((p, status))
    print('fixed %d escape(s) in %d file(s)' % (total, total_files))
    for p, s in problems:
        print('  %s: %s' % (p, s))


if __name__ == '__main__':
    main()
