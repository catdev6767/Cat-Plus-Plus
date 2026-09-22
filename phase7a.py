#!/usr/bin/env python3
"""Phase 7a — Clean catpp repo."""
import os, shutil, subprocess
from datetime import datetime

ROOT = os.path.expanduser('~/catpp')
os.chdir(ROOT)
bk = f'.backup/7a-{datetime.now().strftime("%H%M%S")}'
os.makedirs(bk, exist_ok=True)
print(f'backup: {bk}')

# 1. Git tag truoc khi sua
tag = f'pre-7a-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
subprocess.run(['git', 'tag', tag], capture_output=True)
print(f'✓ git tag {tag}')

# 2. Move test*.cat -> tests/fixtures/transpiler/
os.makedirs('tests/fixtures/transpiler', exist_ok=True)
for n in ['test1', 'test2', 'test3', 'test4']:
    if os.path.exists(f'{n}.cat'):
        shutil.move(f'{n}.cat', f'tests/fixtures/transpiler/{n}.cat')
        print(f'  ✓ moved {n}.cat')

# 3. Xoa binaries + generated C
for n in ['test1', 'test2', 'test3', 'test4']:
    for ext in ['', '.c']:
        f = f'{n}{ext}'
        if os.path.exists(f):
            os.remove(f)
            print(f'  ✓ removed {f}')

# 4. Xoa kitty.iso (duplicate)
if os.path.exists('kitty.iso'):
    sz = os.path.getsize('kitty.iso') // 1024 // 1024
    os.remove('kitty.iso')
    print(f'  ✓ removed kitty.iso ({sz}MB)')

# 5. Cap nhat .gitignore
gi = open('.gitignore', encoding='utf-8').read()
if '*.iso' not in gi:
    gi += """

# Build artifacts
*.o
*.obj
*.elf
*.iso
*.exe
*.so
*.a

# Test binaries
test[0-9]
test[0-9].c
"""
    open('.gitignore', 'w', encoding='utf-8').write(gi)
    print('  ✓ updated .gitignore')

# 6. Git commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase 7a - Clean repo: move test*.cat, remove binaries, update .gitignore'],
    capture_output=True, text=True)
print('committed' if r.returncode == 0 else f'no commit: {(r.stderr or r.stdout)[:100]}')
print('DONE')
