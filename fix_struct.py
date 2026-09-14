#!/usr/bin/env python3
"""Fix transpiler: struct + dot access + các fix nhỏ."""
import os, sys, re

path = 'tools/transpiler.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

# 1. Track structs
if 'self.structs = {}' not in c:
    c = c.replace(
        "        self.vars = {}  # name → type",
        "        self.vars = {}  # name → type\n        self.structs = {}  # name → [fields]",
        1
    )
    print('  ✓ Track structs')

# 2. Trong stmt struct, lưu tên
c = c.replace(
    """        elif t == 'struct':
            name = s[1]; fields = s[2]
            out.append(f'typedef struct {name} {{')
            for f in fields:
                out.append(f'    long {f};')
            out.append(f'}} {name};')""",
    """        elif t == 'struct':
            name = s[1]; fields = s[2]
            self.structs[name] = fields
            out.append(f'typedef struct {name} {{')
            for f in fields:
                out.append(f'    long {f};')
            out.append(f'}} {name};')""",
    1
)
print('  ✓ Lưu struct vào dict')

# 3. Fix let — nếu value là call tới struct → dùng {args}
c = c.replace(
    """        if t == 'let':
            name = s[1]
            e = s[2]
            val = self.expr(e)""",
    """        if t == 'let':
            name = s[1]
            e = s[2]
            # Struct constructor?
            if isinstance(e, tuple) and e[0] == 'call' and e[1] in self.structs:
                args = ', '.join(self.expr(a) for a in e[2])
                ctype = e[1]
                out.append(f'{self.ind()}{ctype} {name} = {{{args}}};')
                self.vars[name] = ctype
                return
            val = self.expr(e)""",
    1
)
print('  ✓ Fix struct constructor')

# 4. Thêm dot access trong expr
c = c.replace(
    """        if t == 'index':
            return f'{self.expr(e[1])}[{self.expr(e[2])}]'""",
    """        if t == 'index':
            return f'{self.expr(e[1])}[{self.expr(e[2])}]'
        if t == 'dot':
            return f'{self.expr(e[1])}.{e[2]}'""",
    1
)
print('  ✓ Thêm dot access')

# 5. cast: cast(ptr, x) → void* nhưng cast(ptr, 0xB8000) cần thành (volatile uint16_t*)
# Giữ đơn giản — cast(ptr, ...) → (void*)
c = c.replace(
    "'ptr':'void*',",
    "'ptr':'void*','pointer':'void*',",
    1
)
print('  ✓ Fix pointer type')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('✓ Đã ghi tools/transpiler.py')
