#!/usr/bin/env python3
"""Cat++ -> C native transpiler.

Sinh C code native (int32_t, double, char*) thay vi Value boxed.
Yeu cau code co type annotation day du.
Neu thieu type -> bao Unsupported, caller fallback transpiler_c.py.
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interpreter import tokenize, Parser, CatError


class Unsupported(Exception):
    pass


C_TYPE = {
    'i8': 'int8_t', 'i16': 'int16_t', 'i32': 'int32_t', 'i64': 'int64_t',
    'u8': 'uint8_t', 'u16': 'uint16_t', 'u32': 'uint32_t', 'u64': 'uint64_t',
    'bool': 'int', 'float': 'double', 'f32': 'float', 'f64': 'double',
    'int': 'int64_t', 'char': 'char', 'byte': 'uint8_t',
    'str': 'char*',
}

PRINTF_FMT = {
    'i8': '%d', 'i16': '%d', 'i32': '%d', 'i64': '%lld',
    'u8': '%u', 'u16': '%u', 'u32': '%u', 'u64': '%llu',
    'bool': '%d', 'float': '%g', 'f32': '%g', 'f64': '%g',
    'int': '%lld', 'char': '%c', 'byte': '%u',
    'str': '%s',
}

INTEGRAL = {'i8','i16','i32','i64','u8','u16','u32','u64','bool','char','byte','int'}
FLOAT = {'float','f32','f64'}


class NativeCompiler:
    def __init__(self):
        self.output = []
        self.indent = 0
        self.func_sigs = {}
        self.scopes = [{}]
        self.tc = 0

    def line(self, s=''):
        self.output.append('    ' * self.indent + s)

    def push_scope(self): self.scopes.append({})
    def pop_scope(self): self.scopes.pop()
    def lookup(self, name):
        for s in reversed(self.scopes):
            if name in s: return s[name]
        return None
    def define(self, name, t): self.scopes[-1][name] = t

    def infer(self, e):
        t = e[0]
        if t == 'num':
            return 'float' if isinstance(e[1], float) else 'int'
        if t == 'str': return 'str'
        if t == 'bool': return 'bool'
        if t == 'null': return None
        if t == 'var': return self.lookup(e[1])
        if t == 'neg': return self.infer(e[1])
        if t == 'not': return 'bool'
        if t in ('+','-','*'):
            lt = self.infer(e[1]); rt = self.infer(e[2])
            if lt is None or rt is None: return None
            if 'str' in (lt, rt): return None
            if lt in FLOAT or rt in FLOAT: return 'float'
            return lt if lt in INTEGRAL else rt
        if t == '/': return 'float'
        if t == '%': return 'int'
        if t in ('==','!=','<','>','<=','>='): return 'bool'
        if t in ('and','or'): return 'bool'
        if t in ('&','|','^','SHL','SHR'): return 'int'
        if t == 'call':
            if e[1] in self.func_sigs:
                return self.func_sigs[e[1]][2]
            return None
        if t == 'cast': return e[1].lower()
        return None

    def cast_to(self, code, from_t, to_t):
        if from_t == to_t or from_t is None or to_t is None:
            return code
        ct = C_TYPE.get(to_t)
        if not ct: return code
        if from_t == to_t: return code
        return f'(({ct})({code}))'

    def expr(self, e):
        t = e[0]
        if t == 'num':
            v = e[1]
            if isinstance(v, float): return repr(v)
            return f'{int(v)}'
        if t == 'str':
            s = e[1].replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\t','\\t')
            return f'"{s}"'
        if t == 'bool': return '1' if e[1] else '0'
        if t == 'var':
            if self.lookup(e[1]) is None and e[1] not in self.func_sigs:
                raise Unsupported(f"Bien '{e[1]}' chua co type")
            return e[1]
        if t == 'neg': return f'(-({self.expr(e[1])}))'
        if t == 'not': return f'(!({self.expr(e[1])}))'
        if t in ('+','-','*','/','%'):
            return f'({self.expr(e[1])} {t} {self.expr(e[2])})'
        if t in ('==','!=','<','>','<=','>='):
            return f'({self.expr(e[1])} {t} {self.expr(e[2])})'
        if t in ('&','|','^'):
            return f'({self.expr(e[1])} {t} {self.expr(e[2])})'
        if t == 'SHL': return f'({self.expr(e[1])} << {self.expr(e[2])})'
        if t == 'SHR': return f'({self.expr(e[1])} >> {self.expr(e[2])})'
        if t == 'and': return f'({self.expr(e[1])} && {self.expr(e[2])})'
        if t == 'or': return f'({self.expr(e[1])} || {self.expr(e[2])})'
        if t == 'call':
            name = e[1]
            if name not in self.func_sigs:
                raise Unsupported(f"Ham '{name}' chua co signature")
            pnames, ptypes, ret = self.func_sigs[name]
            args_raw = e[2]
            if len(args_raw) != len(ptypes):
                raise Unsupported(f"Ham '{name}' can {len(ptypes)} args, nhan {len(args_raw)}")
            casted = []
            for a, want_t in zip(args_raw, ptypes):
                code = self.expr(a)
                got_t = self.infer(a)
                casted.append(self.cast_to(code, got_t, want_t))
            return f'{name}({", ".join(casted)})'
        if t == 'cast':
            tn = e[1].lower()
            code = self.expr(e[2])
            ct = C_TYPE.get(tn)
            if not ct: raise Unsupported(f"Cast type '{tn}' chua ho tro")
            return f'(({ct})({code}))'
        raise Unsupported(f"Expr '{t}' khong native")

    def stmt(self, s):
        t = s[0]
        if t == 'let':
            name = s[1]; expr = s[2]
            ann = s[4] if len(s) > 4 else None
            vt = ann or self.infer(expr)
            if vt is None or vt not in C_TYPE:
                raise Unsupported(f"Bien '{name}' khong co type ro rang")
            self.define(name, vt)
            code = self.expr(expr)
            code = self.cast_to(code, self.infer(expr), vt)
            self.line(f'{C_TYPE[vt]} {name} = {code};')
        elif t == 'assign':
            name = s[1]
            vt = self.lookup(name)
            if vt is None: raise Unsupported(f"Bien '{name}' chua khai bao")
            code = self.expr(s[2])
            code = self.cast_to(code, self.infer(s[2]), vt)
            self.line(f'{name} = {code};')
        elif t == 'op_assign':
            target, op, rhs = s[1], s[2], s[3]
            if target[0] != 'var': raise Unsupported("op_assign chi ho tro bien")
            name = target[1]
            if self.lookup(name) is None:
                raise Unsupported(f"Bien '{name}' chua khai bao")
            self.line(f'{name} {op} {self.expr(rhs)};')
        elif t == 'print':
            code = self.expr(s[1])
            vt = self.infer(s[1])
            if vt is None: raise Unsupported("meow khong biet type")
            fmt = PRINTF_FMT.get(vt, '%lld')
            self.line(f'printf("{fmt}\\n", {code});')
        elif t == 'return':
            self.line(f'return {self.expr(s[1])};')
        elif t == 'if':
            self.line(f'if ({self.expr(s[1])}) {{')
            self.indent += 1; self.push_scope()
            for x in s[2]: self.stmt(x)
            self.pop_scope(); self.indent -= 1
            if s[3]:
                self.line('} else {')
                self.indent += 1; self.push_scope()
                for x in s[3]: self.stmt(x)
                self.pop_scope(); self.indent -= 1
            self.line('}')
        elif t == 'while':
            self.line(f'while ({self.expr(s[1])}) {{')
            self.indent += 1; self.push_scope()
            for x in s[2]: self.stmt(x)
            self.pop_scope(); self.indent -= 1
            self.line('}')
        elif t == 'stop': self.line('break;')
        elif t == 'skip': self.line('continue;')
        elif t == 'expr':
            self.line(f'(void)({self.expr(s[1])});')
        else:
            raise Unsupported(f"Stmt '{t}' khong native")

    def func(self, s):
        name = s[1]; params = s[2]; body = s[4]
        param_types = s[6] if len(s) > 6 else {}
        return_type = s[7] if len(s) > 7 else None

        for p in params:
            if p not in param_types:
                raise Unsupported(f"Ham '{name}': param '{p}' thieu type")
        if not return_type:
            raise Unsupported(f"Ham '{name}': thieu return type")

        self.push_scope()
        for p in params:
            self.define(p, param_types[p])

        arg_list = ', '.join(f'{C_TYPE[param_types[p]]} {p}' for p in params)
        ret_c = C_TYPE[return_type]
        self.line(f'static {ret_c} {name}({arg_list if arg_list else "void"}) {{')
        self.indent += 1

        for stmt in body:
            self.stmt(stmt)

        if not body or body[-1][0] != 'return':
            self.line('return 0;')

        self.indent -= 1
        self.line('}')
        self.line('')
        self.pop_scope()

    def compile(self, ast):
        for s in ast:
            if s[0] == 'func':
                name = s[1]; params = s[2]
                ptypes = s[6] if len(s) > 6 else {}
                rtype = s[7] if len(s) > 7 else None
                if not rtype:
                    raise Unsupported(f"Ham '{name}' thieu return type")
                for p in params:
                    if p not in ptypes:
                        raise Unsupported(f"Ham '{name}': param '{p}' thieu type")
                self.func_sigs[name] = (params, [ptypes[p] for p in params], rtype)

        self.output.append('#include <stdio.h>')
        self.output.append('#include <stdint.h>')
        self.output.append('#include <stdbool.h>')
        self.output.append('')

        for name, (pnames, ptypes, rtype) in self.func_sigs.items():
            args = ', '.join(f'{C_TYPE[t]}' for t in ptypes) if ptypes else 'void'
            self.line(f'static {C_TYPE[rtype]} {name}({args});')
        self.output.append('')

        for s in ast:
            if s[0] == 'func':
                self.func(s)

        self.line('int main(void) {')
        self.indent += 1
        top = [s for s in ast if s[0] != 'func']
        for s in top:
            self.stmt(s)
        self.line('return 0;')
        self.indent -= 1
        self.line('}')
        return '\n'.join(self.output)


def transpile(source):
    ast = Parser(tokenize(source)).parse()
    return NativeCompiler().compile(ast)


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    src = sys.argv[1]
    with open(src, encoding='utf-8') as f: source = f.read()
    try:
        c_code = transpile(source)
    except (Unsupported, CatError) as e:
        print(f'X {e}', file=sys.stderr); return 1
    out = src.rsplit('.', 1)[0] + '.native.c'
    if '-o' in sys.argv:
        out = sys.argv[sys.argv.index('-o')+1]
    with open(out, 'w', encoding='utf-8') as f: f.write(c_code)
    print(f'OK {out}')
    if '--run' in sys.argv:
        binp = out.rsplit('.', 1)[0]
        r = subprocess.run(['gcc', '-O2', '-lm', '-o', binp, out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print('gcc fail:'); print(r.stderr); return 1
        r = subprocess.run([binp], capture_output=True, text=True)
        print('--- Output ---'); print(r.stdout, end='')
        if r.stderr: print(r.stderr, end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
