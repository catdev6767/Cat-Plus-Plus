#!/usr/bin/env python3
"""2-pass type inference cho transpiler."""
import os, re

path = 'tools/transpiler.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

# 1. Thêm state cho func_returns
if 'self.func_returns = {}' not in c:
    c = c.replace(
        "        self.declarations = []  # global typedef/enum/struct",
        "        self.declarations = []  # global typedef/enum/struct\n        self.func_returns = {}  # name → C type",
        1
    )

# 2. Thêm 2 hàm infer
infer_funcs = '''
    def infer_return_type(self, body):
        """Suy return type từ body."""
        locals_ = {}
        rtype = 'void'
        for st in body:
            if not isinstance(st, tuple): continue
            if st[0] == 'let':
                name = st[1]; e = st[2]
                if isinstance(e, tuple):
                    if e[0] == 'call' and e[1] in self.structs:
                        locals_[name] = e[1]
                    elif e[0] == 'call' and e[1] in self.func_returns:
                        locals_[name] = self.func_returns[e[1]]
                    elif e[0] == 'num':
                        locals_[name] = 'long' if isinstance(e[1], int) else 'double'
                    elif e[0] == 'str':
                        locals_[name] = 'char*'
                    else:
                        locals_[name] = 'long'
            elif st[0] == 'return':
                e = st[1]
                if isinstance(e, tuple):
                    if e[0] == 'var' and e[1] in locals_:
                        rtype = locals_[e[1]]
                    elif e[0] == 'call' and e[1] in self.structs:
                        rtype = e[1]
                    elif e[0] == 'call' and e[1] in self.func_returns:
                        rtype = self.func_returns[e[1]]
                    elif e[0] == 'num':
                        rtype = 'long' if isinstance(e[1], int) else 'double'
                    elif e[0] == 'str':
                        rtype = 'char*'
                    else:
                        rtype = 'long'
        return rtype

    def infer_param_types(self, params, body):
        """Suy param types từ cách dùng trong body."""
        types = {p: 'long' for p in params}
        def scan(node):
            if not isinstance(node, tuple): return
            if node[0] == 'dot':
                obj = node[1]; field = node[2]
                if isinstance(obj, tuple) and obj[0] == 'var':
                    pname = obj[1]
                    if pname in types:
                        for sname, sfields in self.structs.items():
                            if field in sfields:
                                types[pname] = sname
                                break
            for x in node[1:]:
                if isinstance(x, tuple): scan(x)
                elif isinstance(x, list):
                    for y in x:
                        if isinstance(y, (tuple, list)): scan(y)
        for st in body:
            scan(st)
        return types

    def gen_func'''
c = c.replace("    def gen_func", infer_funcs, 1)

# 3. Sửa gen_func dùng infer
old_genfunc = re.search(r'    def gen_func\(self, name, params, body\):.*?(?=\n    def gen\(self, ast\):)', c, re.DOTALL)
if old_genfunc:
    new_genfunc = '''    def gen_func(self, name, params, body):
        rtype = self.func_returns.get(name, 'void')
        ptypes = self.infer_param_types(params, body)
        param_str = ', '.join(f'{ptypes[p]} {p}' for p in params)
        lines = []
        self.indent = 1
        for st in body:
            self.stmt(st, lines)
        self.indent = 0
        sig = f'{rtype} {name}({param_str}) {{\\n'
        sig += '\\n'.join(lines)
        sig += '\\n}'
        self.functions.append(sig)

'''
    c = c[:old_genfunc.start()] + new_genfunc + c[old_genfunc.end():]
    print('  ✓ Thay gen_func')

# 4. Sửa gen() — 2-pass
old_gen = re.search(r'    def gen\(self, ast\):.*?(?=\n\ndef transpile)', c, re.DOTALL)
if old_gen:
    new_gen = '''    def gen(self, ast):
        # ═══ PASS 1: scan structs ═══
        for s in ast:
            if s[0] == 'struct':
                self.structs[s[1]] = s[2]

        # ═══ PASS 2: infer return types ═══
        for s in ast:
            if s[0] == 'func':
                name = s[1]; body = s[3]
                self.func_returns[name] = self.infer_return_type(body)

        # ═══ PASS 3: generate ═══
        body = []
        for s in ast:
            self.stmt(s, body)

        header = '#include <stdint.h>\\n'
        header += '#include <stdio.h>\\n'
        header += '#include <stdlib.h>\\n'
        header += '#include "catpp_rt.h"\\n\\n'

        out = []
        out.append('int main(void) {')
        for line in body:
            out.append('    ' + line)
        out.append('    return 0;')
        out.append('}')

        decls = '\\n'.join(self.declarations)
        funcs = '\\n\\n'.join(self.functions)
        return header + decls + '\\n\\n' + funcs + '\\n\\n' + '\\n'.join(out) + '\\n'

'''
    c = c[:old_gen.start()] + new_gen + c[old_gen.end():]
    print('  ✓ Thay gen() — 2 pass')

# 5. Sửa stmt 'let' — infer type từ function call
old_let = """        if t == 'let':
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
            self.vars[name] = ctype"""

new_let = """        if t == 'let':
            name = s[1]
            e = s[2]
            # Struct constructor?
            if isinstance(e, tuple) and e[0] == 'call' and e[1] in self.structs:
                args = ', '.join(self.expr(a) for a in e[2])
                ctype = e[1]
                out.append(f'{self.ind()}{ctype} {name} = {{{args}}};')
                self.vars[name] = ctype
                return
            # Function call → dùng return type
            if isinstance(e, tuple) and e[0] == 'call' and e[1] in self.func_returns:
                rtype = self.func_returns[e[1]]
                if rtype != 'void':
                    val = self.expr(e)
                    out.append(f'{self.ind()}{rtype} {name} = {val};')
                    self.vars[name] = rtype
                    return
            val = self.expr(e)
            if isinstance(e, tuple) and e[0] == 'num':
                ctype = 'long' if isinstance(e[1], int) else 'double'
            elif isinstance(e, tuple) and e[0] == 'str':
                ctype = 'char*'
            elif isinstance(e, tuple) and e[0] == 'bool':
                ctype = 'int'
            elif isinstance(e, tuple) and e[0] == 'cast':
                ctype = self.c_type(e[1])
            elif isinstance(e, tuple) and e[0] == 'var' and e[1] in self.vars:
                ctype = self.vars[e[1]]
            else:
                ctype = 'long'
            out.append(f'{self.ind()}{ctype} {name} = {val};')
            self.vars[name] = ctype"""

if old_let in c:
    c = c.replace(old_let, new_let, 1)
    print('  ✓ Sửa let — infer từ function return + var')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('✓ Đã ghi transpiler')
