#!/usr/bin/env python3
"""Cat++ → C transpiler.
Dùng AST từ interpreter.py, sinh C code.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter import tokenize, Parser, Tok


class CGen:
    def __init__(self):
        self.includes = set()
        self.functions = []
        self.indent = 0
        self.temp_counter = 0
        self.vars = {}  # name → type
        self.structs = {}  # name → [fields]
        self.declarations = []  # global typedef/enum/struct

    def new_temp(self):
        self.temp_counter += 1
        return f'_t{self.temp_counter}'

    def ind(self):
        return '    ' * self.indent

    # ═══ EXPRESSIONS ═══
    def expr(self, e):
        t = e[0]
        if t == 'num':
            v = e[1]
            if isinstance(v, int):
                return str(v)
            return repr(v)
        if t == 'str':
            return self.c_string(e[1])
        if t == 'bool':
            return '1' if e[1] else '0'
        if t == 'null':
            return 'NULL'
        if t == 'var':
            return e[1]
        if t == 'list':
            # Chỉ hỗ trợ list đơn giản → C array literal
            items = ', '.join(self.expr(x) for x in e[1])
            return '{' + items + '}'
        if t == 'neg':
            return '(' + '-' + self.expr(e[1]) + ')'
        if t == 'not':
            return '(' + '!' + self.expr(e[1]) + ')'
        if t == 'bitnot':
            return '(' + '~' + self.expr(e[1]) + ')'
        if t == 'and':
            return '(' + self.expr(e[1]) + ' && ' + self.expr(e[2]) + ')'
        if t == 'or':
            return '(' + self.expr(e[1]) + ' || ' + self.expr(e[2]) + ')'
        if t == 'in':
            self.includes.add('catpp_rt.h')
            return f'catpp_in({self.expr(e[1])}, {self.expr(e[2])})'
        if t == 'cast':
            # cast(type, value) → (type)value
            ctype = self.c_type(e[1])
            return f'(({ctype}){self.expr(e[2])})'
        if t == 'sizeof':
            return f'sizeof({self.expr(e[1])})'
        if t == 'sizeof_type':
            return f'sizeof({self.c_type(e[1])})'
        if t == 'call':
            name = e[1]
            args = ', '.join(self.expr(a) for a in e[2])
            # Map builtins
            if name == 'say':
                self.includes.add('stdio.h')
                return f'catpp_str({args})'
            return f'{name}({args})'
        if t == 'method_call':
            obj = self.expr(e[1])
            name = e[2]
            args = ', '.join(self.expr(a) for a in e[3])
            self.includes.add('catpp_rt.h')
            return f'catpp_method_{name}({obj}{", " + args if args else ""})'
        if t == 'index':
            return f'{self.expr(e[1])}[{self.expr(e[2])}]'
        if t == 'dot':
            return f'{self.expr(e[1])}.{e[2]}'
        if t in ('+','-','*','/','%'):
            return f'({self.expr(e[1])} {t} {self.expr(e[2])})'
        if t in ('&','|','^','SHL','SHR'):
            cop = {'SHL': '<<', 'SHR': '>>'}.get(t, t)
            return f'({self.expr(e[1])} {cop} {self.expr(e[2])})'
        if t in ('==','!=','<','>','<=','>='):
            return f'({self.expr(e[1])} {t} {self.expr(e[2])})'
        if t == 'ternary':
            return f'({self.expr(e[1])} ? {self.expr(e[2])} : {self.expr(e[3])})'
        if t == 'coalesce':
            return f'({self.expr(e[1])} ? {self.expr(e[1])} : {self.expr(e[2])})'
        if t == 'asm':
            return f'__asm__ volatile("{e[1]}")'
        if t == 'list':
            return '{' + ', '.join(self.expr(x) for x in e[1]) + '}'
        raise NotImplementedError(f'expr type: {t}')

    def c_string(self, s):
        # Escape C string
        out = ''
        for ch in s:
            if ch == '"': out += '\\"'
            elif ch == '\\': out += '\\\\'
            elif ch == '\n': out += '\\n'
            elif ch == '\t': out += '\\t'
            elif ord(ch) < 32: out += f'\\x{ord(ch):02x}'
            else: out += ch
        return '"' + out + '"'

    def c_type(self, name):
        t = name.lower()
        m = {
            'i8':'int8_t','i16':'int16_t','i32':'int32_t','i64':'int64_t',
            'u8':'uint8_t','u16':'uint16_t','u32':'uint32_t','u64':'uint64_t',
            'int':'long','float':'double','bool':'int','ptr':'void*','pointer':'void*',
            'char':'char','byte':'uint8_t','str':'char*',
        }
        if t in m:
            self.includes.add('stdint.h')
            return m[t]
        return name  # struct name

    # ═══ STATEMENTS ═══
    def stmt(self, s, out):
        t = s[0]
        if t == 'let':
            name = s[1]
            e = s[2]
            # Struct constructor?
            if isinstance(e, tuple) and e[0] == 'call' and e[1] in self.structs:
                args = ', '.join(self.expr(a) for a in e[2])
                ctype = e[1]
                out.append(f'{self.ind()}{ctype} {name} = {{{args}}};')
                self.vars[name] = ctype
                return
            val = self.expr(e)
            # Đoán type
            if isinstance(e, tuple) and e[0] == 'num':
                if isinstance(e[1], int): ctype = 'long'
                else: ctype = 'double'
            elif isinstance(e, tuple) and e[0] == 'str':
                ctype = 'char*'
            elif isinstance(e, tuple) and e[0] == 'bool':
                ctype = 'int'
            elif isinstance(e, tuple) and e[0] == 'cast':
                ctype = self.c_type(e[1])
            else:
                ctype = 'long'
            out.append(f'{self.ind()}{ctype} {name} = {val};')
            self.vars[name] = ctype
        elif t == 'assign':
            out.append(f'{self.ind()}{s[1]} = {self.expr(s[2])};')
        elif t == 'assign_target':
            target = s[1]
            val = self.expr(s[2])
            if target[0] == 'index':
                lhs = f'{self.expr(target[1])}[{self.expr(target[2])}]'
            elif target[0] == 'dot':
                lhs = f'{self.expr(target[1])}.{target[2]}'
            else:
                lhs = self.expr(target)
            out.append(f'{self.ind()}{lhs} = {val};')
        elif t == 'op_assign':
            target, op, rhs = s[1], s[2], s[3]
            if target[0] == 'var':
                lhs = target[1]
            elif target[0] == 'index':
                lhs = f'{self.expr(target[1])}[{self.expr(target[2])}]'
            else:
                lhs = self.expr(target)
            out.append(f'{self.ind()}{lhs} {op} {self.expr(rhs)};')
        elif t == 'print':
            self.includes.add('stdio.h')
            e = s[1]
            # Detect format
            if isinstance(e, tuple) and e[0] == 'str':
                out.append(f'{self.ind()}printf("%s\\n", {self.expr(e)});')
            else:
                # Đoán format từ biến
                out.append(f'{self.ind()}catpp_print({self.expr(e)});')
                self.includes.add('catpp_rt.h')
        elif t == 'expr':
            out.append(f'{self.ind()}{self.expr(s[1])};')
        elif t == 'if':
            out.append(f'{self.ind()}if ({self.expr(s[1])}) {{')
            self.indent += 1
            for x in s[2]: self.stmt(x, out)
            self.indent -= 1
            if s[3]:
                out.append(f'{self.ind()}}} else {{')
                self.indent += 1
                for x in s[3]: self.stmt(x, out)
                self.indent -= 1
            out.append(f'{self.ind()}}}')
        elif t == 'while':
            out.append(f'{self.ind()}while ({self.expr(s[1])}) {{')
            self.indent += 1
            for x in s[2]: self.stmt(x, out)
            self.indent -= 1
            out.append(f'{self.ind()}}}')
        elif t == 'each':
            # groom x of arr → for
            var = s[1]
            arr = self.expr(s[2])
            out.append(f'{self.ind()}for (long _i = 0; _i < catpp_len({arr}); _i++) {{')
            out.append(f'{self.ind()}    long {var} = {arr}[_i];')
            self.indent += 1
            for x in s[3]: self.stmt(x, out)
            self.indent -= 1
            out.append(f'{self.ind()}}}')
        elif t == 'return':
            out.append(f'{self.ind()}return {self.expr(s[1])};')
        elif t == 'stop':
            out.append(f'{self.ind()}break;')
        elif t == 'skip':
            out.append(f'{self.ind()}continue;')
        elif t == 'func':
            self.gen_func(s[1], s[2], s[3])
        elif t == 'struct':
            name = s[1]; fields = s[2]
            self.structs[name] = fields
            decl = []
            decl.append(f'typedef struct {name} {{')
            for f in fields:
                decl.append(f'    long {f};')
            decl.append(f'}} {name};')
            self.declarations.extend(decl)
        elif t == 'enum':
            name = s[1]; members = s[2]
            decl = []
            decl.append(f'enum {name} {{')
            decl.append('    ' + ', '.join(members))
            decl.append(f'}};')
            self.declarations.extend(decl)
        elif t == 'use':
            # use "file.cat" → include file.c
            fname = s[1].replace('.cat', '.h')
            out.append(f'#include "{fname}"')
        else:
            out.append(f'{self.ind()}/* unknown stmt: {t} */')

    def gen_func(self, name, params, body):
        # Đoán return type từ body
        rtype = 'void'
        for st in body:
            if st[0] == 'return':
                e = st[1]
                if isinstance(e, tuple):
                    if e[0] == 'num':
                        rtype = 'long' if isinstance(e[1], int) else 'double'
                    elif e[0] == 'str':
                        rtype = 'char*'
        lines = []
        self.indent = 1
        for st in body:
            self.stmt(st, lines)
        self.indent = 0
        sig = f'{rtype} {name}({", ".join("long " + p for p in params)}) {{\n'
        sig += '\n'.join(lines)
        sig += '\n}'
        self.functions.append(sig)

    def gen(self, ast):
        self.includes.add('catpp_rt.h')
        body = []
        for s in ast:
            self.stmt(s, body)
        out = []
        # Main
        out.append('int main(void) {')
        for line in body:
            out.append('    ' + line)
        out.append('    return 0;')
        out.append('}')
        # Header
        header = '#include <stdint.h>\n'
        header += '#include <stdio.h>\n'
        header += '#include <stdlib.h>\n'
        header += '#include "catpp_rt.h"\n\n'
        # Order: header → declarations → functions → main
        decls = '\n'.join(self.declarations)
        funcs = '\n\n'.join(self.functions)
        return header + decls + '\n\n' + funcs + '\n\n' + '\n'.join(out) + '\n'


def transpile(code):
    ast = Parser(tokenize(code)).parse()
    gen = CGen()
    return gen.gen(ast)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: transpiler.py <file.cat> [-o output.c]')
        sys.exit(1)
    src = open(sys.argv[1], encoding='utf-8').read()
    c_code = transpile(src)
    if '-o' in sys.argv:
        out = sys.argv[sys.argv.index('-o') + 1]
        open(out, 'w').write(c_code)
        print(f'✓ Ghi {out}')
    else:
        print(c_code)
