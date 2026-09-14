#!/usr/bin/env python3
"""Cat++ Patch Engine — Atomic patching.

Cách dùng:
    python3 patch_engine.py list               # Xem patches
    python3 patch_engine.py apply <name>       # Áp dụng
    python3 patch_engine.py rollback <name>    # Rollback
    python3 patch_engine.py check <name>       # Chỉ kiểm tra
    python3 patch_engine.py test               # Chạy test
    python3 patch_engine.py log                # Xem log patches
"""
import os, sys, json, shutil, subprocess, importlib.util
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

PATCH_DIR = 'patches'
SNAP_DIR = '.catpp/snapshot'
LOG_FILE = '.catpp/log/patch.log'

G = '\033[92m'; R = '\033[91m'; Y = '\033[93m'
C = '\033[96m'; B = '\033[1m'; D = '\033[2m'; X = '\033[0m'


def out(msg, color=''):
    print((color + msg + X) if color else msg)


def now_ts():
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def log(action, name='', data=None):
    """Ghi log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        'time': datetime.now().isoformat(timespec='seconds'),
        'action': action,
        'patch': name,
        'data': data or {},
    }
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def list_patches():
    """Liệt kê patches có sẵn."""
    if not os.path.isdir(PATCH_DIR):
        return []
    patches = []
    for f in sorted(os.listdir(PATCH_DIR)):
        if f.endswith('.py') and not f.startswith('_'):
            name = f[:-3]
            path = os.path.join(PATCH_DIR, f)
            desc = ''
            try:
                with open(path, encoding='utf-8') as fh:
                    for line in fh:
                        if 'DESC' in line and '=' in line:
                            desc = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass
            patches.append({'name': name, 'file': f, 'desc': desc})
    return patches


def load_patch(name):
    """Load patch module."""
    path = os.path.join(PATCH_DIR, f'{name}.py')
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(f'patch_{name}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def snapshot(files):
    """Snapshot files trước khi sửa."""
    snap_id = now_ts()
    snap_path = os.path.join(SNAP_DIR, snap_id)
    os.makedirs(snap_path, exist_ok=True)
    for f in files:
        if os.path.exists(f):
            dst = os.path.join(snap_path, f)
            os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
            shutil.copy2(f, dst)
    # Metadata
    with open(os.path.join(snap_path, '_meta.json'), 'w') as fh:
        json.dump({'files': files, 'time': snap_id}, fh)
    return snap_id


def restore_snapshot(snap_id):
    """Restore từ snapshot."""
    snap_path = os.path.join(SNAP_DIR, snap_id)
    if not os.path.exists(snap_path):
        return False
    meta_file = os.path.join(snap_path, '_meta.json')
    if os.path.exists(meta_file):
        with open(meta_file) as f:
            meta = json.load(f)
        files = meta.get('files', [])
    else:
        files = []
    for f in files:
        src = os.path.join(snap_path, f)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(f) or '.', exist_ok=True)
            shutil.copy2(src, f)
    return True


def run_tests():
    """Chạy test, trả về (pass, msg)."""
    r = subprocess.run([sys.executable, 'tests/test_all.py'],
                       capture_output=True, text=True, timeout=90)
    if not r.stdout:
        return False, 'no output'
    import re
    m = re.search(r'(\d+)\s+pass[,\s]+(\d+)\s+fail', r.stdout)
    if m:
        p, f = int(m.group(1)), int(m.group(2))
        return f == 0, f'{p} pass, {f} fail'
    return False, 'cannot parse'


def syntax_ok(path):
    """Kiểm tra syntax."""
    if not path.endswith('.py'):
        return True, 'not python'
    try:
        with open(path, encoding='utf-8') as f:
            compile(f.read(), path, 'exec')
        return True, 'ok'
    except SyntaxError as e:
        return False, f'dòng {e.lineno}: {e.msg}'


def apply_patch(name, check_only=False):
    """Áp dụng patch — atomic."""
    print(f'\n{B}{C}═══ Patch: {name} ═══{X}\n')

    mod = load_patch(name)
    if mod is None:
        out(f'✗ Không tìm thấy patch: {name}', R)
        return False

    # Danh sách edit
    edits = getattr(mod, 'EDITS', [])
    desc = getattr(mod, 'DESC', '')
    if desc:
        out(f'  Mô tả: {desc}', D)

    if not edits:
        out('  ○ Patch rỗng', Y)
        return True

    # Thu thập files
    files_to_edit = sorted(set(e[0] for e in edits))
    out(f'  Files: {", ".join(files_to_edit)}', D)
    out(f'  Edits: {len(edits)}', D)
    print()

    # Snapshot
    snap_id = snapshot(files_to_edit)
    out(f'  Snapshot: {snap_id}', D)
    log('snapshot', name, {'snap': snap_id, 'files': files_to_edit})

    # Apply từng edit
    for i, edit in enumerate(edits, 1):
        path, old, new = edit[0], edit[1], edit[2]
        label = edit[3] if len(edit) > 3 else f'Edit {i}'

        if not os.path.exists(path):
            out(f'  ✗ [{label}] File không tồn tại: {path}', R)
            out(f'  → Restore snapshot', Y)
            restore_snapshot(snap_id)
            log('fail', name, {'reason': f'file missing: {path}'})
            return False

        with open(path, encoding='utf-8') as f:
            content = f.read()

        if new in content and old not in content:
            out(f'  ○ [{label}] Đã có', Y)
            continue

        if old not in content:
            out(f'  ✗ [{label}] Anchor không tìm thấy', R)
            out(f'     File: {path}', D)
            out(f'     Cần tìm: {old[:80]!r}...', D)
            out(f'  → Restore snapshot', Y)
            restore_snapshot(snap_id)
            log('fail', name, {'reason': f'anchor missing: {label}'})
            return False

        content = content.replace(old, new, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        out(f'  ✓ [{label}]', G)

    # Syntax check
    print()
    out('  Syntax check:', D)
    for f in files_to_edit:
        ok, msg = syntax_ok(f)
        if ok:
            out(f'    ✓ {f}', G)
        else:
            out(f'    ✗ {f}: {msg}', R)
            out(f'  → Restore snapshot', Y)
            restore_snapshot(snap_id)
            log('fail', name, {'reason': f'syntax: {f} - {msg}'})
            return False

    # Test
    if check_only:
        out(f'\n  {Y}○ Check only — không chạy test{X}')
        # Vẫn restore để không thay đổi
        restore_snapshot(snap_id)
        return True

    print()
    out('  Test:', D)
    pass_, msg = run_tests()
    if pass_:
        out(f'    ✓ {msg}', G)
    else:
        out(f'    ✗ {msg}', R)
        out(f'  → Restore snapshot', Y)
        restore_snapshot(snap_id)
        log('fail', name, {'reason': f'test: {msg}'})
        return False

    # Commit
    subprocess.run(['git', 'add', '-A'], capture_output=True)
    r = subprocess.run(['git', 'commit', '-q', '-m', f'Patch: {name} — {desc}'],
                       capture_output=True)
    if r.returncode == 0:
        out(f'\n  {G}✓ Commit{X}', G)
        log('ok', name, {'snap': snap_id, 'test': msg})
        print()
        out(f'{G}{B}✓ Patch {name} thành công{X}')
    else:
        out(f'\n  {Y}○ Không có gì mới để commit{X}')
        log('ok', name, {'snap': snap_id, 'test': msg})

    return True


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'

    if cmd == 'list':
        patches = list_patches()
        if not patches:
            out(f'{D}Chưa có patch nào trong {PATCH_DIR}/{X}')
            return
        out(f'\n{B}{C}Có {len(patches)} patch(es):{X}\n', '')
        for p in patches:
            out(f'  {C}{p["name"]}{X}', '')
            if p['desc']:
                out(f'    {D}{p["desc"]}{X}', '')

    elif cmd == 'apply' and len(sys.argv) > 2:
        ok = apply_patch(sys.argv[2])
        sys.exit(0 if ok else 1)

    elif cmd == 'check' and len(sys.argv) > 2:
        ok = apply_patch(sys.argv[2], check_only=True)
        sys.exit(0 if ok else 1)

    elif cmd == 'rollback' and len(sys.argv) > 2:
        name = sys.argv[2]
        snaps = sorted(os.listdir(SNAP_DIR)) if os.path.exists(SNAP_DIR) else []
        if not snaps:
            out(f'✗ Không có snapshot nào', R)
            return
        # Restore snapshot mới nhất
        latest = snaps[-1]
        restore_snapshot(latest)
        out(f'{G}✓ Đã restore snapshot {latest}{X}')

    elif cmd == 'test':
        pass_, msg = run_tests()
        if pass_:
            out(f'{G}✓ {msg}{X}')
        else:
            out(f'{R}✗ {msg}{X}')
        sys.exit(0 if pass_ else 1)

    elif cmd == 'log':
        if not os.path.exists(LOG_FILE):
            out(f'{D}Chưa có log{X}')
            return
        with open(LOG_FILE, encoding='utf-8') as f:
            lines = f.readlines()[-30:]
        for line in lines:
            try:
                e = json.loads(line)
                t = e['time'][11:19]
                act = e['action']
                patch = e.get('patch', '')
                if act == 'ok':
                    ac = G
                elif act == 'fail':
                    ac = R
                else:
                    ac = Y
                msg = ''
                if e.get('data', {}).get('reason'):
                    msg = f' — {e["data"]["reason"]}'
                out(f'  {D}{t}{X} {ac}{act}{X} {patch}{msg}')
            except Exception:
                pass

    else:
        out(f'''{B}Cat++ Patch Engine{X}

  {C}python3 patch_engine.py list{X}           Xem patches
  {C}python3 patch_engine.py apply <name>{X}   Áp dụng patch
  {C}python3 patch_engine.py check <name>{X}   Kiểm tra (không apply)
  {C}python3 patch_engine.py rollback{X}       Restore snapshot gần nhất
  {C}python3 patch_engine.py test{X}           Chạy test
  {C}python3 patch_engine.py log{X}            Xem log patches
''', '')


if __name__ == '__main__':
    main()
