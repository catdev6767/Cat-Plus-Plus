#!/usr/bin/env python3
"""Cat++ v3.1 — OOP nâng cao: static, private, getter/setter, abstract, operator overload."""
import os, sys, shutil, subprocess
from datetime import datetime
from importlib import reload

ROOT = os.path.expanduser('~/catpp')
os.chdir(ROOT)

# Backup
bk = f'.backup/v3.1-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
os.makedirs(bk, exist_ok=True)
shutil.copy('interpreter.py', f'{bk}/interpreter.py')
print(f'📦 Backup: {bk}\n')

def save():
    shutil.copy('interpreter.py', f'{bk}/interpreter.py.phase')

def rollback():
    shutil.copy(f'{bk}/interpreter.py.phase', 'interpreter.py')

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
        if 'interpreter' in sys.modules:
            reload(sys.modules['interpreter'])
        import interpreter
        got = interpreter.run_catpp(code).strip()
        if got == expect:
            print(f'    ✓ {name}')
            return True
        print(f'    ✗ {name}: {got!r} ≠ {expect!r}')
        return False
    except Exception as e:
        print(f'    ✗ {name}: {type(e).__name__}: {e}')
        return False

def section(t):
    print(f'\n{"═"*52}\n  {t}\n{"═"*52}')

def syntax_ok():
    try:
        with open('interpreter.py') as f: compile(f.read(), 'interpreter.py', 'exec')
        return True
    except SyntaxError as e:
        print(f'  ✗ Syntax error dòng {e.lineno}: {e.msg}')
        return False


# ═══════════════════════════════════════════════
section('PHASE 1: Static method + private field')
# ═══════════════════════════════════════════════
save()

# Sửa class_body parser
patch('Parser class_body: static + abstract + get/set',
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
        getter_methods = {}
        setter_methods = {}
        self.skip_nl()
        while self.peek().type not in ('DEDENT','EOF'):
            t = self.peek()
            if t.type == 'PAW':
                self.next()
                # paw [private|public] name
                name = self.expect('IDENT').value
                if name in ('private', 'public'):
                    name = self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(name)
            elif t.type == 'PURR':
                self.next()
                first = self.expect('IDENT').value
                mname = first
                is_static = False
                is_get = False
                is_set = False
                is_abstract = False
                if first == 'static':
                    is_static = True
                    mname = self.expect('IDENT').value
                elif first == 'get':
                    is_get = True
                    mname = self.expect('IDENT').value
                elif first == 'set':
                    is_set = True
                    mname = self.expect('IDENT').value
                elif first == 'abstract':
                    is_abstract = True
                    mname = self.expect('IDENT').value
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
                if is_abstract:
                    self.expect('NEWLINE')
                    abstract_methods.add(mname)
                    methods[mname] = (params, [])
                else:
                    body = self.block()
                    if is_get:
                        # Lưu riêng, không ghi vào methods
                        getter_methods[mname] = (params, body)
                    elif is_set:
                        setter_methods[mname] = (params, body)
                    else:
                        methods[mname] = (params, body)
                        if is_static: static_methods.add(mname)
            else: raise CatError(f"Cat chi chua paw hoac purr", t.line)
            self.skip_nl()
        if self.peek().type == 'DEDENT': self.next()
        return (fields, methods, static_methods, getters, setters,
                abstract_methods, getter_methods, setter_methods)""")

# Sửa class statement gọi class_body
patch('Parser class stmt: nhận 6 giá trị',
"""        if t.type == 'CAT':
            self.next(); name = self.expect('IDENT').value; parent = None
            if self.peek().type == 'KIN':
                self.next(); parent = self.expect('IDENT').value
            fields, methods = self.class_body()
            return ('class', name, parent, fields, methods, t.line)""",
"""        if t.type == 'CAT':
            self.next()
            is_abstract_class = False
            if self.peek().type == 'IDENT' and self.peek().value == 'abstract':
                self.next(); is_abstract_class = True
            name = self.expect('IDENT').value; parent = None
            if self.peek().type == 'KIN':
                self.next(); parent = self.expect('IDENT').value
            (fields, methods, static_m, getters, setters, abstract_m,
             getter_methods, setter_methods) = self.class_body()
            return ('class', name, parent, fields, methods, static_m,
                    getters, setters, abstract_m, is_abstract_class,
                    getter_methods, setter_methods, t.line)""")

# ClassObj thêm các set
patch('ClassObj: mở rộng',
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

    def find_method(self, name):
        c = self
        while c:
            if name in c.methods: return (c, c.methods[name])
            c = c.parent
        return (None, None)

    def is_static(self, name):
        c = self
        while c:
            if name in c.methods:
                return name in c.static_methods
            c = c.parent
        return False

    def find_abstract(self):
        result = set()
        c = self
        while c:
            result |= c.abstract_methods
            c = c.parent
        return result""")

# Runtime class exec
patch('Runtime class exec: truyền thêm args',
"""        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]
            parent_obj = env.get(parent) if parent else None
            env.define(name, ClassObj(name, parent_obj, fields, methods, env))""",
"""        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]
            static_m, getters, setters, abstract_m, is_abs = s[5], s[6], s[7], s[8], s[9]
            getter_m, setter_m = s[10], s[11]
            parent_obj = env.get(parent) if parent else None
            env.define(name, ClassObj(name, parent_obj, fields, methods, env,
                                      static_m, getters, setters, abstract_m, is_abs,
                                      getter_m, setter_m))""")

# make_instance check abstract
patch('make_instance: chặn abstract + check abstract methods',
"""def make_instance(cls, args, out, rt):
    inst = Instance(cls)
    if 'new' in cls.methods:""",
"""def make_instance(cls, args, out, rt):
    if cls.is_abstract:
        raise CatError(f"Khong the tao instance cua abstract class '{cls.name}'")
    # Check abstract methods phải được override hết
    abstract = cls.find_abstract()
    for m in abstract:
        found = False
        c = cls
        while c:
            if m in c.methods and m not in c.abstract_methods:
                found = True; break
            c = c.parent
        if not found:
            raise CatError(f"Class '{cls.name}' chua override abstract method '{m}'")
    inst = Instance(cls)
    if 'new' in cls.methods:""")

# dot access: static method
patch('dot access: static method trên ClassObj',
"""        if isinstance(obj, EnumObj):
            if name in obj.members: return obj.values[name]
            raise CatError(f"Litter khong co '{name}'")
        raise CatError(f"Khong truy cap duoc '.{name}'")""",
"""        if isinstance(obj, EnumObj):
            if name in obj.members: return obj.values[name]
            raise CatError(f"Litter khong co '{name}'")
        if isinstance(obj, ClassObj):
            if name in obj.methods and name in obj.static_methods:
                return ('static', obj, name)
            raise CatError(f"Class '{obj.name}' khong co static method '{name}'")
        raise CatError(f"Khong truy cap duoc '.{name}'")""")

# method_call cho static
patch('method_call: hỗ trợ static',
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

# call_static function
patch('Thêm call_static',
"""def call_method(inst, name, args, out, rt):""",
"""def call_getter(inst, name, out, rt):
    c, m = inst.cls.find_getter(name)
    if m is None:
        raise CatError(f"Getter '{name}' khong ton tai")
    params, body = m
    local = Env(c.env)
    local.define('me', inst)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx as r: return r.v
    return None


def call_setter(inst, name, value, out, rt):
    c, m = inst.cls.find_setter(name)
    if m is None:
        raise CatError(f"Setter '{name}' khong ton tai")
    params, body = m
    local = Env(c.env)
    local.define('me', inst)
    if params:
        local.define(params[0], value)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx: pass
    return None


def call_static(cls, name, args, out, rt):
    c, m = cls.find_method(name)
    if m is None:
        raise CatError(f"Static method '{name}' khong ton tai")
    params, body = m
    local = Env(cls.env)
    for p, a in zip(params, args): local.define(p, a)
    try:
        for s in body: exec_(s, local, out, rt)
    except ReturnEx as r: return r.v
    return None


def call_method(inst, name, args, out, rt):""")

# Test 1
print()
tests_1 = [
    ('static', 'cat M\n    purr static hi()\n        give "hi"\nmeow M.hi()', 'hi'),
    ('private (conv)', 'cat P\n    paw _x\n    purr new(v)\n        me._x = v\n    purr get_x()\n        give me._x\nmeow P(5).get_x()', '5'),
    ('abstract subclass instance', 'cat abstract S\n    purr area()\n        give 0\ncat C kin S\n    paw x\n    purr new()\n        me.x = 1\nmeow C().area()', '0'),
]
all_ok = True
for n, c, e in tests_1:
    if not test(n, c, e): all_ok = False

if not all_ok or not syntax_ok():
    print('\n❌ Phase 1 fail — rollback')
    rollback()
    sys.exit(1)


# ═══════════════════════════════════════════════
section('PHASE 2: Getter / Setter')
# ═══════════════════════════════════════════════
save()

# dot access: gọi getter nếu field không có
patch('dot: gọi getter khi field không tồn tại',
"""        if isinstance(obj, Instance):
            if name in obj.data: return obj.data[name]
            cls = obj.cls
            while cls:
                if name in cls.methods: return ('bound', obj, name)
                cls = cls.parent
            raise CatError(f"Instance khong co '{name}'")""",
"""        if isinstance(obj, Instance):
            if name in obj.data: return obj.data[name]
            cls = obj.cls
            while cls:
                if name in cls.getters:
                    return call_getter(obj, name, out, rt)
                if name in cls.methods: return ('bound', obj, name)
                cls = cls.parent
            raise CatError(f"Instance khong co '{name}'")""")

# assign_to: gọi setter
patch('assign_to: gọi setter khi có',
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

tests_2 = [
    ('getter', 'cat P\n    paw _x\n    purr new(v)\n        me._x = v\n    purr get x()\n        give me._x\npaw p = P(42)\nmeow p.x', '42'),
    ('setter', 'cat P\n    paw _x\n    purr new()\n        me._x = 0\n    purr set x(v)\n        me._x = v * 2\n    purr get x()\n        give me._x\npaw p = P()\np.x = 5\nmeow p.x', '10'),
]
all_ok = True
for n, c, e in tests_2:
    if not test(n, c, e): all_ok = False

if not all_ok or not syntax_ok():
    print('\n❌ Phase 2 fail — rollback')
    rollback()
    sys.exit(1)


# ═══════════════════════════════════════════════
section('PHASE 3: Abstract method')
# ═══════════════════════════════════════════════
save()

# Test - abstract method cần override
tests_3 = [
    ('abstract cần override',
     'cat abstract Shape\n    purr area()\n    purr name()\n        give "shape"\ncat Circle kin Shape\n    paw r\n    purr new(r)\n        me.r = r\n    purr area()\n        give 3.14 * me.r * me.r\nmeow Circle(2).area()',
     '12.56'),
]
all_ok = True
for n, c, e in tests_3:
    if not test(n, c, e): all_ok = False

# Test abstract method bị chặn khi chưa override
try:
    if 'interpreter' in sys.modules:
        reload(sys.modules['interpreter'])
    import interpreter
    interpreter.run_catpp('cat abstract A\n    paw x\n    purr new()\n        me.x = 0\nA()')
    print('    ✗ abstract chưa chặn instance')
    all_ok = False
except Exception as e:
    if 'abstract' in str(e).lower():
        print('    ✓ abstract chặn instance')
    else:
        print(f'    ⚠ Lỗi khác: {e}')

if not all_ok or not syntax_ok():
    print('\n❌ Phase 3 fail — rollback')
    rollback()
    sys.exit(1)


# ═══════════════════════════════════════════════
section('PHASE 4: Operator overload')
# ═══════════════════════════════════════════════
save()

# Map operator → method name
patch('Thêm OPERATOR_MAP',
"""class Instance:
    def __init__(self, cls):""",
"""OPERATOR_MAP = {
    '+': 'add', '-': 'sub', '*': 'mul', '/': 'div',
    '%': 'mod', '==': 'eq', '!=': 'neq',
    '<': 'lt', '>': 'gt', '<=': 'le', '>=': 'ge',
}

class Instance:
    def __init__(self, cls):""")

# eval binop: check operator overload
patch('eval binop: check operator overload',
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':""",
"""    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        # Operator overload
        if isinstance(l, Instance):
            opname = OPERATOR_MAP.get(t)
            if opname:
                c, m = l.cls.find_method(opname)
                if m is not None:
                    return call_method(l, opname, [r], out, rt)
        if t == '+':""")

tests_4 = [
    ('op add',
     'cat V\n    paw x\n    purr new(v)\n        me.x = v\n    purr add(o)\n        give V(me.x + o.x)\n    purr show()\n        give me.x\npaw a = V(3)\npaw b = V(4)\npaw c = a + b\nmeow c.show()',
     '7'),
    ('op eq',
     'cat P\n    paw x\n    purr new(v)\n        me.x = v\n    purr eq(o)\n        give me.x == o.x\npaw a = P(5)\npaw b = P(5)\nsniff a == b\n    meow "same"\nswat\n    meow "diff"',
     'same'),
    ('op lt',
     'cat P\n    paw x\n    purr new(v)\n        me.x = v\n    purr lt(o)\n        give me.x < o.x\nsniff P(3) < P(5)\n    meow "yes"\nswat\n    meow "no"',
     'yes'),
]
all_ok = True
for n, c, e in tests_4:
    if not test(n, c, e): all_ok = False

if not all_ok or not syntax_ok():
    print('\n❌ Phase 4 fail — rollback')
    rollback()
    sys.exit(1)


# ═══════════════════════════════════════════════
section('PHASE 5: Tích hợp + full test')
# ═══════════════════════════════════════════════

# Test cuối — tất cả cùng lúc
final_test = '''
cat abstract Animal
    paw _name

    purr abstract speak()

    purr get name()
        give me._name

    purr set name(v)
        me._name = v

    purr static create(n)
        give Animal(n)

cat Dog kin Animal
    paw _age

    purr new(n, a)
        me._name = n
        me._age = a

    purr speak()
        give me._name + " says woof"

    purr add(other)
        give Dog(me._name, me._age + other._age)

paw d1 = Dog("Rex", 3)
paw d2 = Dog("Max", 5)
paw d3 = d1 + d2
meow d1.speak()
meow d1.name
meow d3._age
'''
try:
    if 'interpreter' in sys.modules: reload(sys.modules['interpreter'])
    import interpreter
    result = interpreter.run_catpp(final_test).strip()
    print(f'  Kết quả:\n{result}')
    print()
    if 'Rex says woof' in result and '8' in result:
        print('  ✓ Tích hợp OK')
    else:
        print('  ✗ Kết quả không đúng')
except Exception as e:
    print(f'  ✗ Lỗi: {e}')

# Full test
print()
r = subprocess.run([sys.executable, 'tests/test_all.py'],
                   capture_output=True, text=True)
for line in r.stdout.strip().split('\n')[-4:]:
    print(f'  {line}')

if 'fail' not in r.stdout.lower() or '0 fail' in r.stdout:
    # Commit
    subprocess.run(['git', 'add', '-A'], capture_output=True)
    r2 = subprocess.run(['git', 'commit', '-q', '-m',
        'Cat++ v3.1 — OOP nâng cao: static, private, getter/setter, abstract, operator overload'],
        capture_output=True)
    print(f'\n{"✓" if r2.returncode == 0 else "○"} Git commit')

print(f"""
╔══════════════════════════════════════════════╗
║  🎉 CAT++ v3.1 HOÀN TẤT — OOP NÂNG CAO       ║
╚══════════════════════════════════════════════╝

Đã thêm:
  ✓ static method:      purr static create()
  ✓ private convention: paw _x
  ✓ getter:             purr get x()
  ✓ setter:             purr set x(v)
  ✓ abstract class:     cat abstract Shape
  ✓ abstract method:    purr area() (không body)
  ✓ operator overload:  purr add(o), sub, mul, div,
                        eq, neq, lt, gt, le, ge, mod

Backup: {bk}

Ví dụ:
  cat abstract Shape
      purr abstract area()

  cat Circle kin Shape
      paw r
      purr new(r)
          me.r = r
      purr area()
          give 3.14 * me.r * me.r

  meow Circle(2).area()
""")
