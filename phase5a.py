#!/usr/bin/env python3
"""Phase 5a — Default params: purr f(a, b=10)"""
import os, sys, re, shutil, subprocess
from datetime import datetime
from importlib import reload

os.chdir(os.path.expanduser('~/catpp'))
bk = f'.backup/5a-{datetime.now().strftime("%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')

def rollback():
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')

def patch_parser(content):
    """Thêm default params vào PURR parser."""
    # Tìm block PURR parser
    pattern = r"(if t\.type == 'PURR':\s*\n\s*self\.next\(\); name = self\.expect\('IDENT'\)\.value; params = \[\]\s*\n)"
    m = re.search(pattern, content)
    if not m:
        print('  ✗ Không tìm thấy PURR parser')
        return None
    
    # Thay block params parse
    old = m.group(1)
    new = """if t.type == 'PURR':
            self.next(); name = self.expect('IDENT').value; params = []
            defaults = {}
            """
    content = content[:m.start()] + new + content[m.end():]
    
    # Bây giờ tìm dòng "while self.peek().type == 'IDENT': params.append(self.next().value)"
    # Thay bằng logic có default
    old2 = "while self.peek().type == 'IDENT': params.append(self.next().value)"
    new2 = """while self.peek().type == 'IDENT':
                pname = self.next().value
                params.append(pname)
                if self.peek().type == '=':
                    self.next()
                    defaults[pname] = self.expr()
                elif self.peek().type == ':':
                    self.next(); self.expect('IDENT').value"""
    if old2 in content:
        content = content.replace(old2, new2, 1)
        print('  ✓ Parser: while-loop với default')
    
    # Thay logic trong block ngoặc đơn
    old3 = """if self.peek().type != ')':
                    params.append(self.expect('IDENT').value)
                    if self.peek().type == ':':
                        self.next(); self.expect('IDENT').value
                    while self.peek().type == ',':
                        self.next(); params.append(self.expect('IDENT').value)
                        if self.peek().type == ':':
                            self.next(); self.expect('IDENT').value
                self.expect(')')"""
    new3 = """if self.peek().type != ')':
                    pname = self.expect('IDENT').value
                    params.append(pname)
                    if self.peek().type == '=':
                        self.next()
                        defaults[pname] = self.expr()
                    elif self.peek().type == ':':
                        self.next(); self.expect('IDENT').value
                    while self.peek().type == ',':
                        self.next()
                        pname = self.expect('IDENT').value
                        params.append(pname)
                        if self.peek().type == '=':
                            self.next()
                            defaults[pname] = self.expr()
                        elif self.peek().type == ':':
                            self.next(); self.expect('IDENT').value
                self.expect(')')"""
    if old3 in content:
        content = content.replace(old3, new3, 1)
        print('  ✓ Parser: block ngoặc với default')
    else:
        print('  ⚠ Không tìm thấy block ngoặc')
    
    # Sửa return tuple
    old4 = "return ('func', name, params, body, t.line)"
    new4 = "return ('func', name, params, defaults, body, t.line)"
    if old4 in content:
        content = content.replace(old4, new4, 1)
        print('  ✓ Return tuple (thêm defaults)')
    
    return content

def patch_runtime(content):
    """Sửa runtime đọc defaults."""
    # Tìm block func exec
    old = """        elif t == 'func':
            name, params, body = s[1], s[2], s[3]
            def fn(*args, _p=params, _b=body, _e=env, _rt=rt):
                _rt.depth += 1
                if _rt.depth > _rt.max_depth:
                    _rt.depth -= 1
                    raise CatError(f"Meo qua sau (>{_rt.max_depth})")
                local = Env(_e)
                for p, a in zip(_p, args): local.define(p, a)"""
    new = """        elif t == 'func':
            name, params, defaults, body = s[1], s[2], s[3], s[4]
            def fn(*args, _p=params, _d=defaults, _b=body, _e=env, _rt=rt):
                _rt.depth += 1
                if _rt.depth > _rt.max_depth:
                    _rt.depth -= 1
                    raise CatError(f"Meo qua sau (>{_rt.max_depth})")
                local = Env(_e)
                for i, p in enumerate(_p):
                    if i < len(args):
                        local.define(p, args[i])
                    elif p in _d:
                        local.define(p, eval_(_d[p], _e, out, _rt))
                    else:
                        raise CatError(f"Thieu tham so '{p}'")"""
    if old in content:
        content = content.replace(old, new, 1)
        print('  ✓ Runtime: bind defaults')
    else:
        print('  ✗ Không tìm thấy func exec')
        return None
    return content

# Đọc file
with open('interpreter.py', encoding='utf-8') as f:
    c = f.read()

print('═══ Patch parser ═══')
c2 = patch_parser(c)
if c2 is None:
    print('❌ Parser fail — rollback')
    rollback()
    sys.exit(1)
c = c2

print('\n═══ Patch runtime ═══')
c2 = patch_runtime(c)
if c2 is None:
    print('❌ Runtime fail — rollback')
    rollback()
    sys.exit(1)
c = c2

# Ghi
with open('interpreter.py', 'w', encoding='utf-8') as f:
    f.write(c)

# Syntax
print('\n═══ Syntax check ═══')
try:
    with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
    print('  ✓ OK')
except SyntaxError as e:
    print(f'  ✗ dòng {e.lineno}: {e.msg}')
    rollback()
    sys.exit(1)

# Test
print('\n═══ Test ═══')
import interpreter
tests = [
    ('no default', 'purr f(a, b)\n    give a + b\nmeow f(3, 4)', '7'),
    ('with default', 'purr f(a, b=10)\n    give a + b\nmeow f(5)', '15'),
    ('override default', 'purr f(a, b=10)\n    give a + b\nmeow f(5, 3)', '8'),
    ('two defaults', 'purr f(a=1, b=2)\n    give a + b\nmeow f()', '3'),
    ('default + pos', 'purr greet(name, greeting="Hello")\n    give greeting + ", " + name\nmeow greet("Tom")', 'Hello, Tom'),
    ('default override', 'purr greet(name, greeting="Hello")\n    give greeting + ", " + name\nmeow greet("Tom", "Hi")', 'Hi, Tom'),
]
all_ok = True
for n, c, e in tests:
    try:
        reload(interpreter)
        got = interpreter.run_catpp(c).strip()
        if got == e:
            print(f'  ✓ {n}')
        else:
            print(f'  ✗ {n}: {got!r} ≠ {e!r}')
            all_ok = False
    except Exception as ex:
        print(f'  ✗ {n}: {type(ex).__name__}: {ex}')
        all_ok = False

if not all_ok:
    print('\n❌ Test fail — rollback')
    rollback()
    sys.exit(1)

# Full test
print('\n═══ Full test ═══')
r = subprocess.run([sys.executable, 'tests/test_all.py'], capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

if 'fail' in r.stdout.lower() and '0 fail' not in r.stdout:
    print('\n❌ Full test fail — rollback')
    rollback()
    sys.exit(1)

# Commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase 5a — Default params: purr f(a, b=10)'], capture_output=True)
print(f'\n  {"✓ commit" if r2.returncode == 0 else "○ không có gì"}')

print("""
╔══════════════════════════════════════════════╗
║  ✅ PHASE 5a — DEFAULT PARAMS                ║
╚══════════════════════════════════════════════╝

Ví dụ:
  purr greet(name, greeting="Hello")
      give greeting + ", " + name

  meow greet("Tom")          # Hello, Tom
  meow greet("Tom", "Hi")    # Hi, Tom

  purr add(a, b=10)
      give a + b

  meow add(5)      # 15
  meow add(5, 3)   # 8
""")
