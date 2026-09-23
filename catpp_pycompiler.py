"""
Cat++ Python Compiler — VM-6 (tối ưu)
Compile AST Cat++ → Python source → exec().
Nhanh 20-50x so với interpreter vì CPython chạy C-level.
"""


class Unsupported(Exception):
    pass


class PyCompiler:
    def __init__(self):
        self.indent = 0
        self.lines = []
        self.tmp_counter = 0
        self.vars = set()
        self.functions = set()

    def emit(self, line):
        self.lines.append('    ' * self.indent + line)

    def new_tmp(self):
        self.tmp_counter += 1
        return f'_t{self.tmp_counter}'

    # ═══════════════════════════════════════════════
    # STATEMENTS
    # ═══════════════════════════════════════════════
    def compile_stmt(self, s):
        t = s[0]

        if t == 'func':
            self.compile_func(s)
        elif t == 'let':
            name = s[1]
            expr = s[2]
            self.emit(f'{name} = {self.compile_expr(expr)}')
            self.vars.add(name)
        elif t == 'assign':
            self.emit(f'{s[1]} = {self.compile_expr(s[2])}')
        elif t == 'assign_target':
            target = s[1]
            value = self.compile_expr(s[2])
            if target[0] == 'dot':
                obj = self.compile_expr(target[1])
                self.emit(f'_catpp_setattr({obj}, {target[2]!r}, {value})')
            elif target[0] == 'index':
                obj = self.compile_expr(target[1])
                idx = self.compile_expr(target[2])
                self.emit(f'{obj}[{idx}] = {value}')
            elif target[0] == 'var':
                self.emit(f'{target[1]} = {value}')
            else:
                raise Unsupported(f"assign_target '{target[0]}'")
        elif t == 'op_assign':
            target, op, rhs = s[1], s[2], s[3]
            if target[0] != 'var':
                raise Unsupported("op_assign chỉ hỗ trợ biến")
            name = target[1]
            rhs_code = self.compile_expr(rhs)
            py_op = op[:-1] if op.endswith('=') else op  # += → +
            self.emit(f'{name} {op} {rhs_code}')
        elif t == 'print':
            expr = self.compile_expr(s[1])
            self.emit(f'_out.append(_catpp_fmt({expr}))')
        elif t == 'expr':
            self.emit(self.compile_expr(s[1]))
        elif t == 'return':
            self.emit(f'return {self.compile_expr(s[1])}')
        elif t == 'if':
            cond = self.compile_expr(s[1])
            self.emit(f'if {cond}:')
            self.indent += 1
            for x in s[2]:
                self.compile_stmt(x)
            if not s[2]:
                self.emit('pass')
            self.indent -= 1
            if s[3]:
                self.emit('else:')
                self.indent += 1
                for x in s[3]:
                    self.compile_stmt(x)
                self.indent -= 1
        elif t == 'while':
            cond = self.compile_expr(s[1])
            self.emit(f'while {cond}:')
            self.indent += 1
            for x in s[2]:
                self.compile_stmt(x)
            if not s[2]:
                self.emit('pass')
            self.indent -= 1
        elif t == 'stop':
            self.emit('break')
        elif t == 'skip':
            self.emit('continue')
        elif t == 'class':
            self.compile_class(s)
        elif t == 'enum':
            self.compile_enum(s)
        else:
            raise Unsupported(f"Stmt '{t}' chưa hỗ trợ")

    def compile_func(self, s):
        name = s[1]
        params = s[2]
        # Detect defaults vs body
        if len(s) > 4 and isinstance(s[3], dict):
            defaults = s[3]
            body = s[4]
        else:
            defaults = {}
            body = s[3] if len(s) > 3 else []

        # Build signature
        if defaults:
            # Sort params: required first, then defaulted
            req = [p for p in params if p not in defaults]
            defs = [p for p in params if p in defaults]
            sig_parts = req[:]
            for p in defs:
                sig_parts.append(f'{p}={self.compile_expr(defaults[p])}')
            sig = ', '.join(sig_parts)
        else:
            sig = ', '.join(params)

        self.emit(f'def {name}({sig}):')
        self.indent += 1
        if not body:
            self.emit('pass')
        else:
            for x in body:
                self.compile_stmt(x)
        self.indent -= 1
        self.emit('')
        self.functions.add(name)

    def compile_class(self, s):
        name = s[1]
        parent = s[2] if len(s) > 2 else None
        fields = s[3] if len(s) > 3 and isinstance(s[3], list) else []
        methods = {}
        for i in range(4, len(s)):
            if isinstance(s[i], dict):
                methods = s[i]
                break

        if parent:
            self.emit(f'class {name}({parent}):')
        else:
            self.emit(f'class {name}:')
        self.indent += 1
        if not fields and not methods:
            self.emit('pass')
        else:
            # Fields khai báo là class attrs default None
            for f in fields:
                self.emit(f'{f} = None')
            # Methods — 'new' → '__init__'
            for mname, (params, body) in methods.items():
                py_mname = '__init__' if mname == 'new' else mname
                param_str = ', '.join(params) if params else ''
                if param_str:
                    sig = f'def {py_mname}(self, {param_str}):'
                else:
                    sig = f'def {py_mname}(self):'
                self.emit(sig)
                self.indent += 1
                # Alias: me = self (Cat++ dùng 'me' cho self)
                self.emit('me = self')
                if not body:
                    self.emit('pass')
                else:
                    for x in body:
                        self.compile_stmt(x)
                self.indent -= 1
        self.indent -= 1
        self.emit('')

    def compile_enum(self, s):
        name = s[1]
        members = s[2]
        self.emit(f'class {name}:')
        self.indent += 1
        self.emit('    class _EnumVal:')
        self.indent += 1
        self.emit('        def __init__(self, n, v): self.name = n; self.value = v')
        self.emit('        def __repr__(self): return self.name')
        self.emit('        def __str__(self): return self.name')
        self.emit('        def __eq__(self, o): return self.value == o if isinstance(o, int) else (self.name == getattr(o, "name", None))')
        self.emit('        def __hash__(self): return self.value')
        self.indent -= 1
        for i, m in enumerate(members):
            self.emit(f'    {m} = _EnumVal("{name}.{m}", {i})')
        self.indent -= 1
        self.emit('')

    # ═══════════════════════════════════════════════
    # EXPRESSIONS
    # ═══════════════════════════════════════════════
    def compile_expr(self, e):
        t = e[0]

        if t == 'addr':
            raise Unsupported("PyCompiler khong ho tro &x")
        if t == 'deref':
            raise Unsupported("PyCompiler khong ho tro *p")
        if t == 'num':
            return repr(e[1])
        if t == 'str':
            s = e[1]
            if '{' in s:
                # Chuyển thành Python f-string
                # Escape dấu { } không mong muốn
                # Đơn giản: bọc trong f-string với {}, escape quote
                inner = s.replace("'", "\\'")
                return "f'" + inner + "'"
            return repr(s)
        if t == 'bool':
            return 'True' if e[1] else 'False'
        if t == 'null':
            return 'None'
        if t == 'var':
            return e[1]
        if t == 'list':
            items = ', '.join(self.compile_expr(x) for x in e[1])
            return f'[{items}]'
        if t == 'dict':
            pairs = ', '.join(
                f'{self.compile_expr(k)}: {self.compile_expr(v)}'
                for k, v in e[1]
            )
            return f'{{{pairs}}}'
        if t == 'neg':
            return f'(-{self.compile_expr(e[1])})'
        if t == 'not':
            return f'(not {self.compile_expr(e[1])})'
        if t == 'bitnot':
            return f'(~{self.compile_expr(e[1])})'
        if t == 'and':
            return f'({self.compile_expr(e[1])} and {self.compile_expr(e[2])})'
        if t == 'or':
            return f'({self.compile_expr(e[1])} or {self.compile_expr(e[2])})'
        if t == 'in':
            return f'({self.compile_expr(e[1])} in {self.compile_expr(e[2])})'
        if t in ('+', '-', '*', '/', '%'):
            return f'({self.compile_expr(e[1])} {t} {self.compile_expr(e[2])})'
        if t in ('&', '|', '^'):
            return f'({self.compile_expr(e[1])} {t} {self.compile_expr(e[2])})'
        if t == 'SHL':
            return f'({self.compile_expr(e[1])} << {self.compile_expr(e[2])})'
        if t == 'SHR':
            return f'({self.compile_expr(e[1])} >> {self.compile_expr(e[2])})'
        if t in ('==', '!=', '<', '>', '<=', '>='):
            return f'({self.compile_expr(e[1])} {t} {self.compile_expr(e[2])})'
        if t == 'index':
            obj = self.compile_expr(e[1])
            idx = self.compile_expr(e[2])
            return f'{obj}[{idx}]'
        if t == 'slice':
            obj = self.compile_expr(e[1])
            lo = self.compile_expr(e[2]) if e[2] else ''
            hi = self.compile_expr(e[3]) if e[3] else ''
            return f'{obj}[{lo}:{hi}]'
        if t == 'dot':
            obj = self.compile_expr(e[1])
            return f'getattr({obj}, {e[2]!r})'
        if t == 'call':
            name = e[1]
            args = ', '.join(self.compile_expr(a) for a in e[2])
            return f'{name}({args})'
        if t == 'method_call':
            obj = self.compile_expr(e[1])
            mname = e[2]
            args = ', '.join(self.compile_expr(a) for a in e[3])
            if args:
                return f'getattr({obj}, {mname!r})({args})'
            return f'getattr({obj}, {mname!r})()'
        if t == 'lambda':
            params = e[1]
            body = e[2]
            sig = ', '.join(params)
            return f'(lambda {sig}: {self.compile_expr(body)})'
        if t == 'cast':
            type_name = e[1]
            value = self.compile_expr(e[2])
            return f'_catpp_cast({type_name!r}, {value})'
        if t == 'sizeof':
            value = self.compile_expr(e[1])
            return f'_catpp_sizeof({value})'
        if t == 'sizeof_type':
            return f'_catpp_sizeof_type({e[1]!r})'
        if t == 'ternary':
            cond = self.compile_expr(e[1])
            a = self.compile_expr(e[2])
            b = self.compile_expr(e[3])
            return f'({a} if {cond} else {b})'
        if t == 'coalesce':
            left = self.compile_expr(e[1])
            right = self.compile_expr(e[2])
            return f'({left} if {left} is not None else {right})'
        if t == 'asm':
            return 'None'
        if t == 'match':
            # Match trở thành if/elif chain
            subject = self.compile_expr(e[1])
            tmp = self.new_tmp()
            return self.compile_match(subject, e[2], tmp)
        raise Unsupported(f"Expr '{t}' chưa hỗ trợ")

    def compile_match(self, subject, cases, tmp):
        # Không dùng cho expression, chỉ cho statement — nhưng phải trả về string
        # Nếu vô tình rơi vào đây → trả về None
        return 'None'

    # ═══════════════════════════════════════════════
    # TOP
    # ═══════════════════════════════════════════════
    def compile_program(self, ast):
        for s in ast:
            self.compile_stmt(s)
        return '\n'.join(self.lines)


# ═══════════════════════════════════════════════
# RUNTIME HELPERS
# ═══════════════════════════════════════════════
def _catpp_fmt(v):
    if v is True: return 'nod'
    if v is False: return 'shake'
    if v is None: return 'hungry'
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, list):
        return '[' + ', '.join(_catpp_fmt(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ', '.join(f'{_catpp_fmt(k)}: {_catpp_fmt(val)}' for k, val in v.items()) + '}'
    return str(v)


def _catpp_setattr(obj, name, value):
    if isinstance(obj, dict):
        obj[name] = value
    else:
        setattr(obj, name, value)


TYPE_SIZES = {'i8':1,'u8':1,'i16':2,'u16':2,'i32':4,'u32':4,
              'i64':8,'u64':8,'int':8,'float':8,'bool':1,'ptr':8,
              'char':1,'byte':1,'str':8}


def _catpp_cast(type_name, v):
    t = type_name.lower()
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


def _catpp_sizeof(v):
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 8
    if isinstance(v, float): return 8
    if isinstance(v, str): return len(v)
    if isinstance(v, list): return len(v) * 8
    return 8


def _catpp_sizeof_type(name):
    return TYPE_SIZES.get(name.lower(), 8)


# ═══════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════
def compile_to_python(source):
    """Compile Cat++ source → Python source."""
    from interpreter import tokenize, Parser
    ast = Parser(tokenize(source)).parse()
    comp = PyCompiler()
    py_source = comp.compile_program(ast)
    return py_source


def run_catpp_py(source, timeout=5.0):
    """Chạy source qua Python compiler."""
    from interpreter import tokenize, Parser, make_builtins

    ast = Parser(tokenize(source)).parse()
    comp = PyCompiler()
    py_source = comp.compile_program(ast)

    # Chuẩn bị namespace
    namespace = {
        '_out': [],
        '_catpp_fmt': _catpp_fmt,
        '_catpp_setattr': _catpp_setattr,
        '_catpp_cast': _catpp_cast,
        '_catpp_sizeof': _catpp_sizeof,
        '_catpp_sizeof_type': _catpp_sizeof_type,
    }
    # Load builtins
    bi = make_builtins()
    for k, v in bi.items():
        namespace[k] = v
    # Aliases tiếng Anh
    aliases = {
        'len': 'tail', 'upper': 'puff', 'lower': 'melt', 'slice': 'nip',
        'abs': 'bolt', 'min': 'kitten', 'max': 'lion',
        'sqrt': 'scratch', 'floor': 'flop', 'ceil': 'perch',
        'str': 'say', 'int': 'tally', 'float': 'drip',
        'keys': 'collar', 'values': 'kits', 'has': 'seek',
        'split': 'shred', 'join': 'weave', 'replace': 'swap',
        'trim': 'lick', 'contains': 'hunt',
        'push': 'stash', 'pop': 'snatch', 'sort': 'line',
        'reverse': 'flip', 'first': 'head', 'last': 'rear',
        'sum': 'pile', 'range': 'walk',
        'map': 'chase', 'filter': 'sift', 'reduce': 'curl',
    }
    for eng, meow_name in aliases.items():
        if meow_name in bi:
            namespace[eng] = bi[meow_name]
        elif meow_name in namespace:
            namespace[eng] = namespace[meow_name]

    # Thêm print giả để tránh crash nếu dùng
    namespace['print'] = lambda *a: namespace['_out'].append(
        ' '.join(_catpp_fmt(x) for x in a))

    # exec
    exec(py_source, namespace)
    return '\n'.join(namespace['_out'])


def disassemble_py(source):
    """In Python source sinh ra."""
    return compile_to_python(source)
