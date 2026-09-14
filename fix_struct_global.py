#!/usr/bin/env python3
"""Fix: struct/enum phải ở global scope, trước functions."""
import os

path = 'tools/transpiler.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

# Thêm list declarations (global)
if 'self.declarations = []' not in c:
    c = c.replace(
        "        self.structs = {}  # name → [fields]",
        "        self.structs = {}  # name → [fields]\n        self.declarations = []  # global typedef/enum/struct",
        1
    )
    print('  ✓ Thêm declarations list')

# Struct/enum → push vào declarations, không vào body
c = c.replace(
    """        elif t == 'struct':
            name = s[1]; fields = s[2]
            self.structs[name] = fields
            out.append(f'typedef struct {name} {{')
            for f in fields:
                out.append(f'    long {f};')
            out.append(f'}} {name};')""",
    """        elif t == 'struct':
            name = s[1]; fields = s[2]
            self.structs[name] = fields
            decl = []
            decl.append(f'typedef struct {name} {{')
            for f in fields:
                decl.append(f'    long {f};')
            decl.append(f'}} {name};')
            self.declarations.extend(decl)""",
    1
)
print('  ✓ Struct → declarations')

c = c.replace(
    """        elif t == 'enum':
            name = s[1]; members = s[2]
            out.append(f'enum {name} {{')
            out.append('    ' + ', '.join(members))
            out.append(f'}};')""",
    """        elif t == 'enum':
            name = s[1]; members = s[2]
            decl = []
            decl.append(f'enum {name} {{')
            decl.append('    ' + ', '.join(members))
            decl.append(f'}};')
            self.declarations.extend(decl)""",
    1
)
print('  ✓ Enum → declarations')

# Gen: chèn declarations trước functions
c = c.replace(
    """        # Functions trước main
        funcs = '\\n\\n'.join(self.functions)
        return header + funcs + '\\n\\n' + '\\n'.join(out) + '\\n'""",
    """        # Order: header → declarations → functions → main
        decls = '\\n'.join(self.declarations)
        funcs = '\\n\\n'.join(self.functions)
        return header + decls + '\\n\\n' + funcs + '\\n\\n' + '\\n'.join(out) + '\\n'""",
    1
)
print('  ✓ Gen: declarations trước functions')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('✓ Đã ghi transpiler')
