#!/usr/bin/env python3
"""Thay toàn bộ tokenize() bằng bản đầy đủ."""
import os, sys, shutil, subprocess, re
from datetime import datetime

os.chdir(os.path.expanduser('~/catpp'))
bk = f'.backup/tok-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')
print(f'📦 Backup: {bk}\n')

# Đọc file
with open('interpreter.py', encoding='utf-8') as f:
    c = f.read()

# ═══ 1. Thêm keyword mới ═══
print('1. Thêm keywords')
m = re.search(r"KEYWORDS = \{([^}]+)\}", c)
if m:
    kw = m.group(1)
    if 'struct' not in kw:
        kw_new = kw.rstrip().rstrip(',') + ",\n            'struct','volatile','cast','sizeof','asm','ptr','null','packed'"
        c = c[:m.start(1)] + kw_new + c[m.end(1):]
        print('  ✓ Đã thêm keyword')
    else:
        print('  ○ Keywords đã có')

# ═══ 2. Tìm và thay TOÀN BỘ tokenize function ═══
print('\n2. Thay tokenize()')

new_tokenize = '''def tokenize(src):
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
            # Hex / binary / decimal
            if c.isdigit() or (c == '0' and i + 1 < len(line) and line[i+1] in 'xXbB'):
                j = i
                if c == '0' and i + 1 < len(line) and line[i+1] in 'xX':
                    j = i + 2
                    while j < len(line) and line[j] in '0123456789abcdefABCDEF': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 16)), ln)); i = j; continue
                if c == '0' and i + 1 < len(line) and line[i+1] in 'bB':
                    j = i + 2
                    while j < len(line) and line[j] in '01': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 2)), ln)); i = j; continue
                while j < len(line) and (line[j].isdigit() or line[j]=='.'): j += 1
                num_str = line[i:j]
                if '.' in num_str:
                    toks.append(Tok('NUMBER', float(num_str), ln))
                else:
                    toks.append(Tok('NUMBER', int(num_str), ln))
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
            # 2-char operators
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
            # 1-char operators
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

# Replace function
m = re.search(r'def tokenize\(src\):.*?(?=\nclass Parser:)', c, re.DOTALL)
if m:
    c = c[:m.start()] + new_tokenize + '\n\n' + c[m.end():]
    print('  ✓ Đã thay tokenize()')
else:
    print('  ✗ Không tìm thấy tokenize()')
    sys.exit(1)

with open('interpreter.py', 'w', encoding='utf-8') as f:
    f.write(c)

# ═══ 3. Syntax check ═══
print('\n3. Syntax check')
try:
    with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
    print('  ✓ OK')
except SyntaxError as e:
    print(f'  ✗ dòng {e.lineno}: {e.msg}')
    shutil.copy(f'{bk}/interpreter.py', 'interpreter.py')
    sys.exit(1)

# ═══ 4. Test ═══
print('\n4. Test')
from importlib import reload
if 'interpreter' in sys.modules: reload(sys.modules['interpreter'])
import interpreter

tests = [
    ('hex',        'meow 0xFF', '255'),
    ('binary',     'meow 0b1010', '10'),
    ('int parse',  'meow 42', '42'),
    ('bit AND',    'meow 5 & 3', '1'),
    ('bit OR',     'meow 5 | 2', '7'),
    ('bit XOR',    'meow 5 ^ 3', '6'),
    ('shift L',    'meow 1 << 4', '16'),
    ('shift R',    'meow 256 >> 4', '16'),
    ('cast str',   'meow cast(str, 42)', '42'),
    ('cast int',   'meow cast(int, "42")', '42'),
]
for n, c, e in tests:
    try:
        reload(interpreter)
        got = interpreter.run_catpp(c).strip()
        if got == e:
            print(f'  ✓ {n}')
        else:
            print(f'  ✗ {n}: {got!r} ≠ {e!r}')
    except Exception as ex:
        print(f'  ✗ {n}: {type(ex).__name__}: {ex}')

# Full test
print('\n5. Full test')
r = subprocess.run([sys.executable, 'tests/test_all.py'],
                   capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'Fix tokenizer: hex, binary, int, bit ops, shift'],
    capture_output=True)
print(f'\n  {"✓ commit" if r2.returncode == 0 else "○ không có gì"}')
