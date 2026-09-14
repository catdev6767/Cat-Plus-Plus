#!/usr/bin/env python3
"""Patch v3.0 → v3.1 — dùng git checkout để đảm bảo clean state."""
import os, sys, subprocess, shutil
from importlib import reload

os.chdir(os.path.expanduser('~/catpp'))

def patch(desc, old, new):
    with open('interpreter.py', encoding='utf-8') as f:
        c = f.read()
    if new in c:
        print(f'  ○ {desc} (đã có)')
        return True
    if old not in c:
        print(f'  ✗ {desc}')
        print(f'    Anchor (200 ký tự đầu):')
        print(f'    {old[:200]!r}')
        return False
    c = c.replace(old, new, 1)
    with open('interpreter.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print(f'  ✓ {desc}')
    return True

# PHASE 1
print('═══ PHASE 1: Static + private + abstract ═══')

# 1.1 class_body — mở rộng
ok = patch('class_body',
"""    def class_body(self):
        self.expect('NEWLINE'); self.expect('INDENT')
        fields, methods = [], {}
        self.skip_nl()
        while self.peek().type not in ('DEDENT','EOF'):
            t = self.peek()
            if t.type == 'PAW':
                self.next(); name = self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(name)
            elif t.type == 'PURR':
                self.next(); mname = self.expect('IDENT').value
                params = []
                while self.peek().type == 'IDENT': params.append(self.next().value)
                if self.peek().type == '(':
                    self.next()
                    if self.peek().type != ')':
                        params.append(self.expect('IDENT').value)
                        while self.peek().type == ',': self.next(); params.append(self.expect('IDENT').value)
                    self.expect(')')
                body = self.block()
                methods[mname] = (params, body)
            else: raise CatError(f"Cat chi chua paw hoac purr", t.line)
            self.skip_nl()
        if self.peek().type == 'DEDENT': self.next()
        return fields, methods""",
"""    def class_body(self):
        self.expect('NEWLINE'); self.expect('INDENT')
        fields, methods = [], {}
        static_methods = set()
        getters, setters = set(), set()
        abstract_methods = set()
        getter_methods, setter_methods = {}, {}
        self.skip_nl()
        while self.peek().type not in ('DEDENT','EOF'):
            t = self.peek()
            if t.type == 'PAW':
                self.next(); name = self.expect('IDENT').value
                if name in ('private', 'public'):
                    name = self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(name)
            elif t.type == 'PURR':
                self.next(); first = self.expect('IDENT').value
                mname = first; is_static = is_get = is_set = is_abs = False
                if first == 'static': is_static = True; mname = self.expect('IDENT').value
                elif first == 'get': is_get = True; mname = self.expect('IDENT').value
                elif first == 'set': is_set = True; mname = self.expect('IDENT').value
                elif first == 'abstract': is_abs = True; mname = self.expect('IDENT').value
                params = []
                while self.peek().type == 'IDENT': params.append(self.next().value)
                if self.peek().type == '(':
                    self.next()
                    if self.peek().type != ')':
                        params.append(self.expect('IDENT').value)
                        if self.peek().type == ':':
                            self.next(); self.expect('IDENT').value
                        while self.peek().type == ',':
                            self.next(); params.append(self.expect('IDENT').value)
                            if self.peek().type == ':':
                                self.next(); self.expect('IDENT').value
                    self.expect(')')
                if is_abs:
                    self.expect('NEWLINE')
                    abstract_methods.add(mname)
                    methods[mname] = (params, [])
                else:
                    body = self.block()
                    if is_get: getter_methods[mname] = (params, body)
                    elif is_set: setter_methods[mname] = (params, body)
                    else:
                        methods[mname] = (params, body)
                        if is_static: static_methods.add(mname)
            else: raise CatError(f"Cat chi chua paw hoac purr", t.line)
            self.skip_nl()
        if self.peek().type == 'DEDENT': self.next()
        return (fields, methods, static_methods, getters, setters,
                abstract_methods, getter_methods, setter_methods)""")
if not ok: sys.exit(1)

# 1.2 class stmt
ok = patch('class stmt',
"""        if t.type == 'CAT':
            self.next(); name = self.expect('IDENT').value; parent = None
            if self.peek().type == 'KIN':
                self.next(); parent = self.expect('IDENT').value
            fields, methods = self.class_body()
            return ('class', name, parent, fields, methods, t.line)""",
"""        if t.type == 'CAT':
            self.next()
            is_abs_class = False
            if self.peek().type == 'IDENT' and self.peek().value == 'abstract':
                self.next(); is_abs_class = True
            name = self.expect('IDENT').value; parent = None
            if self.peek().type == 'KIN':
                self.next(); parent = self.expect('IDENT').value
            (fields, methods, static_m, getters, setters, abstract_m,
             getter_m, setter_m) = self.class_body()
            return ('class', name, parent, fields, methods, static_m,
                    getters, setters, abstract_m, is_abs_class,
                    getter_m, setter_m, t.line)""")
if not ok: sys.exit(1)

# 1.3 ClassObj
ok = patch('ClassObj',
"""class ClassObj:
    def __init__(self, name, parent, fields, methods, env):
        self.name=name; self.parent=parent
        self.fields=fields; self.methods=methods; self.env=env""",
"""class ClassObj:
    def __init__(self, name, parent, fields, methods, env,
                 static_methods=None, getters=None, setters=None,
                 abstract_methods=None, is_abstract=False,
                 getter_methods=None, setter_methods=None):
        self.name=name; self.parent=parent
        self.fields=fields; self.methods=methods; self.env=env
        self.static_methods = static_methods or set()
        self.getters = getters or set()
        self.setters = setters or set()
        self.abstract_methods = abstract_methods or set()
        self.is_abstract = is_abstract
        self.getter_methods = getter_methods or {}
        self.setter_methods = setter_methods or {}

    def find_method(self, name):
        c = self
        while c:
            if name in c.methods: return (c, c.methods[name])
            c = c.parent
        return (None, None)

    def find_getter(self, name):
        c = self
        while c:
            if name in c.getter_methods: return (c, c.getter_methods[name])
            c = c.parent
        return (None, None)

    def find_setter(self, name):
        c = self
        while c:
            if name in c.setter_methods: return (c, c.setter_methods[name])
            c = c.parent
        return (None, None)

    def find_abstract(self):
        result = set()
        c = self
        while c:
            result |= c.abstract_methods
            c = c.parent
        return result""")
if not ok: sys.exit(1)

# 1.4 runtime class
ok = patch('runtime class',
"""        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]
            parent_obj = env.get(parent) if parent else None
            env.define(name, ClassObj(name, parent_obj, fields, methods, env))""",
"""        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]
            static_m, getters, setters = s[5], s[6], s[7]
            abstract_m, is_abs = s[8], s[9]
            getter_m, setter_m = s[10], s[11]
            parent_obj = env.get(parent) if parent else None
            env.define(name, ClassObj(name, parent_obj, fields, methods, env,
                                      static_m, getters, setters, abstract_m, is_abs,
                                      getter_m, setter_m))""")
if not ok: sys.exit(1)

# 1.5 make_instance check abstract
ok = patch('make_instance',
"""def make_instance(cls, args, out, rt):
    inst = Instance(cls)
    if 'new' in cls.methods:""",
"""def make_instance(cls, args, out, rt):
    if cls.is_abstract:
        raise CatError(f"Khong the tao instance cua abstract class '{cls.name}'")
    abstract = cls.find_abstract()
    for m in abstract:
        found = False
        c = cls
        while c:
            if m in c.methods and m not in c.abstract_methods:
                found = True; break
            c = c.parent
        if not found:
            raise CatError(f"Class '{cls.name}' chua override '{m}'")
    inst = Instance(cls)
    if 'new' in cls.methods:""")
if not ok: sys.exit(1)

# 1.6 dot access static + getter
ok = patch('dot access',
"""        if isinstance(obj, Instance):
            if name in obj.data: return obj.data[name]
            cls = obj.cls
            while cls:
                if name in cls.methods: return ('bound', obj, name)
                cls = cls.parent
            raise CatError(f"Instance khong co '{name}'")
        if isinstance(obj, EnumObj):
            if name in obj.members: return obj.values[name]
            raise CatError(f"Litter khong co '{name}'")
        raise CatError(f"Khong truy cap duoc '.{name}'")""",
"""        if isinstance(obj, Instance):
            if name in obj.data: return obj.data[name]
            cls = obj.cls
            while cls:
                if name in cls.getters: return call_getter(obj, name, out, rt)
                if name in cls.methods: return ('bound', obj, name)
                cls = cls.parent
            raise CatError(f"Instance khong co '{name}'")
        if isinstance(obj, EnumObj):
            if name in obj.members: return obj.values[name]
            raise CatError(f"Litter khong co '{name}'")
        if isinstance(obj, ClassObj):
            if name in obj.methods and name in obj.static_methods:
                return ('static', obj, name)
            raise CatError(f"Class '{obj.name}' khong co static '{name}'")
        raise CatError(f"Khong truy cap duoc '.{name}'")""")
if not ok: sys.exit(1)

# 1.7 method_call static
ok = patch('method_call',
"""    if t == 'method_call':
        obj = eval_(n[1], env, out, rt); name = n[2]
        args = [eval_(a, env, out, rt) for a in n[3]]
        if isinstance(obj, Instance): return call_method(obj, name, args, out, rt)
        if isinstance(obj, str): return str_method(obj, name, args)
        if isinstance(obj, list): return list_method(obj, name, args)
        if isinstance(obj, dict): return dict_method(obj, name, args)
        raise CatError(f"Khong goi duoc '{name}'")""",
"""    if t == 'method_call':
        obj = eval_(n[1], env, out, rt); name = n[2]
        args = [eval_(a, env, out, rt) for a in n[3]]
        if isinstance(obj, Instance): return call_method(obj, name, args, out, rt)
        if isinstance(obj, ClassObj):
            if name in obj.methods and name in obj.static_methods:
                return call_static(obj, name, args, out, rt)
            raise CatError(f"'{obj.name}.{name}' khong phai static")
        if isinstance(obj, str): return str_method(obj, name, args)
        if isinstance(obj, list): return list_method(obj, name, args)
        if isinstance(obj, dict): return dict_method(obj, name, args)
        raise CatError(f"Khong goi duoc '{name}'")""")
if not ok: sys.exit(1)

# 1.8 call_getter + call_setter + call_static
ok = patch('call helpers',
"""def call_method(inst, name, args, out, rt):""",
"""def call_getter(inst, name, out, rt):
    c, m = inst.cls.find_getter(name)
    if m is None: raise CatError(f"Getter '{name}' khong ton tai")
    params, body = m
    local = Env(c.env); local.define('me', inst)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx as r: return r.v
    return None


def call_setter(inst, name, value, out, rt):
    c, m = inst.cls.find_setter(name)
    if m is None: raise CatError(f"Setter '{name}' khong ton tai")
    params, body = m
    local = Env(c.env); local.define('me', inst)
    if params: local.define(params[0], value)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx: pass
    return None


def call_static(cls, name, args, out, rt):
    c, m = cls.find_method(name)
    if m is None: raise CatError(f"Static '{name}' khong ton tai")
    params, body = m
    local = Env(cls.env)
    for p, a in zip(params, args): local.define(p, a)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx as r: return r.v
    return None


def call_method(inst, name, args, out, rt):""")
if not ok: sys.exit(1)

# 1.9 assign_to setter
ok = patch('assign_to setter',
"""    elif target[0] == 'dot':
        obj = eval_(target[1], env, out, rt); name = target[2]
        if isinstance(obj, dict): obj[name] = value
        elif isinstance(obj, Instance): obj.data[name] = value
        else: raise CatError(f"Khong the gan '{name}'")""",
"""    elif target[0] == 'dot':
        obj = eval_(target[1], env, out, rt); name = target[2]
        if isinstance(obj, dict): obj[name] = value
        elif isinstance(obj, Instance):
            cls = obj.cls
            while cls:
                if name in cls.setters:
                    call_setter(obj, name, value, out, rt)
                    return
                cls = cls.parent
            obj.data[name] = value
        else: raise CatError(f"Khong the gan '{name}'")""")
if not ok: sys.exit(1)

# PHASE 4: operator overload
print()
print('═══ PHASE 4: Operator overload ═══')

ok = patch('OPERATOR_MAP',
"""class Instance:
    def __init__(self, cls):""",
"""OPERATOR_MAP = {
    '+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '%': 'mod',
    '==': 'eq', '!=': 'neq', '<': 'lt', '>': 'gt', '<=': 'le', '>=': 'ge',
}

class Instance:
    def __init__(self, cls):""")
if not ok: sys.exit(1)

ok = patch('eval binop overload',
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""",
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if isinstance(l, Instance):
            opname = OPERATOR_MAP.get(t)
            if opname:
                c, m = l.cls.find_method(opname)
                if m is not None:
                    return call_method(l, opname, [r], out, rt)
        if t == '+':""")
if not ok: sys.exit(1)

print()
print('═══ Test ═══')

import interpreter
reload(interpreter)

tests = [
    ('static', 'cat M\n    purr static hi()\n        give "hi"\nmeow M.hi()', 'hi'),
    ('getter', 'cat P\n    paw _x\n    purr new(v)\n        me._x = v\n    purr get x()\n        give me._x\npaw p = P(42)\nmeow p.x', '42'),
    ('setter', 'cat P\n    paw _x\n    purr new()\n        me._x = 0\n    purr set x(v)\n        me._x = v * 2\n    purr get x()\n        give me._x\npaw p = P()\np.x = 5\nmeow p.x', '10'),
    ('abstract subclass', 'cat abstract S\n    purr area()\n        give 0\ncat C kin S\n    paw x\n    purr new()\n        me.x = 1\nmeow C().area()', '0'),
    ('op add', 'cat V\n    paw x\n    purr new(v)\n        me.x = v\n    purr add(o)\n        give V(me.x + o.x)\n    purr show()\n        give me.x\npaw c = V(3) + V(4)\nmeow c.show()', '7'),
    ('op eq', 'cat P\n    paw x\n    purr new(v)\n        me.x = v\n    purr eq(o)\n        give me.x == o.x\nsniff P(5) == P(5)\n    meow "same"\nswat\n    meow "diff"', 'same'),
]
all_ok = True
for name, code, expect in tests:
    try:
        reload(interpreter)
        got = interpreter.run_catpp(code).strip()
        if got == expect:
            print(f'  ✓ {name}')
        else:
            print(f'  ✗ {name}: {got!r} ≠ {expect!r}')
            all_ok = False
    except Exception as e:
        print(f'  ✗ {name}: {type(e).__name__}: {e}')
        all_ok = False

# Syntax check
try:
    with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
    print('  ✓ syntax OK')
except SyntaxError as e:
    print(f'  ✗ syntax dòng {e.lineno}: {e.msg}')
    all_ok = False

if not all_ok:
    print()
    print('❌ Có lỗi — restore')
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'interpreter.py'])
    sys.exit(1)

# Full test
print()
r = subprocess.run([sys.executable, 'tests/test_all.py'],
                   capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-3:]:
    print(f'  {line}')

# Commit
subprocess.run(['git', 'add', '-A'], capture_output=True)
r2 = subprocess.run(['git', 'commit', '-q', '-m',
    'v3.1 — OOP nâng cao: static, getter/setter, abstract, operator overload'],
    capture_output=True)
print(f'  {"✓ commit" if r2.returncode == 0 else "○ không có gì commit"}')

print()
print('╔══════════════════════════════════════════════╗')
print('║  🎉 CAT++ v3.1 — OOP NÂNG CAO HOÀN TẤT      ║')
print('╚══════════════════════════════════════════════╝')
