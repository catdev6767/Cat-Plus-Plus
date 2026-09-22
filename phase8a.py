#!/usr/bin/env python3
"""Phase 8a - PawEditor full syntax highlight."""
import os, sys, shutil, subprocess, re
from datetime import datetime

ROOT = os.path.expanduser('~/catpp')
os.chdir(ROOT)
sys.path.insert(0, ROOT)

bk = f'.backup/8a-{datetime.now().strftime("%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('pawedit/pawedit.py', bk + '/pawedit.py')
print('backup:', bk)

from interpreter import KEYWORDS, make_builtins
kw = sorted(KEYWORDS)
bi = sorted(make_builtins().keys())
print(f'keywords: {len(kw)}, builtins: {len(bi)}')

def fmt_set(name, items):
    lines = [f'{name} = {{']
    line = '    '
    for it in items:
        add = f"'{it}', "
        if len(line) + len(add) > 78:
            lines.append(line.rstrip())
            line = '    '
        line += add
    if line.strip():
        lines.append(line.rstrip())
    lines.append('}')
    return '\n'.join(lines)

new_kw = fmt_set('CATPP_KEYWORDS', kw)
new_bi = fmt_set('CATPP_BUILTINS', bi)

new_hl = '''def hl(line, ext):
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == '#':
            out.append((line[i:], 3)); break
        if c == '"':
            j = i + 1
            while j < n and line[j] != '"':
                j += 2 if (line[j] == '\\\\' and j+1 < n) else 1
            if j < n: j += 1
            out.append((line[i:j], 2)); i = j; continue
        if c.isdigit() or (c == '.' and i+1 < n and line[i+1].isdigit()):
            j = i
            if c == '0' and i+1 < n and line[i+1] in 'xXbB':
                j = i + 2
                while j < n and line[j] in '0123456789abcdefABCDEF_': j += 1
            else:
                while j < n and (line[j].isdigit() or line[j] == '.'): j += 1
            out.append((line[i:j], 4)); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'): j += 1
            w = line[i:j]
            if w in CATPP_KEYWORDS: out.append((w, 5))
            elif w in CATPP_BUILTINS: out.append((w, 6))
            else: out.append((w, 0))
            i = j; continue
        if c in '+-*/%=<>!&|^~?:':
            j = i
            while j < n and line[j] in '+-*/%=<>!&|^~?:': j += 1
            out.append((line[i:j], 7)); i = j; continue
        out.append((c, 0)); i += 1
    return out'''

content = open('pawedit/pawedit.py', encoding='utf-8').read()

pat_kw = re.compile(r'CATPP_KEYWORDS = \{.*?\n\}', re.DOTALL)
pat_bi = re.compile(r'CATPP_BUILTINS = \{.*?\n\}', re.DOTALL)
pat_hl = re.compile(r'def hl\(line, ext\):.*?\n    return out', re.DOTALL)

for name, pat in [('KEYWORDS', pat_kw), ('BUILTINS', pat_bi), ('hl()', pat_hl)]:
    if not pat.search(content):
        print(f'FAIL: {name} not found')
        shutil.copy(bk + '/pawedit.py', 'pawedit/pawedit.py')
        sys.exit(1)

content = pat_kw.sub(new_kw, content, count=1)
content = pat_bi.sub(new_bi, content, count=1)
content = pat_hl.sub(new_hl, content, count=1)

open('pawedit/pawedit.py', 'w', encoding='utf-8').write(content)
print('patched')

try:
    compile(open('pawedit/pawedit.py', encoding='utf-8').read(), 'pawedit.py', 'exec')
    print('syntax ok')
except SyntaxError as e:
    print('syntax FAIL:', e)
    shutil.copy(bk + '/pawedit.py', 'pawedit/pawedit.py')
    sys.exit(1)

import importlib.util
spec = importlib.util.spec_from_file_location('pe', 'pawedit/pawedit.py')
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)

tests = [
    'meow "Hello, {name}!"',
    'purr add(a: i32, b: i32) -> i32',
    'paw x = 0xFF',
    'sniff x > 3 with x < 10',
    'paw f = kit(x) => x * 2',
    'give chase(arr, f)',
    'paw d = {"a": 1}',
    'groom c of arr',
    '# comment test',
]
print()
print('=== Test highlight ===')
for line in tests:
    toks = pe.hl(line, '')
    # In compact: token:color
    compact = ' '.join(f'{t}({c})' for t, c in toks if t.strip())
    print(f'  {line!r}')
    print(f'    {compact}')

subprocess.run(['git', 'add', 'pawedit/pawedit.py'], capture_output=True)
r = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase 8a - PawEditor: full Cat++ syntax highlight'],
    capture_output=True, text=True)
print()
print('committed' if r.returncode == 0 else f'no commit: {(r.stderr or r.stdout)[:80]}')
