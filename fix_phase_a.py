#!/usr/bin/env python3
"""Phase A fixed — hoạt động trên v3.0."""
import os, sys, shutil, subprocess, re
from datetime import datetime

os.chdir(os.path.expanduser('~/catpp'))
bk = f'.backup/osdev2-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')
print(f'📦 Backup: {bk}\n')

def patch(desc, old, new, required=True):
    with open('interpreter.py', encoding='utf-8') as f:
        c = f.read()
    if new in c:
        print(f'  ○ {desc}')
        return True
    if old not in c:
        if required:
            print(f'  ✗ {desc}: anchor không tìm thấy')
            return False
        print(f'  ○ {desc}: bỏ qua (không bắt buộc)')
        return True
    c = c.replace(old, new, 1)
    with open('interpreter.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'  ✓ {desc}')
    return True

def test(name, code, expect):
    try:
        from importlib import reload
        if 'interpreter' in sys.modules: reload(sys.modules['interpreter'])
        import interpreter
        got = interpreter.run_catpp(code).strip()
        if got == expect:
            print(f'  ✓ {name}')
            return True
        print(f'  ✗ {name}: {got!r} ≠ {expect!r}')
        return False
    except Exception as e:
        print(f'  ✗ {name}: {type(e).__name__}: {e}')
        return False

# ═══ 1. KEYWORDS — dùng regex thay vì anchor cứng ═══
print('═══ 1. Thêm keyword (auto-detect) ═══')

with open('interpreter.py', encoding='utf-8') as f:
    c = f.read()

if 'struct' in c.split('KEYWORDS = ')[1].split('}')[0]:
    print('  ○ Keyword đã có')
else:
    # Tìm khối KEYWORDS và chèn từ khóa mới trước dấu }
    m = re.search(r"KEYWORDS = \{([^}]+)\}", c)
    if m:
        kw_block = m.group(1).rstrip().rstrip(',')
        new_kw = "'struct','volatile','cast','sizeof','asm',\n            'ptr','null','packed'"
        c = c[:m.start(1)] + kw_block + ',\n            ' + new_kw + '\n            ' + c[m.end(1):]
        with open('interpreter.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('  ✓ Thêm keyword')
    else:
        print('  ✗ Không parse được KEYWORDS')
        sys.exit(1)

# ═══ 2. Bit ops parser — đã OK, không cần sửa ═══
print('\n═══ 2. Bit ops precedence ═══')
patch('Bit ops precedence',
"""    def in_(self):
        l = self.cmp()
        while self.peek().type == 'IN':
            self.next(); l = ('in', l, self.cmp())
        return l
    def cmp(self):
        l = self.add()""",
"""    def in_(self):
        l = self.bit_or()
        while self.peek().type == 'IN':
            self.next(); l = ('in', l, self.bit_or())
        return l
    def bit_or(self):
        l = self.bit_xor()
        while self.peek().type == 'PIPE':
            self.next(); l = ('|', l, self.bit_xor())
        return l
    def bit_xor(self):
        l = self.bit_and()
        while self.peek().type == 'CARET':
            self.next(); l = ('^', l, self.bit_and())
        return l
    def bit_and(self):
        l = self.shift()
        while self.peek().type == 'AMP':
            self.next(); l = ('&', l, self.shift())
        return l
    def shift(self):
        l = self.cmp()
        while self.peek().type in ('SHL', 'SHR'):
            op = self.next().type; l = (op, l, self.cmp())
        return l
    def cmp(self):
        l = self.add()""")

patch('Unary tilde',
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        return self.postfix()""",
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        if self.peek().type == 'TILDE': self.next(); return ('bitnot', self.unary())
        return self.postfix()""")

# ═══ 3. Parser thêm struct/volatile/cast/sizeof/asm/null/ptr ═══
print('\n═══ 3. Parser keywords mới ═══')

patch('Parse struct/volatile',
"""        if t.type == 'CAT':""",
"""        if t.type == 'STRUCT':
            self.next()
            if self.peek().type == 'PACKED': self.next()
            name = self.expect('IDENT').value
            self.expect('NEWLINE'); self.expect('INDENT')
            fields = []; self.skip_nl()
            while self.peek().type not in ('DEDENT','EOF'):
                fname = self.expect('IDENT').value
                if self.peek().type == ':':
                    self.next(); self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(fname); self.skip_nl()
            if self.peek().type == 'DEDENT': self.next()
            return ('struct', name, fields, t.line)
        if t.type == 'VOLATILE':
            self.next()
            if self.peek().type == 'PAW': return self.stmt()
            e = self.expr(); self.expect('NEWLINE'); return ('expr', e, t.line)
        if t.type == 'CAT':""")

patch('Primary: cast/sizeof/asm/null/ptr',
"""        if t.type == 'HUNGRY': return ('null',)""",
"""        if t.type == 'HUNGRY': return ('null',)
        if t.type == 'NULL': return ('num', 0)
        if t.type == 'PTR': return ('var', 'ptr')
        if t.type == 'CAST':
            self.expect('(')
            type_name = self.expect('IDENT').value
            self.expect(',')
            value = self.expr()
            self.expect(')')
            return ('cast', type_name, value)
        if t.type == 'SIZEOF':
            self.expect('(')
            if self.peek().type == 'IDENT' and self.peek(1).type == ')':
                name = self.next().value; self.expect(')')
                return ('sizeof_type', name)
            e = self.expr(); self.expect(')')
            return ('sizeof', e)
        if t.type == 'ASM':
            self.expect('(')
            asm_str = self.expect('STRING').value
            self.expect(')')
            return ('asm', asm_str)""")

# ═══ 4. Runtime — sửa anchor để phù hợp v3.0 ═══
print('\n═══ 4. Runtime bit ops ═══')

# Trong v3.0, eval binop bắt đầu bằng:
#   if t in ('+','-',...):
#       l = eval_...
#       r = eval_...
#       if t == '+':
# Chèn bit ops TRƯỚC dòng đó

patch('Eval bit ops',
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""",
"""    if t in ('&','|','^','<<','>>'):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        try:
            a = int(l); b = int(r)
        except (ValueError, TypeError):
            raise CatError("Bit op yeu cau so nguyen")
        return {'&': a & b, '|': a | b, '^': a ^ b,
                '<<': a << b, '>>': a >> b}[t]
    if t == 'bitnot':
        v = eval_(n[1], env, out, rt)
        try: return ~int(v)
        except (ValueError, TypeError): raise CatError("~ yeu cau so nguyen")
    if t == 'cast':
        return do_cast(n[1], eval_(n[2], env, out, rt))
    if t == 'sizeof':
        return size_of_value(eval_(n[1], env, out, rt))
    if t == 'sizeof_type':
        return size_of_type(n[1])
    if t == 'asm':
        return None
    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""")

patch('cast/sizeof helpers',
"""def call_method(inst, name, args, out, rt):""",
"""TYPE_SIZES = {'i8':1,'u8':1,'i16':2,'u16':2,'i32':4,'u32':4,
              'i64':8,'u64':8,'int':8,'float':8,'bool':1,'ptr':8,
              'char':1,'byte':1,'str':8}

def do_cast(type_name, v):
    t = type_name.lower()
    if t in ('i8','i16','i32','i64','int','u8','u16','u32','u64','byte','char'):
        try: return int(v) if v is not None else 0
        except: return 0
    if t == 'float':
        try: return float(v) if v is not None else 0.0
        except: return 0.0
    if t == 'bool': return bool(v)
    if t == 'str': return str(v)
    if t == 'ptr':
        try: return int(v) if v is not None else 0
        except: return 0
    return v

def size_of_value(v):
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 8
    if isinstance(v, float): return 8
    if isinstance(v, str): return len(v)
    if isinstance(v, list): return len(v) * 8
    if isinstance(v, dict): return len(v) * 8
    return 8

def size_of_type(name):
    return TYPE_SIZES.get(name.lower(), 8)

def call_method(inst, name, args, out, rt):""")

# Runtime struct — dùng anchor chung hơn
with open('interpreter.py', encoding='utf-8') as f:
    c = f.read()

if "elif t == 'struct':" not in c:
    # Tìm dòng "elif t == 'class':"
    m = re.search(r"(\n        elif t == 'class':)", c)
    if m:
        insert = """
        elif t == 'struct':
            name, fields = s[1], s[2]
            env.define(name, ClassObj(name, None, fields, {}, env))"""
        c = c[:m.start(1)] + insert + c[m.start(1):]
        with open('interpreter.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print('  ✓ Runtime struct')
    else:
        print('  ✗ Không tìm thấy anchor class')
else:
    print('  ○ Runtime struct (đã có)')

# ═══ 5. Syntax check ═══
print('\n═══ 5. Syntax ═══')
try:
    with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
    print('  ✓ syntax OK')
except SyntaxError as e:
    print(f'  ✗ dòng {e.lineno}: {e.msg}')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

# ═══ 6. Test ═══
print('\n═══ 6. Test ═══')
tests = [
    ('bit AND',  'meow 5 & 3', '1'),
    ('bit OR',   'meow 5 | 2', '7'),
    ('bit XOR',  'meow 5 ^ 3', '6'),
    ('bit NOT',  'meow ~0', '-1'),
    ('shift left','meow 1 << 4', '16'),
    ('shift right','meow 256 >> 4', '16'),
    ('mask',     'meow 0xFF & 0x0F', '15'),
    ('cast int', 'meow cast(int, "42")', '42'),
    ('cast str', 'meow cast(str, 42)', '42'),
    ('sizeof int', 'meow sizeof(42)', '8'),
    ('sizeof str', 'meow sizeof("hello")', '5'),
    ('sizeof type', 'meow sizeof(i32)', '4'),
    ('asm noop', 'asm("nop")\\nmeow "ok"', 'ok'),
]
all_ok = True
for n, c, e in tests:
    if not test(n, c, e): all_ok = False

if not all_ok:
    print(f'\n❌ Fail — rollback')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

# Full test
print('\n═══ 7. Full test ═══')
r = subprocess.run([sys.executable, 'tests/test_all.py'],
                   capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'v3.2 Phase A — low-level syntax: bit ops, cast, sizeof, struct, volatile, asm, ptr'],
    capture_output=True)
print(f'\n  {"✓ commit" if r2.returncode == 0 else "○ không có gì"}')

print(f"""
╔══════════════════════════════════════════════╗
║  ✅ PHASE A HOÀN TẤT                          ║
╚══════════════════════════════════════════════╝

Cú pháp mới:
  paw x = 0xFF & 0x0F          # bit AND
  paw y = 1 << 4               # shift
  paw p = cast(ptr, 0xB8000)   # pointer
  paw sz = sizeof(i32)         # size
  struct Point / x: i32 / y: i32
  volatile paw status
  asm("cli")

Backup: {bk}
""")
