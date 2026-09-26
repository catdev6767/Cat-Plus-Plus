"""Cat++ v3 Interpreter — tree-walking evaluator for v3 AST."""
import sys
from tokenizer_v3 import tokenize
from parser_v3 import parse, ParseError


class CatError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line


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
        raise CatError(f"Undefined: '{name}'")

    def set(self, name, val):
        e = self
        while e:
            if name in e.vars:
                e.vars[name] = val
                return
            e = e.parent
        self.vars[name] = val

    def define(self, name, val):
        self.vars[name] = val


class Ref:
    """Reference to a variable in a specific environment."""
    def __init__(self, env, name):
        self.env = env
        self.name = name
    @property
    def value(self):
        return self.env.get(self.name)
    @value.setter
    def value(self, v):
        self.env.set(self.name, v)


class Func:
    def __init__(self, name, params, body, env, ret_type=None):
        self.name = name
        self.params = params  # list of (type, name)
        self.body = body
        self.env = env
        self.ret_type = ret_type


class ClassObj:
    def __init__(self, name, parent, members, env):
        self.name = name
        self.parent = parent
        self.env = env
        self.fields = []
        self.methods = {}
        for m in members:
            if m[0] == 'field':
                _, ftype, fname = m
                self.fields.append((ftype, fname))
            elif m[0] == 'func':
                _, rtype, mname, mparams, mbody = m
                self.methods[mname] = m


class Instance:
    def __init__(self, cls):
        self.cls = cls
        self.data = {}
        all_fields = []
        c = cls
        while c:
            for _, fname in c.fields:
                if fname not in all_fields:
                    all_fields.append(fname)
            c = c.parent
        for fname in all_fields:
            self.data[fname] = None


class EnumObj:
    def __init__(self, name, members):
        self.name = name
        self.members = members
        self.values = {m: f'{name}.{m}' for m in members}


class ReturnEx(Exception):
    def __init__(self, val): self.val = val
class BreakEx(Exception): pass
class ContinueEx(Exception): pass


class Interp:
    def __init__(self):
        self.output = []
        self.global_env = Env()
        self.current_class = None
        self.current_instance = None

    def run(self, ast):
        # Pass 1: collect structs, enums, classes, funcs
        for stmt in ast[1]:
            if stmt[0] == 'struct':
                _, name, fields = stmt
                # Register struct as class
                cls = ClassObj(name, None, [('field', ft, fn) for ft, fn in fields], self.global_env)
                self.global_env.define(name, cls)
            elif stmt[0] == 'enum':
                _, name, members = stmt
                self.global_env.define(name, EnumObj(name, members))
            elif stmt[0] == 'func':
                _, rtype, name, params, body = stmt
                fn = Func(name, params, body, self.global_env, rtype)
                self.global_env.define(name, fn)
            elif stmt[0] == 'class':
                _, name, parent_name, members = stmt
                parent = None
                if parent_name:
                    try:
                        parent = self.global_env.get(parent_name)
                    except CatError:
                        pass
                cls = ClassObj(name, parent, members, self.global_env)
                self.global_env.define(name, cls)

        # Pass 2: exec
        for stmt in ast[1]:
            if stmt[0] in ('struct', 'enum', 'func', 'class'):
                continue
            self.exec_stmt(stmt, self.global_env)

        # Auto-call main() like C++
        try:
            main_fn = self.global_env.get('main')
            if isinstance(main_fn, Func):
                self.call_func(main_fn, [])
        except CatError:
            pass

        return '\n'.join(self.output)

    def fmt(self, v):
        if v is True: return 'nod'
        if v is False: return 'shake'
        if v is None: return 'hungry'
        if isinstance(v, float):
            if v == int(v): return str(int(v))
            return str(v)
        if isinstance(v, list):
            return '[' + ', '.join(self.fmt(x) for x in v) + ']'
        if isinstance(v, dict):
            return '{' + ', '.join(f'{self.fmt(k)}: {self.fmt(vv)}' for k, vv in v.items()) + '}'
        if isinstance(v, Instance):
            return f'<{v.cls.name}>'
        return str(v)

    def exec_stmt(self, s, env):
        t = s[0]

        if t in ('directive', 'struct', 'enum', 'func', 'class'):
            return

        if t == 'var_decl':
            _, vtype, name, init = s
            base, ptr_depth, array_size, _ = vtype
            # Array type: paw int arr[3]
            if array_size is not None:
                if isinstance(array_size, tuple) and array_size[0] == 'num':
                    n = int(array_size[1])
                else:
                    n = int(array_size) if isinstance(array_size, (int, float)) else 0
                val = [None] * n
                env.define(name, val)
                return
            # Pointer / regular
            val = None
            if init is not None:
                val = self.eval(init, env)
            env.define(name, val)
            return

        if t == 'meow':
            val = self.eval(s[1], env)
            self.output.append(self.fmt(val))
            return

        if t == 'return':
            val = self.eval(s[1], env) if s[1] else None
            raise ReturnEx(val)

        if t == 'if':
            _, cond, then, els = s
            if self.eval(cond, env):
                for st in then: self.exec_stmt(st, env)
            elif els:
                for st in els: self.exec_stmt(st, env)
            return

        if t == 'while':
            _, cond, body = s
            count = 0
            while self.eval(cond, env):
                count += 1
                if count > 1_000_000:
                    raise CatError('Infinite loop')
                try:
                    for st in body: self.exec_stmt(st, env)
                except BreakEx: break
                except ContinueEx: continue
            return

        if t == 'for':
            _, init, cond, step, body = s
            self.exec_stmt(init, env)
            count = 0
            while self.eval(cond, env):
                count += 1
                if count > 1_000_000:
                    raise CatError('Infinite loop')
                try:
                    for st in body: self.exec_stmt(st, env)
                except BreakEx: break
                except ContinueEx: pass
                self.eval(step, env)
            return

        if t == 'break': raise BreakEx()
        if t == 'continue': raise ContinueEx()

        if t == 'block':
            for st in s[1]: self.exec_stmt(st, env)
            return

        if t == 'expr_stmt':
            self.eval(s[1], env)
            return

        if t == 'delete':
            self.eval(s[1], env)
            return

        raise CatError(f"Unknown stmt: {t}")

    def eval(self, e, env):
        t = e[0]

        if t == 'num': return e[1]
        if t == 'str': return e[1]
        if t == 'char': return e[1]
        if t == 'bool': return e[1]
        if t == 'null': return None

        if t == 'me':
            if self.current_instance is not None:
                return self.current_instance
            return None

        if t == 'var':
            v = env.get(e[1])
            if isinstance(v, Ref):
                return v.value
            return v

        if t == 'array':
            return [self.eval(x, env) for x in e[1]]

        if t == 'binop':
            op = e[1]
            a = self.eval(e[2], env)
            b = self.eval(e[3], env)
            return self.binop(op, a, b)

        if t == 'unary':
            op = e[1]
            v = self.eval(e[2], env)
            if op == '-': return -v
            if op == '!': return not v
            raise CatError(f'Unknown unary: {op}')

        if t == 'address_of':
            inner = e[1]
            if inner[0] == 'var':
                return ('ref', env, inner[1])
            raise CatError('& only on var')

        if t == 'deref':
            ptr = self.eval(e[1], env)
            if isinstance(ptr, tuple) and ptr and ptr[0] == 'ref':
                return ptr[1].get(ptr[2])
            raise CatError('* expects pointer')

        if t == 'assign':
            op, target, rhs = e[1], e[2], e[3]
            val = self.eval(rhs, env)
            if target[0] == 'var':
                name = target[1]
                try:
                    cur = env.get(name)
                except CatError:
                    cur = None
                if isinstance(cur, Ref):
                    if op == '=':
                        cur.value = val
                        return val
                    actual = cur.value
                    if op == 'ADD_EQ': nv = actual + val
                    elif op == 'SUB_EQ': nv = actual - val
                    elif op == 'MUL_EQ': nv = actual * val
                    elif op == 'DIV_EQ': nv = actual / val
                    elif op == 'MOD_EQ': nv = actual % val
                    else: nv = val
                    cur.value = nv
                    return nv
                if op == '=':
                    env.set(name, val)
                else:
                    cur = env.get(name)
                    if op == 'ADD_EQ': env.set(name, cur + val)
                    elif op == 'SUB_EQ': env.set(name, cur - val)
                    elif op == 'MUL_EQ': env.set(name, cur * val)
                    elif op == 'DIV_EQ': env.set(name, cur / val)
                    elif op == 'MOD_EQ': env.set(name, cur % val)
                return val
            if target[0] == 'index':
                obj = self.eval(target[1], env)
                idx = self.eval(target[2], env)
                obj[int(idx)] = val
                return val
            if target[0] == 'member':
                obj = self.eval(target[1], env)
                if isinstance(obj, Instance):
                    obj.data[target[2]] = val
                    return val
            if target[0] == 'deref':
                ptr = self.eval(target[1], env)
                if isinstance(ptr, tuple) and ptr[0] == 'ref':
                    ptr[1].set(ptr[2], val)
                    return val
            raise CatError('Invalid assign target')

        if t == 'call':
            fn_expr = e[1]
            args = [self.eval(a, env) for a in e[2]]

            # Class constructor
            if fn_expr[0] == 'var':
                name = fn_expr[1]
                try:
                    fn = env.get(name)
                except CatError:
                    fn = None
                if isinstance(fn, ClassObj):
                    return self.instantiate(fn, args)
                if isinstance(fn, Func):
                    return self.call_func(fn, args, e[2], env)
                # Builtin
                return self.call_builtin(name, args)
            if fn_expr[0] == 'member':
                obj = self.eval(fn_expr[1], env)
                mname = fn_expr[2]
                if isinstance(obj, Instance):
                    return self.call_method(obj, mname, args)
            raise CatError('Invalid call')

        if t == 'member':
            obj = self.eval(e[1], env)
            name = e[2]
            if isinstance(obj, Instance):
                if name in obj.data:
                    return obj.data[name]
                return ('bound', obj, name)
            if isinstance(obj, dict):
                return obj.get(name)
            if isinstance(obj, EnumObj):
                return obj.values.get(name)
            raise CatError(f'Unknown member: {name}')

        if t == 'arrow':
            obj = self.eval(e[1], env)
            name = e[2]
            if isinstance(obj, Instance):
                if name in obj.data:
                    return obj.data[name]
                return ('bound', obj, name)
            raise CatError(f'Unknown -> {name}')

        if t == 'index':
            obj = self.eval(e[1], env)
            idx = self.eval(e[2], env)
            if isinstance(obj, str):
                return obj[int(idx)]
            if isinstance(obj, list):
                return obj[int(idx)]
            if isinstance(obj, dict):
                return obj.get(idx)
            raise CatError('Index error')

        if t == 'new':
            _, typename, args_expr = e
            args = [self.eval(a, env) for a in args_expr]
            cls = env.get(typename[0])
            if isinstance(cls, ClassObj):
                return self.instantiate(cls, args)
            raise CatError(f'Unknown class: {typename[0]}')

        if t == 'sizeof_type':
            sizes = {'int': 4, 'float': 8, 'double': 8, 'bool': 1,
                     'char': 1, 'long': 8, 'short': 2, 'str': 8, 'void': 1}
            return sizes.get(e[1], 8)

        if t == 'sizeof':
            v = self.eval(e[1], env)
            if isinstance(v, bool): return 1
            if isinstance(v, int): return 4
            if isinstance(v, float): return 8
            if isinstance(v, str): return len(v)
            return 8

        raise CatError(f'Unknown expr: {t}')

    def binop(self, op, a, b):
        # Safe None handling
        if a is None: a = 0 if op not in ('+',) else ''
        if b is None: b = 0 if op not in ('+',) else ''
        if op == '+':
            if isinstance(a, str) or isinstance(b, str):
                return str(a) + str(b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/':
            if b == 0: raise CatError('Div by 0')
            if isinstance(a, int) and isinstance(b, int):
                return a // b
            return a / b
        if op == '%': return a % b
        if op == '==': return a == b
        if op == '!=': return a != b
        if op == '<': return a < b
        if op == '>': return a > b
        if op == '<=': return a <= b
        if op == '>=': return a >= b
        if op == '&&': return bool(a) and bool(b)
        if op == '||': return bool(a) or bool(b)
        if op == '<<': return int(a) << int(b)
        if op == '>>': return int(a) >> int(b)
        raise CatError(f'Unknown op: {op}')

    def instantiate(self, cls, args):
        inst = Instance(cls)
        # Find constructor (look for 'new' OR class name in chain)
        c = cls
        ctor = None
        ctor_cls = None
        while c:
            if 'new' in c.methods:
                ctor = c.methods['new']; ctor_cls = c; break
            if c.name in c.methods:
                ctor = c.methods[c.name]; ctor_cls = c; break
            c = c.parent
        if ctor:
            self.call_method_impl(inst, ctor, args, ctor_cls)
        return inst

    def call_method_impl(self, inst, method, args, cls):
        _, rtype, mname, mparams, mbody = method
        fenv = Env(cls.env)
        fenv.define('me', inst)
        for (ptype, pname), aval in zip(mparams, args):
            fenv.define(pname, aval)
        old_inst = self.current_instance
        old_cls = self.current_class
        self.current_instance = inst
        self.current_class = cls
        try:
            for st in mbody:
                self.exec_stmt(st, fenv)
        except ReturnEx as r:
            return r.val
        finally:
            self.current_instance = old_inst
            self.current_class = old_cls
        return None

    def call_method(self, inst, mname, args):
        cls = inst.cls
        while cls:
            if mname in cls.methods:
                return self.call_method_impl(inst, cls.methods[mname], args, cls)
            cls = cls.parent
        raise CatError(f'Unknown method: {mname}')

    def call_func(self, fn, args, arg_exprs=None, caller_env=None):
        env = Env(fn.env)
        if len(args) != len(fn.params):
            raise CatError(f"{fn.name} expects {len(fn.params)} args, got {len(args)}")
        for i, ((ptype, pname), aval) in enumerate(zip(fn.params, args)):
            base = ptype[0]
            # Reference parameter → bind Ref to caller's variable
            if base.startswith('REF_') and arg_exprs and caller_env is not None:
                aexpr = arg_exprs[i]
                if aexpr[0] == 'var':
                    env.define(pname, Ref(caller_env, aexpr[1]))
                    continue
            env.define(pname, aval)
        try:
            for st in fn.body:
                self.exec_stmt(st, env)
        except ReturnEx as r:
            return r.val
        return None

    def call_builtin(self, name, args):
        # Basic builtins
        import math as _math
        if name == 'print':
            for a in args: print(a)
            return None
        if name == 'sqrt': return _math.sqrt(args[0])
        if name == 'pow': return args[0] ** args[1]
        if name == 'abs': return abs(args[0])
        if name == 'floor': return _math.floor(args[0])
        if name == 'ceil': return _math.ceil(args[0])
        if name == 'sin': return _math.sin(args[0])
        if name == 'cos': return _math.cos(args[0])
        if name == 'tan': return _math.tan(args[0])
        if name == 'exit':
            raise SystemExit(args[0] if args else 0)
        raise CatError(f'Unknown builtin: {name}')


def run_catpp_v3(source):
    ast = parse(source)
    return Interp().run(ast)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: interpreter_v3.py <file.cat>')
        sys.exit(1)
    src = open(sys.argv[1]).read()
    try:
        print(run_catpp_v3(src))
    except ParseError as e:
        print(f'ParseError at {e.line}:{e.col}: {e}')
        sys.exit(1)
    except CatError as e:
        print(f'Error: {e}')
        sys.exit(1)
