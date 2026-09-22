#!/usr/bin/env python3
"""Phase 8b - Comment color gray + README fix + push."""
import os, sys, shutil, subprocess
from datetime import datetime

ROOT = os.path.expanduser('~/catpp')
os.chdir(ROOT)

bk = f'.backup/8b-{datetime.now().strftime("%H%M%S")}'
os.makedirs(bk, exist_ok=True)
for f in ['pawedit/pawedit.py', 'README.md']:
    shutil.copy(f, os.path.join(bk, os.path.basename(f)))
print('backup:', bk)

# === 1. Fix comment color: yellow -> gray ===
c = open('pawedit/pawedit.py', encoding='utf-8').read()
old = "    curses.init_pair(3, curses.COLOR_YELLOW, -1)"
new = """    # Comment color: gray if terminal supports it
    if curses.COLORS >= 256:
        curses.init_pair(3, 244, -1)
    elif curses.can_change_color():
        curses.init_color(8, 500, 500, 500)
        curses.init_pair(3, 8, -1)
    else:
        curses.init_pair(3, curses.COLOR_WHITE, -1)"""
if old not in c:
    print('FAIL: comment color anchor not found')
    sys.exit(1)
c = c.replace(old, new, 1)
open('pawedit/pawedit.py', 'w', encoding='utf-8').write(c)
print('fixed comment color (gray)')

try:
    compile(open('pawedit/pawedit.py', encoding='utf-8').read(), 'pawedit.py', 'exec')
    print('syntax ok')
except SyntaxError as e:
    print('syntax FAIL:', e)
    shutil.copy(bk + '/pawedit.py', 'pawedit/pawedit.py')
    sys.exit(1)

# === 2. Fix README PawEditor section ===
r = open('README.md', encoding='utf-8').read()

old_pawedit = """## PawEditor

Nano-like editor for Cat++ with syntax highlight. Written in Python + curses.

    pawedit hello.cat

Shortcuts: ^S Save, ^O Save-As, ^W Find, ^G Goto, ^K Cut, ^U Paste, ^X Exit."""

new_pawedit = """## PawEditor

Terminal editor for Cat++, written in Python + curses. Nano-like with
full Cat++ syntax highlighting (keywords, builtins, strings, numbers,
comments, operators).

    python3 pawedit/pawedit.py              # empty buffer
    python3 pawedit/pawedit.py hello.cat    # open file

Shortcuts:

| Key      | Action                     |
|----------|----------------------------|
| `Ctrl+S` | Save                       |
| `Ctrl+O` | Save as                    |
| `Ctrl+G` | Go to line                 |
| `Ctrl+K` | Delete line                |
| `Ctrl+X` | Exit                       |"""

if old_pawedit not in r:
    print('WARN: README block not found')
else:
    r = r.replace(old_pawedit, new_pawedit, 1)
    open('README.md', 'w', encoding='utf-8').write(r)
    print('fixed README PawEditor')

# === 3. Commit ===
subprocess.run(['git', 'add', '-A'], capture_output=True)
r = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase 8b - PawEditor: gray comments, README shortcuts fix'],
    capture_output=True, text=True)
print('committed' if r.returncode == 0 else f'no commit: {(r.stderr or r.stdout)[:100]}')

# === 4. Push ===
print()
r = subprocess.run(['git', 'push'], capture_output=True, text=True)
if r.returncode == 0:
    print('pushed to GitHub')
    print(r.stdout[:200] if r.stdout else '')
else:
    print('push failed:')
    print((r.stderr or r.stdout)[:300])

print()
print('DONE')

