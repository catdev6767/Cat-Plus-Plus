#!/usr/bin/env python3
"""Test toàn bộ hệ thống Cat++."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0
ERRORS = []

def check(name, cond, msg=''):
    global PASS, FAIL
    if cond:
        print(f'  ✓ {name}')
        PASS += 1
    else:
        print(f'  ✗ {name}: {msg}')
        FAIL += 1
        ERRORS.append((name, msg))


def section(title):
    print()
    print('═' * 50)
    print('  ' + title)
    print('═' * 50)


# 1. Core
section('1. Core modules')

try:
    from core.registry import Registry
    r = Registry()
    r.set('x', 42)
    check('Registry.set/get', r.get('x') == 42)
    check('Registry.has', r.has('x'))
except Exception as e:
    check('Registry', False, str(e))

try:
    from core.bus import EventBus
    b = EventBus()
    got = []
    b.on('test', lambda d: got.append(d))
    b.emit('test', 'hello')
    check('Bus on/emit', got == ['hello'])
except Exception as e:
    check('Bus', False, str(e))

try:
    from core.module import BaseModule
    m = BaseModule(None, None)
    check('BaseModule', m.name == 'unnamed')
except Exception as e:
    check('BaseModule', False, str(e))

try:
    from core.loader import Loader
    check('Loader import', True)
except Exception as e:
    check('Loader import', False, str(e))


# 2. Interpreter backend
section('2. Interpreter backend')

try:
    from interpreter import run_catpp
    check('Import interpreter', True)

    tests = [
        ('meow', 'meow "hi"', 'hi'),
        ('paw + cộng', 'paw x = 5\nmeow x + 3', '8'),
        ('+=', 'paw x = 5\nx += 3\nmeow x', '8'),
        ('++', 'paw x = 5\nx++\nmeow x', '6'),
        ('sniff/swat', 'sniff 5 > 3\n    meow "big"\nswat\n    meow "small"', 'big'),
        ('knead', 'paw i = 1\nknead i <= 3\n    meow i\n    i++', '1\n2\n3'),
        ('groom', 'groom c of ["a","b"]\n    meow c', 'a\nb'),
        ('in operator', 'sniff 3 in [1,2,3]\n    meow "yes"', 'yes'),
        ('string.upper', 'meow "hello".upper()', 'HELLO'),
        ('list.sort', 'paw a = [3,1,2]\na.sort()\nmeow a', '[1, 2, 3]'),
        ('regex', 'sniff match("[0-9]", "a1")\n    meow "yes"', 'yes'),
        ('match/case', 'paw x = 2\nmatch x\n    case 1\n        meow "one"\n    case 2\n        meow "two"', 'two'),
        ('purr/give', 'purr add(a,b)\n    give a+b\nmeow add(3,4)', '7'),
        ('cat/me', 'cat P\n    paw x\n    purr new(v)\n        me.x = v\npaw p = P(5)\nmeow p.x', '5'),
    ]

    for name, code, expect in tests:
        try:
            got = run_catpp(code).strip()
            check(f'  {name}', got == expect, f'mong {expect!r}, nhận {got!r}')
        except Exception as e:
            check(f'  {name}', False, f'{type(e).__name__}: {e}')
except Exception as e:
    check('Import interpreter', False, str(e))


# 3. Module interpreter
section('3. Module interpreter')

try:
    from modules.interpreter.module import InterpreterModule
    check('Import InterpreterModule', True)

    from core.registry import Registry
    from core.bus import EventBus
    reg = Registry()
    bus = EventBus()
    mod = InterpreterModule(reg, bus)
    mod.setup()

    check('Đăng ký registry', reg.get('interpreter') is mod)

    out = mod.run('meow "from module"')
    check('Module.run()', out == 'from module', f'got {out!r}')

    data = {'code': 'meow "via bus"', 'timeout': 5.0}
    bus.emit('code.run', data)
    check('Event code.run', data.get('result', {}).get('output') == 'via bus', str(data.get('result')))
except Exception as e:
    check('Module interpreter', False, str(e))
    import traceback
    traceback.print_exc()


# 4. Loader
section('4. Loader')

try:
    from core.loader import Loader
    loader = Loader('modules', 'config.json')
    loader.load_all()
    check('Load interpreter', 'interpreter' in loader.modules)
    check('Load cli', 'cli' in loader.modules)

    loader.setup_all()
    check('Setup all', True)
except Exception as e:
    check('Loader', False, str(e))
    import traceback
    traceback.print_exc()


# 5. Files
section('5. Files hệ thống')

files_to_check = [
    'catpp.py',
    'config.json',
    'core/__init__.py',
    'core/module.py',
    'core/registry.py',
    'core/bus.py',
    'core/loader.py',
    'modules/interpreter/module.py',
    'modules/server/module.py',
    'modules/cli/module.py',
    'interpreter.py',
    'server.py',
    'static/index.html',
]
for f in files_to_check:
    check(f'  {f}', os.path.exists(os.path.join(ROOT, f)))


print()
print('═' * 50)
print(f'  KẾT QUẢ: {PASS} pass, {FAIL} fail')
print('═' * 50)

if FAIL > 0:
    print()
    print('Chi tiết lỗi:')
    for name, msg in ERRORS:
        print(f'  ✗ {name}')
        if msg: print(f'      {msg}')

sys.exit(0 if FAIL == 0 else 1)
