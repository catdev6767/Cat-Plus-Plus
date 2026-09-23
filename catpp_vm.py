"""
Cat++ Bytecode VM — Phase 1
Stack-based virtual machine + compiler.

Không đụng interpreter.py. Chạy song song, fallback khi cần.
"""

# ═══════════════════════════════════════════════
# OPCODES
# ═══════════════════════════════════════════════
OP_CONST          = 'CONST'
OP_LOAD           = 'LOAD'
OP_STORE          = 'STORE'
OP_DEFINE         = 'DEFINE'
OP_NEW            = 'NEW'
OP_GET_FIELD      = 'GET_FIELD'
OP_SET_FIELD      = 'SET_FIELD'
OP_CALL_METHOD    = 'CALL_METHOD'
OP_MATCH          = 'MATCH'
OP_LAMBDA         = 'LAMBDA'
OP_BUILD_LIST     = 'BUILD_LIST'
OP_INDEX          = 'INDEX'
OP_ADD            = 'ADD'
OP_SUB            = 'SUB'
OP_MUL            = 'MUL'
OP_DIV            = 'DIV'
OP_MOD            = 'MOD'
OP_NEG            = 'NEG'
OP_NOT            = 'NOT'
OP_AND            = 'AND'
OP_OR             = 'OR'
OP_EQ             = 'EQ'
OP_NEQ            = 'NEQ'
OP_LT             = 'LT'
OP_GT             = 'GT'
OP_LTE            = 'LTE'
OP_GTE            = 'GTE'
OP_PRINT          = 'PRINT'
OP_POP            = 'POP'
OP_JUMP           = 'JUMP'
OP_JUMP_IF_FALSE  = 'JUMP_IF_FALSE'
OP_CALL           = 'CALL'
OP_RETURN         = 'RETURN'
OP_HALT           = 'HALT'
OP_ADDR           = 'ADDR'
OP_DEREF          = 'DEREF'
OP_DEREF_SET      = 'DEREF_SET'
OP_BUILD_DICT     = 'BUILD_DICT'
OP_IN             = 'IN'
OP_SLICE          = 'SLICE'
OP_ITER_BEGIN     = 'ITER_BEGIN'
OP_ITER_CHECK     = 'ITER_CHECK'
OP_ITER_END       = 'ITER_END'


class Unsupported(Exception):
    """Raised khi VM không hỗ trợ cú pháp — caller fallback interpreter."""
    pass


# ═══════════════════════════════════════════════
# BYTECODE INSTRUCTION
# ═══════════════════════════════════════════════
class Ins:
    __slots__ = ('op', 'arg', 'line')
    def __init__(self, op, arg=None, line=0):
        self.op = op
        self.arg = arg
        self.line = line
    def __repr__(self):
        return f'{self.op} {self.arg!r}' if self.arg is not None else self.op


# ═══════════════════════════════════════════════
# COMPILER — AST → Bytecode
# ═══════════════════════════════════════════════
class Compiler:
    def __init__(self):
        self.code = []
        self.loop_stack = []
        self.functions = {}
        self.classes = {}
        self.func_stack = []


    def emit(self, op, arg=None, line=0):
        idx = len(self.code)
        self.code.append(Ins(op, arg, line))
        return idx

    def patch(self, idx, target):
        self.code[idx].arg = target

    def compile(self, ast):
        top_stmts = []
        for s in ast:
            if s[0] == 'func':
                self.compile_function(s)
            else:
                top_stmts.append(s)
        for s in top_stmts:
            self.compile_stmt(s)
        self.emit(OP_HALT)
        return self.code

    def compile_function(self, stmt):
        name = stmt[1]
        params = stmt[2]
        # Detect defaults vs body
        if len(stmt) > 4 and isinstance(stmt[3], dict):
            defaults = stmt[3]
            body = stmt[4]
        elif len(stmt) > 3 and isinstance(stmt[3], list):
            defaults = {}
            body = stmt[3]
        else:
            defaults = {}
            body = stmt[3] if len(stmt) > 3 else []

        saved_code = self.code
        saved_loop = self.loop_stack
        self.code = []
        self.loop_stack = []

        for s in body:
            self.compile_stmt(s)

        # Auto return None
        self.emit(OP_CONST, None)
        self.emit(OP_RETURN)

        func_code = self.code
        self.code = saved_code
        self.loop_stack = saved_loop

        self.functions[name] = {
            'params': params,
            'defaults': defaults,
            'code': func_code,
        }

    def compile_stmt(self, stmt):
        t = stmt[0]
        line = stmt[-1] if isinstance(stmt[-1], int) else 0

        if t == 'func':
            self.compile_function(stmt)
            return

        if t == 'class':
            name = stmt[1]
            parent = stmt[2] if len(stmt) > 2 else None
            # Detect: fields ở vị trí nào
            # Pattern cũ: ('class', name, parent, fields, methods, line)
            # Pattern mới: ('class', name, parent, fields, methods, static, ...)
            fields = stmt[3] if len(stmt) > 3 and isinstance(stmt[3], list) else []
            methods = {}
            for i in range(4, len(stmt)):
                if isinstance(stmt[i], dict):
                    methods = stmt[i]
                    break
            # Fallback: methods ở vị trí 4
            if not methods and len(stmt) > 4 and isinstance(stmt[4], dict):
                methods = stmt[4]
            # Compile từng method thành bytecode
            method_code = {}
            for mname, (params, body) in methods.items():
                saved_code = self.code
                saved_loop = self.loop_stack
                self.code = []
                self.loop_stack = []
                for s in body:
                    self.compile_stmt(s)
                self.emit(OP_CONST, None)
                self.emit(OP_RETURN)
                method_code[mname] = {
                    'params': params,
                    'code': self.code,
                }
                self.code = saved_code
                self.loop_stack = saved_loop
            self.classes[name] = {
                'parent': parent,
                'fields': fields,
                'methods': method_code,
            }
            return

        if t == 'return':
            self.compile_expr(stmt[1])
            self.emit(OP_RETURN, None, line)

        elif t == 'let':
            self.compile_expr(stmt[2])
            self.emit(OP_DEFINE, stmt[1], line)

        elif t == 'assign':
            self.compile_expr(stmt[2])
            self.emit(OP_STORE, stmt[1], line)

        elif t == 'assign_target':
            # me.x = value hoặc obj.field = value
            target = stmt[1]
            value = stmt[2]
            if target[0] == 'deref':
                self.compile_expr(target[1])
                self.compile_expr(value)
                self.emit(OP_DEREF_SET, None, line)
            elif target[0] == 'dot':
                self.compile_expr(target[1])
                self.compile_expr(value)
                self.emit(OP_SET_FIELD, target[2], line)
            elif target[0] == 'index':
                raise Unsupported("index assign chua ho tro")
            elif target[0] == 'var':
                self.compile_expr(value)
                self.emit(OP_STORE, target[1], line)
            else:
                raise Unsupported(f"assign_target '{target[0]}' chua ho tro")

        elif t == 'op_assign':
            target, op, rhs = stmt[1], stmt[2], stmt[3]
            op_map = {'+=': OP_ADD, '-=': OP_SUB, '*=': OP_MUL,
                      '/=': OP_DIV, '%=': OP_MOD}
            if op not in op_map:
                raise Unsupported(f"Toan tu '{op}' chua ho tro")
            if target[0] == 'deref':
                # *p += x  ->  *p = *p + x
                self.compile_expr(target[1])  # ptr
                self.compile_expr(target[1])  # ptr (lan 2)
                self.emit(OP_DEREF)           # ptr, *p
                self.compile_expr(rhs)
                self.emit(op_map[op], None, line)
                self.emit(OP_DEREF_SET)
            elif target[0] == 'var':
                name = target[1]
                self.emit(OP_LOAD, name, line)
                self.compile_expr(rhs)
                self.emit(op_map[op], None, line)
                self.emit(OP_STORE, name, line)
            else:
                raise Unsupported("op_assign chi ho tro bien hoac *ptr")

        elif t == 'print':
            self.compile_expr(stmt[1])
            self.emit(OP_PRINT, None, line)

        elif t == 'expr':
            self.compile_expr(stmt[1])
            self.emit(OP_POP, None, line)

        elif t == 'if':
            self.compile_if(stmt, line)

        elif t == 'while':
            self.compile_while(stmt, line)

        elif t == 'each':
            name = stmt[1]; expr = stmt[2]; body = stmt[3]
            self.compile_expr(expr)
            self.emit(OP_ITER_BEGIN, name, line)
            loop_start = len(self.code)
            jump_end = self.emit(OP_ITER_CHECK, None, line)
            for s in body:
                self.compile_stmt(s)
            self.emit(OP_JUMP, loop_start, line)
            self.patch(jump_end, len(self.code))
            self.emit(OP_ITER_END, None, line)

        elif t == 'stop':
            if not self.loop_stack:
                raise Unsupported("stop ngoai vong lap")
            brk = self.emit(OP_JUMP, None, line)
            self.loop_stack[-1][1].append(brk)

        elif t == 'skip':
            if not self.loop_stack:
                raise Unsupported("skip ngoai vong lap")
            self.emit(OP_JUMP, self.loop_stack[-1][0], line)

        else:
            raise Unsupported(f"Stmt '{t}' chua ho tro trong VM")

    def compile_if(self, stmt, line):
        cond, then, els = stmt[1], stmt[2], stmt[3]
        self.compile_expr(cond)
        jump_false = self.emit(OP_JUMP_IF_FALSE, None, line)
        for s in then:
            self.compile_stmt(s)
        if els:
            jump_end = self.emit(OP_JUMP, None, line)
            self.patch(jump_false, len(self.code))
            for s in els:
                self.compile_stmt(s)
            self.patch(jump_end, len(self.code))
        else:
            self.patch(jump_false, len(self.code))

    def compile_while(self, stmt, line):
        cond, body = stmt[1], stmt[2]
        start = len(self.code)
        self.loop_stack.append([start, []])
        self.compile_expr(cond)
        jump_false = self.emit(OP_JUMP_IF_FALSE, None, line)
        for s in body:
            self.compile_stmt(s)
        self.emit(OP_JUMP, start, line)
        self.patch(jump_false, len(self.code))
        _, breaks = self.loop_stack.pop()
        end = len(self.code)
        for brk in breaks:
            self.patch(brk, end)

    def compile_expr(self, expr):
        t = expr[0]

        if t == 'addr':
            inner = expr[1]
            if inner[0] != 'var':
                raise Unsupported("& chi ho tro bien")
            self.emit(OP_ADDR, inner[1])
        elif t == 'deref':
            self.compile_expr(expr[1])
            self.emit(OP_DEREF)
        elif t == 'num':
            self.emit(OP_CONST, expr[1])
        elif t == 'str':
            s = expr[1]
            if '{' not in s:
                self.emit(OP_CONST, s)
            else:
                import re as _re
                parts = _re.split(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', s)
                first = True
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        if not part:
                            continue
                        self.emit(OP_CONST, part)
                    else:
                        self.emit(OP_LOAD, part)
                    if not first:
                        self.emit(OP_ADD)
                    first = False
                if first:
                    self.emit(OP_CONST, '')
        elif t == 'bool':
            self.emit(OP_CONST, expr[1])
        elif t == 'null':
            self.emit(OP_CONST, None)
        elif t == 'var':
            self.emit(OP_LOAD, expr[1])
        elif t == 'neg':
            self.compile_expr(expr[1])
            self.emit(OP_NEG)
        elif t == 'not':
            self.compile_expr(expr[1])
            self.emit(OP_NOT)
        elif t == 'and':
            self.compile_expr(expr[1])
            self.compile_expr(expr[2])
            self.emit(OP_AND)
        elif t == 'or':
            self.compile_expr(expr[1])
            self.compile_expr(expr[2])
            self.emit(OP_OR)
        elif t in ('+', '-', '*', '/', '%'):
            self.compile_expr(expr[1])
            self.compile_expr(expr[2])
            op_map = {'+': OP_ADD, '-': OP_SUB, '*': OP_MUL,
                      '/': OP_DIV, '%': OP_MOD}
            self.emit(op_map[t])
        elif t in ('==', '!=', '<', '>', '<=', '>='):
            self.compile_expr(expr[1])
            self.compile_expr(expr[2])
            op_map = {'==': OP_EQ, '!=': OP_NEQ, '<': OP_LT, '>': OP_GT,
                      '<=': OP_LTE, '>=': OP_GTE}
            self.emit(op_map[t])
        elif t == 'call':
            name = expr[1]
            args = expr[2]
            for a in args:
                self.compile_expr(a)
            # Nếu là class → OP_NEW
            if name in self.classes:
                self.emit(OP_NEW, (name, len(args)))
            else:
                self.emit(OP_CALL, (name, len(args)))
        elif t == 'index':
            obj = expr[1]
            idx = expr[2]
            self.compile_expr(obj)
            self.compile_expr(idx)
            self.emit(OP_INDEX)
        elif t == 'list':
            items = expr[1]
            for item in items:
                self.compile_expr(item)
            self.emit(OP_BUILD_LIST, len(items))
        elif t == 'dict':
            pairs = expr[1]
            for k, v in pairs:
                self.compile_expr(k)
                self.compile_expr(v)
            self.emit(OP_BUILD_DICT, len(pairs))
        elif t == 'in':
            self.compile_expr(expr[1])
            self.compile_expr(expr[2])
            self.emit(OP_IN)
        elif t == 'slice':
            obj = expr[1]; lo = expr[2]; hi = expr[3]
            self.compile_expr(obj)
            if lo: self.compile_expr(lo)
            else: self.emit(OP_CONST, None)
            if hi: self.compile_expr(hi)
            else: self.emit(OP_CONST, None)
            self.emit(OP_SLICE)
        elif t == 'lambda':
            params = expr[1]
            body = expr[2]
            # Compile body thành sub-function
            saved_code = self.code
            saved_loop = self.loop_stack
            self.code = []
            self.loop_stack = []
            self.compile_expr(body)
            self.emit(OP_RETURN)
            lambda_code = self.code
            self.code = saved_code
            self.loop_stack = saved_loop
            self.emit(OP_LAMBDA, (params, lambda_code))
        elif t == 'dot':
            obj = expr[1]
            field = expr[2]
            self.compile_expr(obj)
            self.emit(OP_GET_FIELD, field)
        elif t == 'method_call':
            obj = expr[1]
            mname = expr[2]
            args = expr[3]
            self.compile_expr(obj)
            for a in args:
                self.compile_expr(a)
            self.emit(OP_CALL_METHOD, (mname, len(args)))
        else:
            raise Unsupported(f"Expr '{t}' chua ho tro trong VM")


# ═══════════════════════════════════════════════
# VM — Execute bytecode
# ═══════════════════════════════════════════════
class ClassObj:
    def __init__(self, name, parent, fields, methods, env=None):
        self.name = name
        self.parent = parent
        self.fields = fields
        self.methods = methods
        self.env = env

    def find_method(self, name):
        cls = self
        while cls:
            if name in cls.methods:
                return (cls, cls.methods[name])
            cls = cls.parent
        return (None, None)


class Instance:
    def __init__(self, cls):
        self.cls = cls
        self.data = {}
        # Gom fields từ class cha (dùng MRO đơn giản)
        all_fields = []
        c = cls
        while c:
            for f in c.fields:
                if f not in all_fields:
                    all_fields.append(f)
            c = c.parent
        for f in all_fields:
            self.data[f] = None


class Ptr:
    def __init__(self, env, name):
        self.env = env
        self.name = name
    def get(self):
        return self.env.get(self.name)
    def set(self, value):
        e = self.env
        while e:
            if self.name in e.vars:
                e.vars[self.name] = value
                return
            e = e.parent
        raise NameError(f"Bien chua khai bao: '{self.name}'")


def _eval_const_ast(node, env):
    """Eval don gian cho default value — chi ho tro literal + var."""
    t = node[0]
    if t == 'num': return node[1]
    if t == 'str': return node[1]
    if t == 'bool': return node[1]
    if t == 'null': return None
    if t == 'neg': return -_eval_const_ast(node[1], env)
    if t == 'list': return [_eval_const_ast(x, env) for x in node[1]]
    if t == 'dict':
        d = {}
        for k, v in node[1]:
            d[_eval_const_ast(k, env)] = _eval_const_ast(v, env)
        return d
    if t == 'var': return env.get(node[1])
    raise TypeError(f"Default phuc tap chua ho tro: {t}")


def _builtin_method(obj, name, args):
    """Method cho str/list/dict — giong interpreter."""
    if isinstance(obj, str):
        if name == 'upper': return obj.upper()
        if name == 'lower': return obj.lower()
        if name == 'trim': return obj.strip()
        if name == 'length' or name == 'len': return len(obj)
        if name == 'contains': return args[0] in obj
        if name == 'split': return obj.split(args[0] if args else ' ')
        if name == 'replace': return obj.replace(args[0], args[1])
    if isinstance(obj, list):
        if name == 'push': obj.append(args[0]); return obj
        if name == 'pop': return obj.pop() if obj else None
        if name == 'length' or name == 'len': return len(obj)
        if name == 'first': return obj[0] if obj else None
        if name == 'last': return obj[-1] if obj else None
        if name == 'contains': return args[0] in obj
        if name == 'sum': return sum(obj)
    if isinstance(obj, dict):
        if name == 'get': return obj.get(args[0])
        if name == 'keys': return list(obj.keys())
        if name == 'values': return list(obj.values())
        if name == 'has': return args[0] in obj
        if name == 'size' or name == 'len': return len(obj)
    raise AttributeError(f"'{name}' khong ho tro cho {type(obj).__name__}")


class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        e = self
        while e:
            if name in e.vars:
                return e.vars[name]
            e = e.parent
        raise NameError(f"Bien chua khai bao: '{name}'")

    def set(self, name, value):
        e = self
        while e:
            if name in e.vars:
                e.vars[name] = value
                return
            e = e.parent
        # Không tìm thấy → tạo ở scope hiện tại
        self.vars[name] = value

    def define(self, name, value):
        self.vars[name] = value


class VM:
    def __init__(self, code, functions=None, classes=None):
        self.code = code
        self.functions = functions or {}
        self.classes_data = classes or {}
        self.stack = []
        self.env = Env()
        self.output = []
        self.call_stack = []
        self.iter_stack = []
        # Load builtins từ interpreter
        try:
            from interpreter import make_builtins
            bi = make_builtins()
            for k, v in bi.items():
                self.env.define(k, v)
            # Aliases tiếng Anh → tên mèo
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
                'sin': 'sway', 'cos': 'wave', 'tan': 'slant',
                'log': 'grow', 'pow': 'bound',
                'random': 'wander', 'random_int': 'dice',
                'match': 'match', 'find_all': 'find_all',
                'replace_all': 'replace_all',
            }
            for eng, meow_name in aliases.items():
                if meow_name in bi:
                    self.env.define(eng, bi[meow_name])
        except Exception as e:
            print(f"[VM] Không load được builtins: {e}")


    def push(self, v):
        self.stack.append(v)

    def pop(self):
        return self.stack.pop()

    def fmt(self, v):
        if v is True: return 'nod'
        if v is False: return 'shake'
        if v is None: return 'hungry'
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        if isinstance(v, list):
            return '[' + ', '.join(self.fmt(x) for x in v) + ']'
        if isinstance(v, dict):
            return '{' + ', '.join(f'{self.fmt(k)}: {self.fmt(val)}' for k, val in v.items()) + '}'
        return str(v)

    def run(self):
        code = self.code
        stack = self.stack
        env = self.env
        out = self.output
        pc = 0
        n = len(code)

        while pc < n:
            ins = code[pc]
            op = ins.op
            pc += 1

            if op == OP_CONST:
                stack.append(ins.arg)

            elif op == OP_LOAD:
                stack.append(env.get(ins.arg))

            elif op == OP_STORE:
                env.set(ins.arg, stack.pop())

            elif op == OP_DEFINE:
                env.define(ins.arg, stack.pop())

            elif op == OP_ADD:
                b = stack.pop(); a = stack.pop()
                if isinstance(a, str) or isinstance(b, str):
                    stack.append(str(a) + str(b))
                elif isinstance(a, list) and isinstance(b, list):
                    stack.append(a + b)
                else:
                    stack.append(a + b)

            elif op == OP_SUB:
                b = stack.pop(); a = stack.pop()
                stack.append(a - b)

            elif op == OP_MUL:
                b = stack.pop(); a = stack.pop()
                stack.append(a * b)

            elif op == OP_DIV:
                b = stack.pop(); a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Chia cho 0")
                stack.append(a / b)

            elif op == OP_MOD:
                b = stack.pop(); a = stack.pop()
                stack.append(a % b)

            elif op == OP_NEG:
                stack.append(-stack.pop())

            elif op == OP_NOT:
                stack.append(not stack.pop())

            elif op == OP_AND:
                b = stack.pop(); a = stack.pop()
                stack.append(a and b)

            elif op == OP_OR:
                b = stack.pop(); a = stack.pop()
                stack.append(a or b)

            elif op == OP_EQ:
                b = stack.pop(); a = stack.pop()
                stack.append(a == b)

            elif op == OP_NEQ:
                b = stack.pop(); a = stack.pop()
                stack.append(a != b)

            elif op == OP_LT:
                b = stack.pop(); a = stack.pop()
                stack.append(a < b)

            elif op == OP_GT:
                b = stack.pop(); a = stack.pop()
                stack.append(a > b)

            elif op == OP_LTE:
                b = stack.pop(); a = stack.pop()
                stack.append(a <= b)

            elif op == OP_GTE:
                b = stack.pop(); a = stack.pop()
                stack.append(a >= b)

            elif op == OP_PRINT:
                out.append(self.fmt(stack.pop()))

            elif op == OP_POP:
                stack.pop()

            elif op == OP_JUMP:
                pc = ins.arg

            elif op == OP_JUMP_IF_FALSE:
                v = stack.pop()
                if not v:
                    pc = ins.arg

            elif op == OP_CALL:
                fname, argc = ins.arg
                # Builtin? — gọi trực tiếp
                if fname not in self.functions:
                    try:
                        bfn = env.get(fname)
                        if callable(bfn):
                            args = []
                            for _ in range(argc):
                                args.insert(0, stack.pop())
                            stack.append(bfn(*args))
                            continue
                    except NameError:
                        pass
                    raise NameError(f"Ham chua dinh nghia: '{fname}'")
                fn = self.functions[fname]
                params = fn['params']
                defaults = fn.get('defaults', {})
                if argc > len(params):
                    raise TypeError(f"'{fname}' can toi da {len(params)} tham so, nhan {argc}")
                if argc < len(params):
                    missing = params[argc:]
                    for p in missing:
                        if p not in defaults:
                            raise TypeError(f"'{fname}' thieu tham so '{p}'")
                args = []
                for _ in range(argc):
                    args.insert(0, stack.pop())
                new_env = Env(parent=env)
                for p, a in zip(params, args):
                    new_env.define(p, a)
                for p in params[argc:]:
                    new_env.define(p, _eval_const_ast(defaults[p], env))
                self.call_stack.append({
                    'return_pc': pc,
                    'saved_env': env,
                    'saved_code': code,
                    'saved_n': n,
                })
                env = new_env
                code = fn['code']
                n = len(code)
                pc = 0

            elif op == OP_RETURN:
                result = stack.pop()
                if not self.call_stack:
                    break
                frame = self.call_stack.pop()
                pc = frame['return_pc']
                env = frame['saved_env']
                code = frame['saved_code']
                n = frame['saved_n']
                # Constructor: instance đã nằm trong stack, không push lại
                if frame.get('is_constructor'):
                    pass
                else:
                    stack.append(result)

            elif op == OP_NEW:
                cname, argc = ins.arg
                if cname not in self.classes_data:
                    raise NameError(f"Class chua dinh nghia: '{cname}'")
                cdata = self.classes_data[cname]
                def build_class(cd, nm):
                    parent_obj = None
                    if cd.get('parent'):
                        pdata = self.classes_data.get(cd['parent'], {})
                        parent_obj = build_class(pdata, cd['parent'])
                    return ClassObj(nm, parent_obj, cd['fields'], cd['methods'])
                cls = build_class(cdata, cname)
                inst = Instance(cls)
                args = []
                for _ in range(argc):
                    args.insert(0, stack.pop())
                stack.append(inst)
                if 'new' in cls.methods:
                    m = cls.methods['new']
                    new_env = Env(parent=env)
                    new_env.define('me', inst)
                    for p, a in zip(m['params'], args):
                        new_env.define(p, a)
                    self.call_stack.append({
                        'return_pc': pc,
                        'saved_env': env,
                        'saved_code': code,
                        'saved_n': n,
                        'is_constructor': True,
                    })
                    env = new_env
                    code = m['code']
                    n = len(code)
                    pc = 0
                else:
                    # Không có constructor → bind args vào fields theo thứ tự
                    if argc > 0:
                        all_fields = []
                        c = cls
                        while c:
                            for f in c.fields:
                                if f not in all_fields:
                                    all_fields.append(f)
                            c = c.parent
                        for f, a in zip(all_fields, args):
                            inst.data[f] = a

            elif op == OP_GET_FIELD:
                obj = stack.pop()
                if isinstance(obj, Instance):
                    if ins.arg in obj.data:
                        stack.append(obj.data[ins.arg])
                    else:
                        cc, mm = obj.cls.find_method(ins.arg)
                        if mm is not None:
                            stack.append(('bound', obj, ins.arg))
                        else:
                            raise AttributeError(f"Instance khong co '{ins.arg}'")
                elif isinstance(obj, dict):
                    stack.append(obj.get(ins.arg))
                else:
                    raise TypeError(f"Khong lay duoc field '{ins.arg}'")

            elif op == OP_SET_FIELD:
                value = stack.pop()
                obj = stack.pop()
                if isinstance(obj, Instance):
                    obj.data[ins.arg] = value
                elif isinstance(obj, dict):
                    obj[ins.arg] = value
                else:
                    raise TypeError(f"Khong gan duoc field '{ins.arg}'")

            elif op == OP_CALL_METHOD:
                mname, argc = ins.arg
                args = []
                for _ in range(argc):
                    args.insert(0, stack.pop())
                obj = stack.pop()
                if not isinstance(obj, Instance):
                    # Fallback builtin methods (str/list/dict)
                    stack.append(_builtin_method(obj, mname, args))
                    continue
                cc, mm = obj.cls.find_method(mname)
                if mm is None:
                    raise AttributeError(f"Method '{mname}' khong ton tai")
                new_env = Env(parent=env)
                new_env.define('me', obj)
                for p, a in zip(mm['params'], args):
                    new_env.define(p, a)
                self.call_stack.append({
                    'return_pc': pc,
                    'saved_env': env,
                    'saved_code': code,
                    'saved_n': n,
                    'is_method': True,
                })
                env = new_env
                code = mm['code']
                n = len(code)
                pc = 0

            elif op == OP_LAMBDA:
                params, lcode = ins.arg
                # Tạo closure — hàm Python đóng gói
                def make_closure(_params, _code, _env):
                    def closure(*args):
                        # Mini-VM cho lambda
                        sub_env = Env(parent=_env)
                        for p, a in zip(_params, args):
                            sub_env.define(p, a)
                        sub_vm = VM(_code, self.functions, self.classes_data)
                        sub_vm.env = sub_env
                        # Chạy code, lấy kết quả
                        # Ghi đè run() để trả giá trị cuối
                        sub_stack = sub_vm.stack
                        sub_code = sub_vm.code
                        sub_pc = 0
                        sub_n = len(sub_code)
                        while sub_pc < sub_n:
                            sub_ins = sub_code[sub_pc]
                            sub_pc += 1
                            op2 = sub_ins.op
                            if op2 == OP_CONST:
                                sub_stack.append(sub_ins.arg)
                            elif op2 == OP_LOAD:
                                sub_stack.append(sub_env.get(sub_ins.arg))
                            elif op2 == OP_ADD:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                if isinstance(a, str) or isinstance(b, str):
                                    sub_stack.append(str(a) + str(b))
                                else:
                                    sub_stack.append(a + b)
                            elif op2 == OP_SUB:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a - b)
                            elif op2 == OP_MUL:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a * b)
                            elif op2 == OP_DIV:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a / b)
                            elif op2 == OP_MOD:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a % b)
                            elif op2 == OP_LT:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a < b)
                            elif op2 == OP_GT:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a > b)
                            elif op2 == OP_EQ:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a == b)
                            elif op2 == OP_NEQ:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a != b)
                            elif op2 == OP_LTE:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a <= b)
                            elif op2 == OP_GTE:
                                b = sub_stack.pop(); a = sub_stack.pop()
                                sub_stack.append(a >= b)
                            elif op2 == OP_RETURN:
                                if sub_stack:
                                    return sub_stack.pop()
                                return None
                            elif op2 == OP_CALL:
                                fname, argc = sub_ins.arg
                                if fname in sub_vm.functions:
                                    ff = sub_vm.functions[fname]
                                    cargs = []
                                    for _ in range(argc):
                                        cargs.insert(0, sub_stack.pop())
                                    ce = Env(parent=sub_env)
                                    for p, a in zip(ff['params'], cargs):
                                        ce.define(p, a)
                                    # Mini-call — đơn giản hóa
                                    sub_stack.append(None)
                                else:
                                    try:
                                        bfn = sub_env.get(fname)
                                        cargs = []
                                        for _ in range(argc):
                                            cargs.insert(0, sub_stack.pop())
                                        sub_stack.append(bfn(*cargs))
                                    except Exception:
                                        sub_stack.append(None)
                            else:
                                return None
                        return sub_stack[-1] if sub_stack else None
                    return closure
                stack.append(make_closure(params, lcode, env))

            elif op == OP_BUILD_LIST:
                n_items = ins.arg
                items = []
                for _ in range(n_items):
                    items.insert(0, stack.pop())
                stack.append(items)

            elif op == OP_INDEX:
                idx = stack.pop()
                obj = stack.pop()
                try:
                    if isinstance(idx, float):
                        idx = int(idx)
                    stack.append(obj[idx])
                except Exception as e:
                    raise IndexError(f"Index lỗi: {e}")

            elif op == OP_ADDR:
                stack.append(Ptr(env, ins.arg))

            elif op == OP_DEREF:
                p = stack.pop()
                if not isinstance(p, Ptr):
                    raise TypeError("Khong phai con tro")
                stack.append(p.get())

            elif op == OP_DEREF_SET:
                value = stack.pop()
                p = stack.pop()
                if not isinstance(p, Ptr):
                    raise TypeError("Khong phai con tro")
                p.set(value)

            elif op == OP_BUILD_DICT:
                n_pairs = ins.arg
                d = {}
                for _ in range(n_pairs):
                    v = stack.pop(); k = stack.pop()
                    d[k] = v
                stack.append(d)

            elif op == OP_IN:
                container = stack.pop()
                needle = stack.pop()
                try:
                    stack.append(needle in container)
                except TypeError:
                    stack.append(False)

            elif op == OP_SLICE:
                hi = stack.pop()
                lo = stack.pop()
                obj = stack.pop()
                a = 0 if lo is None else int(lo)
                b = len(obj) if hi is None else int(hi)
                stack.append(obj[a:b])

            elif op == OP_ITER_BEGIN:
                lst = stack.pop()
                if not isinstance(lst, list):
                    raise TypeError(f"groom chi ho tro list, nhan {type(lst).__name__}")
                self.iter_stack.append({'list': lst, 'idx': 0, 'name': ins.arg})

            elif op == OP_ITER_CHECK:
                it = self.iter_stack[-1]
                if it['idx'] >= len(it['list']):
                    pc = ins.arg
                else:
                    env.define(it['name'], it['list'][it['idx']])
                    it['idx'] += 1

            elif op == OP_ITER_END:
                self.iter_stack.pop()

            elif op == OP_HALT:
                break

            else:
                raise RuntimeError(f"Unknown opcode: {op}")

        return '\n'.join(out)


# ═══════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════
def compile_ast(ast):
    return Compiler().compile(ast)


def run_ast(ast):
    comp = Compiler()
    code = comp.compile(ast)
    return VM(code, comp.functions, comp.classes).run()


def run_catpp_vm(source):
    """Chạy source qua VM. Raise Unsupported nếu không hỗ trợ."""
    from interpreter import tokenize, Parser
    ast = Parser(tokenize(source)).parse()
    return run_ast(ast)


def run_catpp_fast(source, timeout=5.0):
    """Thử VM trước, fallback interpreter nếu Unsupported."""
    try:
        return run_catpp_vm(source)
    except Unsupported:
        from interpreter import run_catpp
        return run_catpp(source, timeout=timeout)


def disassemble(source):
    """In bytecode để debug."""
    from interpreter import tokenize, Parser
    ast = Parser(tokenize(source)).parse()
    code = compile_ast(ast)
    lines = []
    for i, ins in enumerate(code):
        arg = f' {ins.arg!r}' if ins.arg is not None else ''
        lines.append(f'{i:4d}  {ins.op}{arg}')
    return '\n'.join(lines)
