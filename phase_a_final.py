#!/usr/bin/env python3
"""Phase A final — tất cả trong 1 script."""
import os, sys, shutil, subprocess, re
from datetime import datetime

os.chdir(os.path.expanduser('~/catpp'))
bk = f'.backup/phaseA-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')
print(f'📦 Backup: {bk}\n')

def patch(desc, old, new, req=True):
    with open('interpreter.py', encoding='utf-8') as f:
        c = f.read()
    if new in c:
        print(f'  ○ {desc}'); return True
    if old not in c:
        if req: print(f'  ✗ {desc}'); return False
        print(f'  ○ {desc}'); return True
    c = c.replace(old, new, 1)
    with open('interpreter.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'  ✓ {desc}')
    return True

# ═══ 1. KEYWORDS ═══
print('1. Keywords')
with open('interpreter.py', encoding='utf-8') as f:
    c = f.read()
m = re.search(r"KEYWORDS = \{([^}]+)\}", c)
if m and 'struct' not in m.group(1):
    kw = m.group(1).rstrip().rstrip(',')
    c = c[:m.start(1)] + kw + ",\n            'struct','volatile','cast','sizeof','asm','ptr','null','packed'" + c[m.end(1):]
    with open('interpreter.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print('  ✓ Thêm keyword')
else:
    print('  ○ Đã có')

# ═══ 2. TOKENIZER ═══
print('\n2. Tokenizer')
new_tok = '''def tokenize(src):
    toks, indent_stack = [], [0]
    lines = src.split('\\n')
    for ln, line in enumerate(lines, 1):
        stripped = line.lstrip(' \\t')
        if not stripped or stripped.startswith('#'): continue
        indent = len(line) - len(line.lstrip(' \\t'))
        if indent > indent_stack[-1]:
            indent_stack.append(indent); toks.append(Tok('INDENT','',ln))
        while indent < indent_stack[-1]:
            indent_stack.pop(); toks.append(Tok('DEDENT','',ln))
        i = 0
        while i < len(line):
            c = line[i]
            if c in ' \\t': i += 1; continue
            if c == '#': break
            if c.isdigit():
                j = i
                if i+1 < len(line) and line[i+1] in 'xX':
                    j = i + 2
                    while j < len(line) and line[j] in '0123456789abcdefABCDEF': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 16)), ln)); i = j; continue
                if i+1 < len(line) and line[i+1] in 'bB':
                    j = i + 2
                    while j < len(line) and line[j] in '01': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 2)), ln)); i = j; continue
                while j < len(line) and (line[j].isdigit() or line[j]=='.'): j += 1
                ns = line[i:j]
                toks.append(Tok('NUMBER', float(ns) if '.' in ns else int(ns), ln))
                i = j; continue
            if c == '"':
                j, s = i+1, ''
                while j < len(line) and line[j] != '"':
                    if line[j]=='\\\\' and j+1<len(line):
                        s += {'n':'\\n','t':'\\t','"':'"','\\\\':'\\\\'}.get(line[j+1], line[j+1]); j += 2
                    else: s += line[j]; j += 1
                toks.append(Tok('STRING', s, ln)); i = j+1; continue
            if c.isalpha() or c == '_':
                j = i
                while j < len(line) and (line[j].isalnum() or line[j]=='_'): j += 1
                w = line[i:j]
                toks.append(Tok(w.upper() if w in KEYWORDS else 'IDENT', w, ln)); i = j; continue
            two = line[i:i+2]
            if two == '<<': toks.append(Tok('SHL', '<<', ln)); i += 2; continue
            if two == '>>': toks.append(Tok('SHR', '>>', ln)); i += 2; continue
            if two == '->': toks.append(Tok('ARROW_R', '->', ln)); i += 2; continue
            if two == '??': toks.append(Tok('COALESCE', '??', ln)); i += 2; continue
            if two in ('+=','-=','*=','/=','%='):
                toks.append(Tok('OP_ASSIGN', two, ln)); i += 2; continue
            if two == '++': toks.append(Tok('INC', '++', ln)); i += 2; continue
            if two == '--': toks.append(Tok('DEC', '--', ln)); i += 2; continue
            if two == '=>': toks.append(Tok('ARROW', '=>', ln)); i += 2; continue
            if two in ('==','!=','<=','>='): toks.append(Tok(two, two, ln)); i += 2; continue
            if c == '&': toks.append(Tok('AMP', '&', ln)); i += 1; continue
            if c == '|': toks.append(Tok('PIPE', '|', ln)); i += 1; continue
            if c == '^': toks.append(Tok('CARET', '^', ln)); i += 1; continue
            if c == '~': toks.append(Tok('TILDE', '~', ln)); i += 1; continue
            if c == '?': toks.append(Tok('QUESTION', '?', ln)); i += 1; continue
            if c in '+-*/%=<>()[]{}.,:': toks.append(Tok(c, c, ln)); i += 1; continue
            i += 1
        toks.append(Tok('NEWLINE','',ln))
    while len(indent_stack) > 1:
        indent_stack.pop(); toks.append(Tok('DEDENT','',len(lines)))
    toks.append(Tok('EOF','',0))
    return toks'''
with open('interpreter.py', encoding='utf-8') as f: c = f.read()
m = re.search(r'def tokenize\(src\):.*?(?=\nclass Parser:)', c, re.DOTALL)
if m:
    c = c[:m.start()] + new_tok + '\n\n' + c[m.end():]
    with open('interpreter.py', 'w', encoding='utf-8') as f: f.write(c)
    print('  ✓ Thay tokenize')

# ═══ 3. PARSER ═══
print('\n3. Parser')
patch('Bit precedence',
"""    def in_(self):
        l = self.cmp()
        while self.peek().type == 'IN':
            self.next(); l = ('in', l, self.cmp())
        return l""",
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
        while self.peek().type in ('SHL','SHR'):
            op = self.next().type; l = (op, l, self.cmp())
        return l""")

patch('Unary tilde',
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        return self.postfix()""",
"""    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        if self.peek().type == 'TILDE': self.next(); return ('bitnot', self.unary())
        return self.postfix()""")

patch('Struct/volatile',
"""        if t.type == 'CAT':""",
"""        if t.type == 'STRUCT':
            self.next()
            if self.peek().type == 'PACKED': self.next()
            name = self.expect('IDENT').value
            self.expect('NEWLINE'); self.expect('INDENT')
            fields = []; self.skip_nl()
            while self.peek().type not in ('DEDENT','EOF'):
                fname = self.expect('IDENT').value
                if self.peek().type == ':': self.next(); self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(fname); self.skip_nl()
            if self.peek().type == 'DEDENT': self.next()
            return ('struct', name, fields, t.line)
        if t.type == 'VOLATILE':
            self.next()
            if self.peek().type == 'PAW': return self.stmt()
            e = self.expr(); self.expect('NEWLINE'); return ('expr', e, t.line)
        if t.type == 'CAT':""")

patch('Primary cast/sizeof/asm',
"""        if t.type == 'HUNGRY': return ('null',)""",
"""        if t.type == 'HUNGRY': return ('null',)
        if t.type == 'NULL': return ('num', 0)
        if t.type == 'PTR': return ('var', 'ptr')
        if t.type == 'CAST':
            self.expect('(')
            tn = self.expect('IDENT').value
            self.expect(',')
            v = self.expr()
            self.expect(')')
            return ('cast', tn, v)
        if t.type == 'SIZEOF':
            self.expect('(')
            if self.peek().type == 'IDENT' and self.peek(1).type == ')':
                nm = self.next().value; self.expect(')')
                return ('sizeof_type', nm)
            e = self.expr(); self.expect(')')
            return ('sizeof', e)
        if t.type == 'ASM':
            self.expect('(')
            s = self.expect('STRING').value
            self.expect(')')
            return ('asm', s)""")

# ═══ 4. RUNTIME ═══
print('\n4. Runtime')
patch('Eval bit ops (fix SHL/SHR)',
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""",
"""    if t in ('&','|','^','<<','>>','SHL','SHR'):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        try: a = int(l); b = int(r)
        except (ValueError, TypeError): raise CatError("Bit op yeu cau so nguyen")
        return {'&': a&b, '|': a|b, '^': a^b,
                '<<': a<<b, '>>': a>>b,
                'SHL': a<<b, 'SHR': a>>b}[t]
    if t == 'bitnot':
        v = eval_(n[1], env, out, rt)
        try: return ~int(v)
        except (ValueError, TypeError): raise CatError("~ yeu cau so nguyen")
    if t == 'cast': return do_cast(n[1], eval_(n[2], env, out, rt))
    if t == 'sizeof': return size_of_value(eval_(n[1], env, out, rt))
    if t == 'sizeof_type': return size_of_type(n[1])
    if t == 'asm': return None
    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""")

patch('Helpers',
"""def call_method(inst, name, args, out, rt):""",
"""TYPE_SIZES = {'i8':1,'u8':1,'i16':2,'u16':2,'i32':4,'u32':4,
              'i64':8,'u64':8,'int':8,'float':8,'bool':1,'ptr':8,
              'char':1,'byte':1,'str':8}

def do_cast(t, v):
    t = t.lower()
    if t in ('i8','i16','i32','i64','int','u8','u16','u32','u64','byte','char'):
        try: return int(v) if v is not None else 0
        except: return 0
    if t == 'float':
        try: return float(v) if v is not None else 0.0
        except: return 0.0
    if t == 'bool': return bool(v)
    if t == 'str':
        if isinstance(v, float) and v == int(v): return str(int(v))
        return str(v)
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

def size_of_type(n):
    return TYPE_SIZES.get(n.lower(), 8)

def call_method(inst, name, args, out, rt):""")

# Struct runtime
with open('interpreter.py', encoding='utf-8') as f: c = f.read()
if "elif t == 'struct':" not in c:
    m = re.search(r"(\n        elif t == 'class':)", c)
    if m:
        c = c[:m.start(1)] + "\n        elif t == 'struct':\n            name, fields = s[1], s[2]\n            env.define(name, ClassObj(name, None, fields, {}, env))" + c[m.start(1):]
        with open('interpreter.py', 'w', encoding='utf-8') as f: f.write(c)
        print('  ✓ Runtime struct')

# ═══ 5. TEST ═══
print('\n5. Test')
try:
    with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
    print('  ✓ syntax OK')
except SyntaxError as e:
    print(f'  ✗ dòng {e.lineno}: {e.msg}')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

from importlib import reload
tests = [
    ('hex', 'meow 0xFF', '255'),
    ('bit AND', 'meow 5 & 3', '1'),
    ('bit OR',  'meow 5 | 2', '7'),
    ('bit XOR', 'meow 5 ^ 3', '6'),
    ('bit NOT', 'meow ~0', '-1'),
    ('shift L', 'meow 1 << 4', '16'),
    ('shift R', 'meow 256 >> 4', '16'),
    ('mask',    'meow 0xFF & 0x0F', '15'),
    ('cast int','meow cast(int, "42")', '42'),
    ('cast str','meow cast(str, 42)', '42'),
    ('sizeof',  'meow sizeof(i32)', '4'),
    ('asm',     'asm("nop")\nmeow "ok"', 'ok'),
    ('struct',  'struct P\n    x: i32\n    y: i32\nmeow sizeof(P)', '8'),
    ('volatile','volatile paw x = 5\nmeow x', '5'),
]
all_ok = True
for n, code, e in tests:
    try:
        reload(sys.modules['interpreter']) if 'interpreter' in sys.modules else None
        import interpreter
        got = interpreter.run_catpp(code).strip()
        if got == e: print(f'  ✓ {n}')
        else: print(f'  ✗ {n}: {got!r} ≠ {e!r}'); all_ok = False
    except Exception as ex:
        print(f'  ✗ {n}: {type(ex).__name__}: {ex}'); all_ok = False

if not all_ok:
    print(f'\n❌ Fail — rollback')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

print('\n6. Full test')
r = subprocess.run([sys.executable, 'tests/test_all.py'], capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'Phase A — low-level syntax hoàn tất'], capture_output=True)
print(f'\n  {"✓ commit" if r2.returncode == 0 else "○ không có gì"}')
