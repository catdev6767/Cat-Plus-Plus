#!/usr/bin/env python3
"""Cat++ Self-Healing."""
import os, sys, json, shutil, ast
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
BACKUP_DIR = '.backup'
LOG_DIR = '.catpp/log'
LOG_FILE = os.path.join(LOG_DIR, 'heal.log')

WATCH_FILES = [
    'interpreter.py','catpp_vm.py','catpp_pycompiler.py','server.py',
    'catpp.py','transpiler_c.py','catpplog.py','patch_engine.py',
    'gen_docs.py','gen_text.py','static/app.js','config.json','features.json',
]

G = '\033[92m'; R = '\033[91m'; Y = '\033[93m'
C = '\033[96m'; B = '\033[1m'; D = '\033[2m'; X = '\033[0m'

def log(action, data=None):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {'time': datetime.now().isoformat(timespec='seconds'),
             'action': action, 'data': data or {}}
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def verify(path):
    if not os.path.exists(path):
        return False, 'khong ton tai'
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, f'doc fail: {e}'
    if ext == '.py':
        try:
            ast.parse(content, path)
            return True, 'python OK'
        except SyntaxError as e:
            return False, f'SyntaxError dong {e.lineno}: {e.msg}'
        except Exception as e:
            return False, f'{type(e).__name__}: {e}'
    if ext == '.json':
        try:
            json.loads(content)
            return True, 'json OK'
        except json.JSONDecodeError as e:
            return False, f'JSON loi dong {e.lineno}: {e.msg}'
    if ext == '.js':
        o = content.count('{') - content.count('}')
        p = content.count('(') - content.count(')')
        b = content.count('[') - content.count(']')
        if abs(o) > 3 or abs(p) > 3 or abs(b) > 3:
            return False, f'ngoac lech: {{}}={o} ()={p} []={b}'
        return True, 'js OK'
    if ext == '.html':
        if '<html' not in content.lower() and '<!doctype' not in content.lower():
            return False, 'khong phai HTML'
        return True, 'html OK'
    return True, f'{ext} skip'

def find_backups(path):
    base = os.path.basename(path)
    candidates = []
    if os.path.isdir(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.startswith(base + '.'):
                candidates.append(os.path.join(BACKUP_DIR, f))
        for d in os.listdir(BACKUP_DIR):
            dpath = os.path.join(BACKUP_DIR, d)
            if os.path.isdir(dpath):
                cand = os.path.join(dpath, path)
                if os.path.exists(cand):
                    candidates.append(cand)
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates

def find_good_backup(path):
    backups = find_backups(path)
    if not backups:
        return None, 'khong co backup nao'
    tried = []
    for b in backups:
        ok, msg = verify(b)
        if ok:
            return b, f'{os.path.relpath(b)} ({msg})'
        tried.append(f'{os.path.basename(b)}: {msg}')
    return None, f'{len(backups)} backup, tat ca loi:\n     ' + '\n     '.join(tried[:3])

def backup_current(path):
    if not os.path.exists(path):
        return None
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    dst = os.path.join(BACKUP_DIR, f'{os.path.basename(path)}.{ts}.broken')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, dst)
    return dst

def cmd_check():
    print(f'{B}{C}=== Heal: check ==={X}\n')
    bad = 0
    for path in WATCH_FILES:
        ok, msg = verify(path)
        if ok:
            print(f'  {G}OK{X} {path}  {D}{msg}{X}')
        else:
            print(f'  {R}XX{X} {path}  {R}{msg}{X}')
            bad += 1
    print()
    if bad:
        print(f'{Y}{bad} file loi. Chay: python3 heal.py auto{X}')
        return 1
    print(f'{G}Tat ca OK.{X}')
    return 0

def cmd_auto():
    print(f'{B}{C}=== Heal: auto ==={X}\n')
    log('auto.start', {'files': len(WATCH_FILES)})
    fixed = 0; failed = 0
    for path in WATCH_FILES:
        ok, msg = verify(path)
        if ok:
            continue
        print(f'  {R}XX{X} {path}')
        print(f'     {D}Loi: {msg}{X}')
        bp, bp_msg = find_good_backup(path)
        if not bp:
            print(f'     {R}-> Khong co backup tot: {bp_msg}{X}')
            log('fail', {'file': path, 'reason': bp_msg})
            failed += 1
            continue
        broken = backup_current(path)
        if broken:
            print(f'     {D}-> Luu file loi: {os.path.relpath(broken)}{X}')
        try:
            shutil.copy2(bp, path)
            ok2, msg2 = verify(path)
            if ok2:
                print(f'     {G}-> Restore tu {os.path.relpath(bp)} OK{X}')
                log('restore.ok', {'file': path, 'from': bp, 'broken': broken})
                fixed += 1
            else:
                print(f'     {R}-> Restore nhung van loi: {msg2}{X}')
                log('restore.fail', {'file': path, 'from': bp, 'why': msg2})
                failed += 1
        except Exception as e:
            print(f'     {R}-> Restore fail: {e}{X}')
            log('error', {'file': path, 'err': str(e)})
            failed += 1
    print()
    log('auto.done', {'fixed': fixed, 'failed': failed})
    if fixed: print(f'{G}Da restore {fixed} file{X}')
    if failed:
        print(f'{R}{failed} file khong phuc hoi{X}')
        return 1
    if not fixed and not failed:
        print(f'{G}Tat ca OK.{X}')
    return 0

def cmd_list():
    print(f'{B}{C}=== Backups ==={X}\n')
    if not os.path.isdir(BACKUP_DIR):
        print(f'{D}Chua co .backup/{X}'); return
    entries = []
    for root, dirs, files in os.walk(BACKUP_DIR):
        for f in files:
            p = os.path.join(root, f)
            entries.append((os.path.getmtime(p), p))
    entries.sort(reverse=True)
    if not entries:
        print(f'{D}.backup/ rong{X}'); return
    for mt, p in entries[:30]:
        t = datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M')
        rel = os.path.relpath(p)
        ok, msg = verify(p)
        color = G if ok else R
        print(f'  {color}{"OK" if ok else "XX"}{X} {D}{t}{X}  {rel}')
    if len(entries) > 30:
        print(f'  {D}... va {len(entries)-30} file khac{X}')

def cmd_log():
    if not os.path.exists(LOG_FILE):
        print(f'{D}Chua co log{X}'); return
    print(f'{B}{C}=== Heal log ==={X}\n')
    with open(LOG_FILE, encoding='utf-8') as f:
        lines = f.readlines()[-20:]
    for line in lines:
        try:
            e = json.loads(line)
            t = e['time'][11:19]
            a = e['action']
            color = G if 'ok' in a or a == 'auto.done' else (R if 'fail' in a or 'error' in a else Y)
            data = e.get('data', {})
            extra = f' {data["file"]}' if 'file' in data else ''
            if 'fixed' in data:
                extra = f' fixed={data["fixed"]} failed={data["failed"]}'
            print(f'  {D}{t}{X} {color}{a}{X}{extra}')
        except Exception:
            pass

def cmd_add(path):
    if not os.path.exists(path):
        print(f'{R}File khong ton tai: {path}{X}'); return 1
    ok, msg = verify(path)
    if not ok:
        print(f'{R}File loi, khong backup: {msg}{X}'); return 1
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    dst = os.path.join(BACKUP_DIR, f'{os.path.basename(path)}.{ts}')
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(path, dst)
    print(f'{G}{dst}{X}')
    log('manual.backup', {'file': path, 'to': dst})
    return 0

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 0
    cmd = sys.argv[1]
    if cmd == 'check': return cmd_check()
    if cmd == 'auto': return cmd_auto()
    if cmd == 'list': cmd_list(); return 0
    if cmd == 'log': cmd_log(); return 0
    if cmd == 'add' and len(sys.argv) > 2: return cmd_add(sys.argv[2])
    print(__doc__); return 1

if __name__ == '__main__':
    sys.exit(main())
