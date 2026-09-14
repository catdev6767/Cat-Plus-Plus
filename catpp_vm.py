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
            if target[0] == 'dot':
                # obj.field = value
                self.compile_expr(target[1])  # obj
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
            if target[0] != 'var':
                raise Unsupported("op_assign chi ho tro bien")
            name = target[1]
            self.emit(OP_LOAD, name, line)
            self.compile_expr(rhs)
            op_map = {'+=': OP_ADD, '-=': OP_SUB, '*=': OP_MUL,
                      '/=': OP_DIV, '%=': OP_MOD}
            if op not in op_map:
                raise Unsupported(f"Toan tu '{op}' chua ho tro")
            self.emit(op_map[op], None, line)
            self.emit(OP_STORE, name, line)

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

        if t == 'num':
            self.emit(OP_CONST, expr[1])
        elif t == 'str':
            self.emit(OP_CONST, expr[1])
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
        for f in cls.fields:
            self.data[f] = None


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
        self.instances = {}
        self.stack = []
        self.env = Env()
        self.output = []
        self.call_stack = []

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
                if fname not in self.functions:
                    raise NameError(f"Ham chua dinh nghia: '{fname}'")
                fn = self.functions[fname]
                params = fn['params']
                if argc != len(params):
                    raise TypeError(f"'{fname}' can {len(params)} tham so, nhan {argc}")
                # Pop args (từ phải sang trái)
                args = []
                for _ in range(argc):
                    args.insert(0, stack.pop())
                # Tạo Env con — có parent = env hiện tại (cho global access)
                new_env = Env(parent=env)
                for p, a in zip(params, args):
                    new_env.define(p, a)
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
