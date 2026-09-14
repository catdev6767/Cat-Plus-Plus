#!/usr/bin/env python3
"""Phase A — Low-level syntax for OS dev.
Adds: bit ops, cast, sizeof, ptr, volatile, struct, asm, -> return type."""
import os, sys, shutil, subprocess
from datetime import datetime

os.chdir(os.path.expanduser('~/catpp'))
bk = f'.backup/osdev-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')
print(f'📦 Backup: {bk}\n')

def patch(desc, old, new):
    with open('interpreter.py', encoding='utf-8') as f:
        c = f.read()
    if new in c:
        print(f'  ○ {desc}')
        return True
    if old not in c:
        print(f'  ✗ {desc}: anchor không tìm thấy')
        return False
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

def syntax_ok():
    try:
        with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
        return True
    except SyntaxError as e:
        print(f'  ✗ syntax dòng {e.lineno}: {e.msg}')
        return False

# ══════════════════════════════════════════════
print('═══ 1. Lexer: bit ops + keyword mới ═══')
# ══════════════════════════════════════════════

ok = patch('Thêm keyword',
"""KEYWORDS = {'paw','meow','purr','give','hiss','tap','sit','leap','listen',
            'sniff','swat','knead','groom','of','nod','shake','hungry',
            'with','either','never','cat','me','kin','kit','litter','in',
            'match','case','use'}""",
"""KEYWORDS = {'paw','meow','purr','give','hiss','tap','sit','leap','listen',
            'sniff','swat','knead','groom','of','nod','shake','hungry',
            'with','either','never','cat','me','kin','kit','litter','in',
            'match','case','use','struct','volatile','cast','sizeof','asm',
            'ptr','null','packed'}""")

ok = patch('Thêm token & | ^ ~ << >> ->',
"""            two = line[i:i+2]
            if two == '??': toks.append(Tok('COALESCE', '??', ln)); i += 2; continue""",
"""            two = line[i:i+2]
            if two == '<<': toks.append(Tok('SHL', '<<', ln)); i += 2; continue
            if two == '>>': toks.append(Tok('SHR', '>>', ln)); i += 2; continue
            if two == '->': toks.append(Tok('ARROW_R', '->', ln)); i += 2; continue
            if c == '&': toks.append(Tok('AMP', '&', ln)); i += 1; continue
            if c == '|': toks.append(Tok('PIPE', '|', ln)); i += 1; continue
            if c == '^': toks.append(Tok('CARET', '^', ln)); i += 1; continue
            if c == '~': toks.append(Tok('TILDE', '~', ln)); i += 1; continue
            if two == '??': toks.append(Tok('COALESCE', '??', ln)); i += 2; continue""")

# ══════════════════════════════════════════════
print('\n═══ 2. Parser: precedence chain ═══')
# ══════════════════════════════════════════════

# Chèn bit_or, bit_xor, bit_and, shift vào giữa in_ và cmp
ok = patch('Bit ops precedence',
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

# Unary ~
ok = patch('Unary tilde',
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        return self.postfix()""",
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        if self.peek().type == 'TILDE': self.next(); return ('bitnot', self.unary())
        return self.postfix()""")

# cast/sizeof/asm/struct/null keyword
ok = patch('Parse struct',
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
            # volatile paw x = ... → coi như paw
            if self.peek().type == 'PAW':
                return self.stmt()
            # volatile <expr> → bỏ qua
            e = self.expr(); self.expect('NEWLINE'); return ('expr', e, t.line)
        if t.type == 'CAT':""")

# Return type -> thay vì to
ok = patch('Return type ->',
"""            if self.peek().type == 'IDENT' and self.peek().value == 'to':
                self.next(); self.expect('IDENT').value
            body = self.block(); return ('func', name, params, body, t.line)""",
"""            while self.peek().type in ('ARROW_R', 'IDENT'):
                if self.peek().type == 'ARROW_R':
                    self.next(); self.expect('IDENT').value
                elif self.peek().value == 'to':
                    self.next(); self.expect('IDENT').value
                else:
                    break
            body = self.block(); return ('func', name, params, body, t.line)""")

# cast/sizeof/asm/null/ptr trong primary
ok = patch('Primary: cast/sizeof/asm/null/ptr',
"""        if t.type == 'HUNGRY': return ('null',)""",
"""        if t.type == 'HUNGRY': return ('null',)
        if t.type == 'NULL': return ('num', 0)
        if t.type == 'PTR': return ('var', 'ptr')
        if t.type == 'CAST':
            self.expect('(')
            # Type name
            type_name = self.expect('IDENT').value
            self.expect(',')
            value = self.expr()
            self.expect(')')
            return ('cast', type_name, value)
        if t.type == 'SIZEOF':
            self.expect('(')
            # Có thể là type name hoặc expr
            save = self.pos
            if self.peek().type == 'IDENT' and self.peek(1).type == ')':
                name = self.next().value; self.expect(')')
                return ('sizeof_type', name)
            self.pos = save
            e = self.expr(); self.expect(')')
            return ('sizeof', e)
        if t.type == 'ASM':
            self.expect('(')
            asm_str = self.expect('STRING').value
            self.expect(')')
            return ('asm', asm_str)""")

# ══════════════════════════════════════════════
print('\n═══ 3. Runtime: eval bit ops + cast + sizeof ═══')
# ══════════════════════════════════════════════

# Bit ops in binop tuple
ok = patch('Eval bit ops',
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if isinstance(l, Instance):""",
"""    if t in ('&','|','^','<<','>>'):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        try:
            a = int(l); b = int(r)
        except (ValueError, TypeError):
            raise CatError(f"Bit op yêu cầu số nguyên")
        return {'&': a & b, '|': a | b, '^': a ^ b,
                '<<': a << b, '>>': a >> b}[t]
    if t == 'bitnot':
        v = eval_(n[1], env, out, rt)
        try: return ~int(v)
        except (ValueError, TypeError): raise CatError("~ yêu cầu số nguyên")
    if t == 'cast':
        type_name, expr = n[1], n[2]
        v = eval_(expr, env, out, rt)
        return do_cast(type_name, v)
    if t == 'sizeof':
        v = eval_(n[1], env, out, rt)
        return size_of_value(v)
    if t == 'sizeof_type':
        return size_of_type(n[1])
    if t == 'asm':
        # Interpreter không chạy asm — no-op
        return None
    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if isinstance(l, Instance):""")

# cast + sizeof functions
ok = patch('cast/sizeof helpers',
"""def call_method(inst, name, args, out, rt):""",
"""TYPE_SIZES = {'i8':1,'u8':1,'i16':2,'u16':2,'i32':4,'u32':4,
              'i64':8,'u64':8,'int':8,'float':8,'bool':1,'ptr':8,
              'char':1,'byte':1}

def do_cast(type_name, v):
    t = type_name.lower()
    if t in ('i8','i16','i32','i64','int','u8','u16','u32','u64',
             'byte','char'):
        return int(v) if v is not None else 0
    if t == 'float':
        return float(v) if v is not None else 0.0
    if t == 'bool':
        return bool(v)
    if t == 'str':
        return str(v)
    if t == 'ptr':
        return int(v) if v is not None else 0
    return v

def size_of_value(v):
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 8
    if isinstance(v, float): return 8
    if isinstance(v, str): return len(v)
    if isinstance(v, list): return len(v) * 8
    if isinstance(v, dict): return len(v) * 8
    if isinstance(v, Instance):
        total = 0
        for f in v.cls.fields:
            total += 8
        return total
    return 8

def size_of_type(name):
    return TYPE_SIZES.get(name.lower(), 8)

def call_method(inst, name, args, out, rt):""")

# Struct runtime
ok = patch('Runtime struct',
"""        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]""",
"""        elif t == 'struct':
            name, fields = s[1], s[2]
            env.define(name, ClassObj(name, None, fields, {}, env))
        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]""")

# ══════════════════════════════════════════════
print('\n═══ 4. Test ═══')
# ══════════════════════════════════════════════

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
    ('struct', 'struct Point\\n    x: i32\\n    y: i32\\npaw p = Point(3, 4)\\nmeow p.x', '3'),
    ('volatile', 'volatile paw x = 5\\nmeow x', '5'),
    ('ptr cast', 'paw p = cast(ptr, 4096)\\nmeow p', '4096'),
    ('asm noop', 'asm("nop")\\nmeow "ok"', 'ok'),
]

all_ok = True
for n, c, e in tests:
    if not test(n, c, e): all_ok = False

if not syntax_ok(): all_ok = False

if not all_ok:
    print(f'\n❌ Fail — rollback')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

# Full test
print('\n═══ 5. Full test ═══')
r = subprocess.run([sys.executable, 'tests/test_all.py'],
                   capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'v3.2 — Low-level primitives: bit ops, cast, sizeof, ptr, struct, volatile, asm'],
    capture_output=True)
print(f'\n  {"✓ commit" if r2.returncode == 0 else "○ không có gì"}')

print(f"""
╔══════════════════════════════════════════════╗
║  PHASE A HOÀN TẤT — Cú pháp OS-dev           ║
╚══════════════════════════════════════════════╝

Đã thêm:
  ✓ Bit ops:    & | ^ ~ << >>
  ✓ cast():     cast(ptr, 0xB8000)
  ✓ sizeof():   sizeof(i32) → 4
  ✓ struct:     struct Point / x: i32 / y: i32
  ✓ volatile:   volatile paw status
  ✓ asm("..."): inline assembly (placeholder)
  ✓ ptr:        kiểu con trỏ
  ✓ null:       alias của hungry
  ✓ ->:         return type

Ví dụ VGA (prototype):
  paw vga = cast(ptr, 0xB8000)
  paw color = (0x0F << 8) | ord("H")
  # Phase B sẽ dịch thành: *(u16*)0xB8000 = color

⚠ Phase B (transpiler Cat++ → C) chưa làm.
  Code này chỉ PARSE được, chưa compile ra binary.
""")
