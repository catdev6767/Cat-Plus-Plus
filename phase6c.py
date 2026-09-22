#!/usr/bin/env python3
"""Phase 6c — EN-only docs pipeline (remove VI)."""
import os, sys, shutil, subprocess
from datetime import datetime

ROOT = os.path.expanduser('~/catpp')
os.chdir(ROOT)

bk = f'.backup/6c-{datetime.now().strftime("%H%M%S")}'
os.makedirs(bk, exist_ok=True)

FILES = ['gen_docs.py', 'server.py', 'docs_data_en.py', 'docs_extra_en.py']

print('═══ Backup ═══')
for f in FILES:
    if os.path.exists(f):
        shutil.copy(f, os.path.join(bk, f))
        print(f'  ✓ {f}')

def rollback(msg=''):
    print(f'\n❌ Rollback {msg}')
    for f in FILES:
        src = os.path.join(bk, os.path.basename(f))
        if os.path.exists(src):
            shutil.copy(src, f)
    for f in ['docs_data_vi.py', 'docs_extra_vi.py']:
        src = os.path.join(bk, f)
        if os.path.exists(src) and not os.path.exists(f):
            shutil.copy(src, f)
    if not os.path.exists('static/docs/vi') and os.path.exists(f'{bk}/static_docs_vi'):
        shutil.move(f'{bk}/static_docs_vi', 'static/docs/vi')
    sys.exit(1)

def patch(c, old, new, label):
    if old not in c:
        print(f'  ✗ {label} — anchor không tìm thấy')
        print(f'     Cần tìm: {old[:80]!r}...')
        rollback()
    return c.replace(old, new, 1)

print('\n═══ Patch gen_docs.py ═══')
c = open('gen_docs.py', encoding='utf-8').read()

c = patch(c,
    "        import docs_data_vi; import docs_data_en\n        importlib.reload(docs_data_vi)\n        pass  # EN removed",
    "        import docs_data_en\n        importlib.reload(docs_data_en)",
    'P1 header import')
print('  ✓ P1 header')

c = patch(c,
    "            import docs_extra_vi, docs_extra_en\n            importlib.reload(docs_extra_vi)\n            importlib.reload(docs_extra_en)",
    "            import docs_extra_en\n            importlib.reload(docs_extra_en)",
    'P2 extra import')
print('  ✓ P2 extra import')

c = patch(c,
    "            docs_data_vi.KEYWORDS = {**docs_data_vi.KEYWORDS, **docs_extra_vi.KEYWORDS_EXTRA}\n            docs_data_vi.BUILTINS = {**docs_data_vi.BUILTINS, **docs_extra_vi.BUILTINS_EXTRA}\n",
    "",
    'P3 VI kw/bi merge')
print('  ✓ P3 VI kw/bi removed')

c = patch(c,
    "            if hasattr(docs_extra_vi, 'TUTORIAL_EXTRA'):\n                docs_data_vi.TUTORIAL = list(docs_data_vi.TUTORIAL) + list(docs_extra_vi.TUTORIAL_EXTRA)\n",
    "",
    'P4 VI tutorial')
print('  ✓ P4 VI tutorial removed')

c = patch(c,
    "            if hasattr(docs_extra_vi, 'COOKBOOK_EXTRA'):\n                docs_data_vi.COOKBOOK = list(docs_extra_vi.COOKBOOK_EXTRA)\n",
    "",
    'P5 VI cookbook')
print('  ✓ P5 VI cookbook removed')

c = patch(c,
    "            if hasattr(docs_extra_vi, 'ERRORS_EXTRA'):\n                docs_data_vi.ERRORS = list(docs_extra_vi.ERRORS_EXTRA)\n",
    "",
    'P6 VI errors')
print('  ✓ P6 VI errors removed')

c = patch(c,
    "            if hasattr(docs_extra_vi, 'GUIDE_EXTRA'):\n                docs_data_vi.GUIDE = list(docs_extra_vi.GUIDE_EXTRA)\n",
    "",
    'P7 VI guide')
print('  ✓ P7 VI guide removed')

c = patch(c,
    "            print(f'  + Merged extras: {len(docs_data_vi.KEYWORDS)} kw, {len(docs_data_vi.BUILTINS)} bi, {len(docs_data_vi.TUTORIAL)} tut')",
    "            print(f'  + Merged extras: {len(docs_data_en.KEYWORDS)} kw, {len(docs_data_en.BUILTINS)} bi, {len(docs_data_en.TUTORIAL)} tut')",
    'P8 print line')
print('  ✓ P8 print line')

c = patch(c,
    "        build_lang('vi', docs_data_vi)\n        # build_lang('en', docs_data_en)\n        build_lang('en', docs_data_en)",
    "        build_lang('en', docs_data_en)",
    'P9 build_lang VI')
print('  ✓ P9 build_lang VI removed')

c = patch(c,
    "  var lang = localStorage.getItem('catpp:lang') || 'vi';",
    "  var lang = 'en';",
    'P10 redirect')
print('  ✓ P10 redirect → en')

open('gen_docs.py', 'w', encoding='utf-8').write(c)

print('\n═══ Patch server.py ═══')
s = open('server.py', encoding='utf-8').read()
s = patch(s, "        lang = 'vi'", "        lang = 'en'", 'server.py default lang')
open('server.py', 'w', encoding='utf-8').write(s)
print('  ✓ server.py default lang → en')

print('\n═══ Syntax check ═══')
for f in ['gen_docs.py', 'server.py']:
    try:
        compile(open(f, encoding='utf-8').read(), f, 'exec')
        print(f'  ✓ {f}')
    except SyntaxError as e:
        print(f'  ✗ {f}: {e}')
        rollback('syntax check')

print('\n═══ Move VI files to backup ═══')
for f in ['docs_data_vi.py', 'docs_extra_vi.py']:
    if os.path.exists(f):
        shutil.move(f, os.path.join(bk, f))
        print(f'  ✓ moved {f}')
if os.path.exists('static/docs/vi'):
    shutil.move('static/docs/vi', os.path.join(bk, 'static_docs_vi'))
    print(f'  ✓ moved static/docs/vi')

print('\n═══ Rebuild EN ═══')
r = subprocess.run(['python3', 'gen_docs.py'], capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    rollback('build failed')

print('═══ Verify ═══')
if not os.path.exists('static/docs/en/index.html'):
    rollback('en/index.html missing')
count = sum(1 for root, _, files in os.walk('static/docs/en')
            for f in files if f.endswith('.html'))
print(f'  ✓ static/docs/en: {count} html files')
print(f'  {"✓" if not os.path.exists("static/docs/vi") else "⚠"} static/docs/vi: {"gone" if not os.path.exists("static/docs/vi") else "still there"}')

idx = open('static/docs/index.html', encoding='utf-8').read()
print(f'  {"✓" if chr(39)+"en"+chr(39) in idx else "⚠"} redirect → en')

print('\n═══ Commit ═══')
subprocess.run(['git', 'add', '-A'], capture_output=True)
r = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase 6c — EN-only docs pipeline'],
    capture_output=True, text=True)
print('  ✓ commit' if r.returncode == 0 else f'  ○ no commit: {(r.stderr or r.stdout).strip()[:80]}')

print(f"""
╔══════════════════════════════════════════════╗
║  ✅ PHASE 6c — EN-ONLY DOCS                  ║
╚══════════════════════════════════════════════╝
Backup: {bk}/
Rollback: python3 phase6c.py --rollback {bk}
""")
