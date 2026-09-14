#!/usr/bin/env python3
"""Cat++ Log — theo dõi mọi thay đổi."""
import os, sys, json, subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT, '.catpp', 'log')
os.makedirs(LOG_DIR, exist_ok=True)

G = '\033[92m'; R = '\033[91m'; Y = '\033[93m'
C = '\033[96m'; B = '\033[1m'; D = '\033[2m'; X = '\033[0m'


def log(action, data=None):
    """Ghi 1 entry vào log."""
    entry = {
        'time': datetime.now().isoformat(timespec='seconds'),
        'action': action,
        'data': data or {},
        'cwd': os.getcwd(),
        'user': os.environ.get('USER', 'unknown'),
    }
    # Ghi file theo ngày
    day = datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(LOG_DIR, f'{day}.log')
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def read_logs(day=None, limit=50):
    """Đọc log."""
    if day is None:
        day = datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(LOG_DIR, f'{day}.log')
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-limit:]


def show(day=None, limit=30):
    entries = read_logs(day, limit)
    if not entries:
        print(f'{D}Chưa có log cho ngày {day or "hôm nay"}{X}')
        return
    print(f'{B}{C}Log ({len(entries)} entries){X}\n')
    for e in entries:
        t = e.get('time', '')[11:19]
        action = e.get('action', '?')
        data = e.get('data', {})
        # Màu theo action
        if 'error' in action or 'fail' in action:
            ac = R
        elif 'ok' in action or 'done' in action or 'pass' in action:
            ac = G
        elif 'patch' in action or 'edit' in action:
            ac = C
        else:
            ac = Y
        msg = data.get('msg', '')
        files = data.get('files', [])
        fstr = f' [{", ".join(files[:3])}]' if files else ''
        print(f'  {D}{t}{X} {ac}{action}{X}{fstr}')
        if msg:
            print(f'      {D}{msg}{X}')


def stats():
    """Thống kê log."""
    if not os.path.exists(LOG_DIR):
        return
    files = sorted(os.listdir(LOG_DIR))
    print(f'{B}{C}Log stats{X}\n')
    total = 0
    for f in files:
        path = os.path.join(LOG_DIR, f)
        with open(path, encoding='utf-8') as fh:
            n = sum(1 for _ in fh)
        total += n
        print(f'  {f}: {n} entries')
    print(f'\n  {B}Tổng: {total}{X}')


def clean(days=30):
    """Xóa log cũ hơn X ngày."""
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    for f in os.listdir(LOG_DIR):
        if not f.endswith('.log'):
            continue
        try:
            day = datetime.strptime(f[:-4], '%Y-%m-%d')
            if day < cutoff:
                os.remove(os.path.join(LOG_DIR, f))
                removed += 1
        except Exception:
            pass
    print(f'{G}✓ Đã xóa {removed} file log cũ{X}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'show'
    if cmd == 'show':
        day = sys.argv[2] if len(sys.argv) > 2 else None
        show(day)
    elif cmd == 'stats':
        stats()
    elif cmd == 'clean':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        clean(days)
    elif cmd == 'test':
        # Test log
        log('test.start', {'msg': 'Test log system'})
        log('test.ok', {'msg': 'Success'})
        show()
    else:
        print(f'''{B}Cat++ Log{X}

  python3 catpplog.py show [YYYY-MM-DD]   Xem log
  python3 catpplog.py stats               Thống kê
  python3 catpplog.py clean [days]        Xóa log cũ
''')
