"""Cat++ v3 → LLVM IR codegen."""
import llvmlite.ir as ir
import llvmlite.binding as llvm
import ctypes, sys
from parser_v3 import parse, ParseError

# ═══ Initialize LLVM targets (required for JIT + native codegen) ═══
try:
    llvm.initialize()
except RuntimeError:
    pass  # Newer llvmlite auto-initializes
try:
    llvm.initialize_native_target()
except RuntimeError:
    pass
try:
    llvm.initialize_native_asmprinter()
except RuntimeError:
    pass
try:
    llvm.initialize_native_asmparser()
except RuntimeError:
    pass

class CodegenError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line


class LLVMCodegen:
    def __init__(self):
        self.module = ir.Module(name='catpp')
        self.builder = None
        self.env = {}  # name → (alloca, ir_type)
        self.funcs = {}

        self.classes = {}
        self.i32 = ir.IntType(32)
        self.i64 = ir.IntType(64)
        self.f64 = ir.DoubleType()
        self.i8 = ir.IntType(8)
        self.i8ptr = ir.PointerType(self.i8)
        self.str_count = 0
        self._class_types = {}
        self.lines = []
        self.indent = 0
        self._current_class = None
        self._loop_end_stack = []
        self._loop_cond_stack = []
        self._var_classes = {}
        self._enum_names = set()
        self._enum_values = {}

    def _get_all_fields(self, cls_name):
        if cls_name not in self.classes:
            return []
        result = []
        chain = []
        p = self.classes[cls_name]['parent']
        while p and p in self.classes:
            chain.append(p)
            p = self.classes[p]['parent']
        for anc in reversed(chain):
            for _, fname in self.classes[anc]['fields']:
                result.append(fname)
        for _, fname in self.classes[cls_name]['fields']:
            result.append(fname)
        return result

    def _infer_obj_class(self, expr):
        if expr[0] == 'me':
            return self._current_class
        if expr[0] == 'var':
            name = expr[1]
            # Check var_classes mapping first (set in var_decl)
            if hasattr(self, '_var_classes') and name in self._var_classes:
                return self._var_classes[name]
            if name in self.env:
                alloca, ir_ty = self.env[name]
                # Check struct type or pointer-to-struct
                for cname, cty in self._class_types.items():
                    if ir_ty is cty:
                        return cname
                    if isinstance(ir_ty, ir.PointerType) and ir_ty.pointee is cty:
                        return cname
        return None

    def _find_method(self, cls_name, method_name):
        """Find method in class or parent chain. Return (class_name, func) or (None, None)."""
        c = cls_name
        while c:
            fn_name = f'{c}__{method_name}'
            for f in self.module.functions:
                if f.name == fn_name:
                    return (c, f)
            # Look up parent
            if c in self.classes:
                c = self.classes[c]['parent']
            else:
                break
        return (None, None)

    def _size_of(self, ir_ty):
        """Get size of LLVM type in bytes (approximate)."""
        if isinstance(ir_ty, ir.IntType):
            return ir.Constant(self.i64, max(1, ir_ty.width // 8))
        if isinstance(ir_ty, ir.DoubleType):
            return ir.Constant(self.i64, 8)
        if isinstance(ir_ty, ir.PointerType):
            return ir.Constant(self.i64, 8)
        if isinstance(ir_ty, ir.LiteralStructType):
            total = 0
            for el in ir_ty.elements:
                if isinstance(el, ir.IntType): total += max(1, el.width // 8)
                elif isinstance(el, ir.DoubleType): total += 8
                elif isinstance(el, ir.PointerType): total += 8
                else: total += 8
            return ir.Constant(self.i64, total)
        return ir.Constant(self.i64, 8)

    def emit(self, line=''):
        self.lines.append('  ' * self.indent + line)

    def c_type(self, vtype):
        base, ptr_depth, array_size, generic = vtype
        # Class type
        if base in self.classes and base in self._class_types:
            base_t = self._class_types[base]
        elif base.startswith('ptr_') and base[4:] in self._class_types:
            base_t = ir.PointerType(self._class_types[base[4:]])
            # Already pointer; don't apply ptr_depth twice
            return base_t
        elif base in ('int', 'bool'):
            base_t = self.i32
        elif base in ('long',):
            base_t = self.i64
        elif base in ('float', 'double'):
            base_t = self.f64
        elif base == 'char':
            base_t = self.i8
        elif base == 'void':
            base_t = ir.VoidType()
        elif base == 'str':
            base_t = self.i8ptr
        else:
            base_t = self.i32
        # Array -> pointer to elem
        if array_size is not None:
            return ir.PointerType(base_t)
        for _ in range(ptr_depth):
            base_t = ir.PointerType(base_t)
        return base_t

    def compile(self, ast):
        # Pass 0: collect classes and functions
        self._collect(ast[1])

        # Pass 0.5: emit structs and enums as C typedefs
        for stmt in ast[1]:
            if stmt[0] == 'struct':
                _, name, fields = stmt
                all_fields = list(fields)
                struct_ty = ir.LiteralStructType([self._basic_type(ft) for ft, _ in all_fields])
                self._class_types[name] = struct_ty
                # Register as class for field access
                self.classes[name] = {'parent': None, 'fields': fields, 'methods': {}}
                self.emit(f'struct {name} {{')
                self.indent += 1
                for ft, fn in all_fields:
                    self.emit(f'{self._basic_c_type(ft)} {fn};')
                if not all_fields:
                    self.emit('int _dummy;')
                self.indent -= 1
                self.emit('};')
                self.emit('')
            elif stmt[0] == 'enum':
                _, name, members = stmt
                self.emit(f'enum {name} {{')
                self.indent += 1
                for i, m in enumerate(members):
                    self.emit(f'{name}_{m} = {i},')
                self.indent -= 1
                self.emit('};')
                self.emit('')
                self._enum_names.add(name)
                for i, m in enumerate(members):
                    self._enum_values[f'{name}_{m}'] = i

        # Pass 1: emit class structs
        for stmt in ast[1]:
            if stmt[0] == 'class':
                self._emit_class(stmt)

        # Pass 2: declare function signatures
        for stmt in ast[1]:
            if stmt[0] == 'func':
                self._declare_func(stmt)

        # Pass 3: emit method functions (as ClassName__method(me, ...))
        for stmt in ast[1]:
            if stmt[0] == 'class':
                self._emit_class_methods(stmt)

        # Pass 4: emit function bodies
        for stmt in ast[1]:
            if stmt[0] == 'func':
                self._emit_func(stmt)

        return str(self.module)

    def _collect(self, stmts):
        for s in stmts:
            if s[0] == 'func':
                _, ret_type, name, params, body = s
                self.funcs[name] = (ret_type, params)
            elif s[0] == 'class':
                _, name, parent, members = s
                fields = []
                methods = {}
                for m in members:
                    if m[0] == 'field':
                        fields.append((m[1], m[2]))
                    elif m[0] == 'func':
                        methods[m[2]] = m
                self.classes[name] = {'parent': parent, 'fields': fields, 'methods': methods}

    def _emit_class(self, stmt):
        _, name, parent, members = stmt
        cdata = self.classes[name]
        # Collect all fields including parents
        all_fields = []
        chain = []
        p = cdata['parent']
        while p and p in self.classes:
            chain.append(p)
            p = self.classes[p]['parent']
        for anc in reversed(chain):
            for ftype, fname in self.classes[anc]['fields']:
                all_fields.append((ftype, fname))
        for ftype, fname in cdata['fields']:
            all_fields.append((ftype, fname))

        # Create struct type
        struct_ty = ir.LiteralStructType([self._basic_type(ft) for ft, _ in all_fields])
        self._class_types[name] = struct_ty

        # Emit C struct
        self.emit(f'struct {name} {{')
        self.indent += 1
        for ftype, fname in all_fields:
            self.emit(f'{self._basic_c_type(ftype)} {fname};')
        if not all_fields:
            self.emit('int _dummy;')
        self.indent -= 1
        self.emit(f'}};')
        self.emit('')

    def _basic_type(self, vtype):
        """Get LLVM type for basic type (no pointers)."""
        base = vtype[0]
        if base == 'void': return ir.VoidType()
        if base == 'int': return self.i32
        if base == 'bool': return self.i32
        if base == 'long': return self.i64
        if base in ('float', 'double'): return self.f64
        if base == 'char': return self.i8
        if base == 'str': return self.i8ptr
        return self.i32

    def _basic_c_type(self, vtype):
        """Get C type string."""
        base = vtype[0]
        if base in ('int', 'bool'): return 'int'
        if base == 'long': return 'long long'
        if base in ('float', 'double'): return 'double'
        if base == 'char': return 'char'
        if base == 'str': return 'char*'
        return 'int'

    def _emit_class_methods(self, stmt):
        _, cname, parent, members = stmt
        cdata = self.classes[cname]
        struct_ty = self._class_types[cname]
        me_ptr_ty = ir.PointerType(struct_ty)

        for mname, m in cdata['methods'].items():
            _, mret, _, mparams, mbody = m
            # C-style method: ret ClassName__method(ClassName* me, params...)
            fn_name = f'{cname}__{mname}'
            param_types = [me_ptr_ty] + [self._basic_type(pt) for pt, _ in mparams]
            ret_ty = self._basic_type(mret)
            fn_ty = ir.FunctionType(ret_ty, param_types)
            fn = ir.Function(self.module, fn_ty, name=fn_name)
            fn.args[0].name = 'me'
            for i, (_, pname) in enumerate(mparams):
                fn.args[i+1].name = pname

            # Body
            entry = fn.append_basic_block(name='entry')
            self.builder = ir.IRBuilder(entry)
            self.env = {}
            self._current_class = cname

            # Alloc params
            for i, ((ptype, pname), arg) in enumerate(zip([('ptr_me', 'me')] + mparams, fn.args)):
                alloca = self.builder.alloca(arg.type, name=pname)
                self.builder.store(arg, alloca)
                self.env[pname] = (alloca, arg.type)

            for st in mbody:
                self._emit_stmt(st)

            if not self.builder.block.is_terminated:
                if mret[0] == 'void':
                    self.builder.ret_void()
                else:
                    self.builder.ret(ir.Constant(ret_ty, 0))

    def _declare_func(self, s):
        _, ret_type, name, params, body = s
        param_types = [self.c_type(p[0]) for p in params]
        fn_ty = ir.FunctionType(self.c_type(ret_type), param_types)
        fn = ir.Function(self.module, fn_ty, name=name)
        # Name args
        for i, (ptype, pname) in enumerate(params):
            fn.args[i].name = pname
        self.funcs[name] = fn

    def _emit_func(self, s):
        _, ret_type, name, params, body = s
        fn = self.funcs[name]
        entry = fn.append_basic_block(name='entry')
        self.builder = ir.IRBuilder(entry)
        self.env = {}

        # Alloc params
        for i, (ptype, pname) in enumerate(params):
            ctype = self.c_type(ptype)
            alloca = self.builder.alloca(ctype, name=pname)
            self.builder.store(fn.args[i], alloca)
            self.env[pname] = (alloca, ctype)

        # Emit body
        last_value = None
        for stmt in body:
            last_value = self._emit_stmt(stmt)

        # Auto return
        if not self.builder.block.is_terminated:
            if ret_type[0] == 'void':
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(self.c_type(ret_type), 0))

    def _emit_stmt(self, s):
        t = s[0]

        if t == 'var_decl':
            _, vtype, name, init = s
            base = vtype[0]
            ptr_depth = vtype[1]
            array_size = vtype[2]
            # Pointer type: paw int* p = &x
            if ptr_depth > 0:
                ctype = self.c_type(vtype)
                alloca = self.builder.alloca(ctype, name=name)
                self.env[name] = (alloca, ctype)
                # Record class if pointer to class
                if base in self.classes:
                    self._var_classes[name] = base
                if init is not None:
                    val = self._emit_expr(init)
                    if val.type != ctype:
                        if isinstance(val.type, ir.PointerType) and isinstance(ctype, ir.PointerType):
                            val = self.builder.bitcast(val, ctype)
                    self.builder.store(val, alloca)
                return None
            # Array type: paw int arr[5]
            if array_size is not None:
                # array_size may be ('num', 5) or int
                if isinstance(array_size, tuple) and array_size[0] == 'num':
                    size_n = int(array_size[1])
                else:
                    size_n = int(array_size)
                elem_ty = self._basic_type((base, 0, None, None))
                arr_ty = ir.ArrayType(elem_ty, size_n)
                alloca = self.builder.alloca(arr_ty, name=name)
                self.env[name] = (alloca, arr_ty)
                return None
            # Class type
            if base in self.classes and base in self._class_types:
                struct_ty = self._class_types[base]
                alloca = self.builder.alloca(struct_ty, name=name)
                self.env[name] = (alloca, struct_ty)
                self._var_classes[name] = base
                if init is not None and init[0] == 'call' and init[1][0] == 'var' and init[1][1] == base:
                    args = [self._emit_expr(a) for a in init[2]]
                    fn_name = base + '__' + base
                    for f in self.module.functions:
                        if f.name == fn_name:
                            self.builder.call(f, [alloca] + args)
                            break
                return None
            ctype = self.c_type(vtype)
            alloca = self.builder.alloca(ctype, name=name)
            if init is not None:
                val = self._emit_expr(init)
                self.builder.store(val, alloca)
            self.env[name] = (alloca, ctype)
            return None

        if t == 'meow':
            val = self._emit_expr(s[1])
            # Detect type
            if isinstance(val.type, ir.PointerType) and val.type.pointee == self.i8:
                puts = self._get_or_declare_puts()
                self.builder.call(puts, [val])
            elif isinstance(val.type, ir.DoubleType):
                printf = self._get_or_declare_printf()
                fmt = self._global_string('%g\n\0', name='.fmt_d')
                self.builder.call(printf, [fmt, val])
            else:
                printf = self._get_or_declare_printf()
                fmt = self._global_string('%d\n\0', name='.fmt_i')
                if isinstance(val.type, ir.IntType):
                    if val.type.width > 32:
                        val = self.builder.trunc(val, self.i32)
                    elif val.type.width < 32:
                        val = self.builder.sext(val, self.i32)
                self.builder.call(printf, [fmt, val])
            return None

        if t == 'return':
            if s[1] is None:
                self.builder.ret_void()
            else:
                val = self._emit_expr(s[1])
                # Match return type
                ret_ty = self.builder.function.function_type.return_type
                if isinstance(ret_ty, ir.IntType) and isinstance(val.type, ir.IntType):
                    if val.type.width != ret_ty.width:
                        if val.type.width < ret_ty.width:
                            val = self.builder.sext(val, ret_ty)
                        else:
                            val = self.builder.trunc(val, ret_ty)
                self.builder.ret(val)
            return None

        if t == 'if':
            _, cond, then, els = s
            cond_val = self._to_i1(self._emit_expr(cond))
            then_bb = self.builder.function.append_basic_block(name='then')
            merge_bb = self.builder.function.append_basic_block(name='merge')
            if els:
                else_bb = self.builder.function.append_basic_block(name='else')
                self.builder.cbranch(cond_val, then_bb, else_bb)
            else:
                self.builder.cbranch(cond_val, then_bb, merge_bb)

            # Then
            self.builder.position_at_end(then_bb)
            for st in then: self._emit_stmt(st)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

            # Else
            if els:
                self.builder.position_at_end(else_bb)
                for st in els: self._emit_stmt(st)
                if not self.builder.block.is_terminated:
                    self.builder.branch(merge_bb)

            self.builder.position_at_end(merge_bb)
            return None

        if t == 'for':
            _, init, cond, step, body = s
            # Emit init
            self._emit_stmt(init)
            # Loop blocks
            cond_bb = self.builder.function.append_basic_block(name='for.cond')
            body_bb = self.builder.function.append_basic_block(name='for.body')
            step_bb = self.builder.function.append_basic_block(name='for.step')
            end_bb = self.builder.function.append_basic_block(name='for.end')
            self.builder.branch(cond_bb)
            # Cond
            self.builder.position_at_end(cond_bb)
            c_val = self._to_i1(self._emit_expr(cond))
            self.builder.cbranch(c_val, body_bb, end_bb)
            # Body
            self.builder.position_at_end(body_bb)
            self._loop_end_stack.append(end_bb)
            self._loop_cond_stack.append(step_bb)
            for st in body:
                self._emit_stmt(st)
            self._loop_end_stack.pop()
            self._loop_cond_stack.pop()
            if not self.builder.block.is_terminated:
                self.builder.branch(step_bb)
            # Step
            self.builder.position_at_end(step_bb)
            self._emit_expr(step)
            self.builder.branch(cond_bb)
            # End
            self.builder.position_at_end(end_bb)
            return None

        if t == 'while':
            _, cond, body = s
            cond_bb = self.builder.function.append_basic_block(name='while.cond')
            body_bb = self.builder.function.append_basic_block(name='while.body')
            end_bb = self.builder.function.append_basic_block(name='while.end')
            self.builder.branch(cond_bb)

            self.builder.position_at_end(cond_bb)
            cond_val = self._to_i1(self._emit_expr(cond))
            self.builder.cbranch(cond_val, body_bb, end_bb)

            self.builder.position_at_end(body_bb)
            self._loop_end_stack.append(end_bb)
            self._loop_cond_stack.append(cond_bb)
            for st in body: self._emit_stmt(st)
            self._loop_end_stack.pop()
            self._loop_cond_stack.pop()
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(end_bb)
            return None

        if t == 'expr_stmt':
            self._emit_expr(s[1])
            return None

        if t == 'delete':
            ptr = self._emit_expr(s[1])
            free = self._get_or_declare('free', ir.VoidType(), [self.i8ptr])
            if isinstance(ptr.type, ir.PointerType):
                raw = self.builder.bitcast(ptr, self.i8ptr)
                self.builder.call(free, [raw])
            return None

        if t == 'break':
            if hasattr(self, '_loop_end_stack') and self._loop_end_stack:
                self.builder.branch(self._loop_end_stack[-1])
                # Move to dead block so following code isn't emitted in this block
                dead = self.builder.function.append_basic_block(name='break.dead')
                self.builder.position_at_end(dead)
            return None

        if t == 'continue':
            if hasattr(self, '_loop_cond_stack') and self._loop_cond_stack:
                self.builder.branch(self._loop_cond_stack[-1])
                dead = self.builder.function.append_basic_block(name='cont.dead')
                self.builder.position_at_end(dead)
            return None

        raise CodegenError(f'Unknown stmt: {t}')

    def _emit_expr(self, e):
        t = e[0]

        if t == 'num':
            v = e[1]
            if isinstance(v, float):
                return ir.Constant(self.f64, v)
            return ir.Constant(self.i32, int(v))

        if t == 'bool':
            return ir.Constant(self.i32, 1 if e[1] else 0)

        if t == 'sizeof_type':
            tn = e[1]
            # Map C types to sizes
            sizes = {'int': 4, 'float': 8, 'double': 8, 'bool': 1, 'char': 1,
                     'long': 8, 'short': 2, 'str': 8, 'void': 1}
            sz = sizes.get(tn, 8)
            if tn in self.classes:
                # struct size
                if tn in self._class_types:
                    struct_ty = self._class_types[tn]
                    if isinstance(struct_ty, ir.LiteralStructType):
                        sz = sum(
                            4 if isinstance(el, ir.IntType) and el.width == 32 else
                            8 if isinstance(el, (ir.IntType, ir.DoubleType, ir.PointerType)) else
                            1 if isinstance(el, ir.IntType) else 8
                            for el in struct_ty.elements
                        )
            return ir.Constant(self.i32, sz)

        if t == 'sizeof':
            # sizeof expression — approximate
            val = self._emit_expr(e[1])
            if isinstance(val.type, ir.IntType):
                return ir.Constant(self.i32, max(1, val.type.width // 8))
            if isinstance(val.type, ir.DoubleType):
                return ir.Constant(self.i32, 8)
            if isinstance(val.type, ir.PointerType):
                return ir.Constant(self.i32, 8)
            return ir.Constant(self.i32, 8)

        if t == 'address_of':
            inner = e[1]
            if inner[0] == 'var':
                name = inner[1]
                if name in self.env:
                    alloca, _ = self.env[name]
                    return alloca
                raise CodegenError(f'&: undefined {name}')
            if inner[0] == 'index':
                obj_expr = inner[1]
                idx_expr = inner[2]
                if obj_expr[0] == 'var':
                    alloca, ty = self.env[obj_expr[1]]
                    if isinstance(ty, ir.ArrayType):
                        obj_ptr = self.builder.gep(alloca, [ir.Constant(self.i32, 0), ir.Constant(self.i32, 0)], inbounds=True)
                    else:
                        obj_ptr = alloca
                else:
                    obj_ptr = self._emit_expr(obj_expr)
                idx = self._emit_expr(idx_expr)
                if isinstance(idx.type, ir.IntType) and idx.type.width != 64:
                    idx = self.builder.sext(idx, self.i64) if idx.type.width < 64 else self.builder.trunc(idx, self.i64)
                return self.builder.gep(obj_ptr, [idx], inbounds=True)
            if inner[0] == 'member':
                # &obj.field
                cls_name = self._infer_obj_class(inner[1])
                if inner[1][0] == 'var':
                    obj_ptr = self.env[inner[1][1]][0]
                elif inner[1][0] == 'me':
                    alloca, _ = self.env['me']
                    obj_ptr = self.builder.load(alloca, name='me')
                else:
                    obj_ptr = self._emit_expr(inner[1])
                all_fields = self._get_all_fields(cls_name)
                field_name = inner[2]
                idx = all_fields.index(field_name)
                return self.builder.gep(obj_ptr, [ir.Constant(self.i32, 0), ir.Constant(self.i32, idx)], inbounds=True)
            raise CodegenError('& only on var/index/member')

        if t == 'deref':
            ptr = self._emit_expr(e[1])
            if not isinstance(ptr.type, ir.PointerType):
                raise CodegenError(f'*: expected pointer, got {ptr.type}')
            return self.builder.load(ptr, name='deref')

        if t == 'str':
            s = e[1]
            if not s.endswith('\0'):
                s += '\0'
            return self._global_string(s, name='.str')

        if t == 'array':
            # [1, 2, 3] -> create global array or alloca
            items = [self._emit_expr(x) for x in e[1]]
            n = len(items)
            if n == 0:
                return ir.Constant(ir.ArrayType(self.i32, 0), [])
            elem_ty = items[0].type
            arr_ty = ir.ArrayType(elem_ty, n)
            alloca = self.builder.alloca(arr_ty, name='.arr')
            for i, item in enumerate(items):
                ptr = self.builder.gep(alloca, [ir.Constant(self.i32, 0), ir.Constant(self.i32, i)], inbounds=True)
                self.builder.store(item, ptr)
            # Return pointer to first element
            return self.builder.gep(alloca, [ir.Constant(self.i32, 0), ir.Constant(self.i32, 0)], inbounds=True)

        if t == 'index':
            obj_expr = e[1]
            idx_expr = e[2]
            # Get array pointer
            if obj_expr[0] == 'var':
                name = obj_expr[1]
                if name in self.env:
                    alloca, ty = self.env[name]
                    if isinstance(ty, ir.ArrayType):
                        obj_ptr = self.builder.gep(alloca, [ir.Constant(self.i32, 0), ir.Constant(self.i32, 0)], inbounds=True)
                    else:
                        obj_ptr = alloca
                else:
                    obj_ptr = self._emit_expr(obj_expr)
            else:
                obj_ptr = self._emit_expr(obj_expr)
            idx = self._emit_expr(idx_expr)
            if isinstance(idx.type, ir.IntType) and idx.type.width != 64:
                idx = self.builder.sext(idx, self.i64) if idx.type.width < 64 else self.builder.trunc(idx, self.i64)
            ptr = self.builder.gep(obj_ptr, [idx], inbounds=True)
            return self.builder.load(ptr, name='elem')

        if t == 'char':
            return ir.Constant(self.i8, ord(e[1]) if e[1] else 0)

        if t == 'null':
            return ir.Constant(self.i8ptr, None)

        if t == 'new':
            _, typename, args_expr = e
            base = typename[0]
            if base in self.classes and base in self._class_types:
                struct_ty = self._class_types[base]
                # malloc(sizeof(Struct))
                size = self._size_of(struct_ty)
                malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
                raw = self.builder.call(malloc, [size])
                ptr = self.builder.bitcast(raw, ir.PointerType(struct_ty))
                # Call constructor if args
                if args_expr:
                    args = [self._emit_expr(a) for a in args_expr]
                    fn_name = base + '__' + base
                    for f in self.module.functions:
                        if f.name == fn_name:
                            self.builder.call(f, [ptr] + args)
                            break
                return ptr
            raise CodegenError(f'new: unknown class {base}')

        if t == 'me':
            if 'me' not in self.env:
                raise CodegenError('me not in scope')
            alloca, ctype = self.env['me']
            return self.builder.load(alloca, name='me')

        if t == 'var':
            name = e[1]
            # Enum value
            if name in self._enum_values:
                return ir.Constant(self.i32, self._enum_values[name])
            if name not in self.env:
                raise CodegenError(f'Undefined: {name}')
            alloca, ctype = self.env[name]
            return self.builder.load(alloca, name=name)

        if t == 'binop':
            op, a, b = e[1], self._emit_expr(e[2]), self._emit_expr(e[3])
            # String concat
            if op == '+' and isinstance(a.type, ir.PointerType) and a.type.pointee == self.i8:
                return self._str_concat(a, b)
            if op == '+' and isinstance(b.type, ir.PointerType) and b.type.pointee == self.i8:
                return self._str_concat(a, b)
            if op == '==':
                # String compare
                if isinstance(a.type, ir.PointerType) and isinstance(b.type, ir.PointerType):
                    return self._str_cmp(a, b)
            if op == '!=':
                if isinstance(a.type, ir.PointerType) and isinstance(b.type, ir.PointerType):
                    cmp_i1 = self._str_cmp(a, b)
                    # Extend i1 -> i32 truoc khi xor
                    cmp_i32 = self.builder.zext(cmp_i1, self.i32)
                    return self.builder.xor(cmp_i32, ir.Constant(self.i32, 1))
            if op == '+':
                if isinstance(a.type, ir.DoubleType) or isinstance(b.type, ir.DoubleType):
                    # Promote int -> double
                    if isinstance(a.type, ir.IntType):
                        a = self.builder.sitofp(a, self.f64)
                    if isinstance(b.type, ir.IntType):
                        b = self.builder.sitofp(b, self.f64)
                    return self.builder.fadd(a, b)
                return self.builder.add(a, b)
            if op == '-':
                if isinstance(a.type, ir.DoubleType) or isinstance(b.type, ir.DoubleType):
                    return self.builder.fsub(a, b)
                return self.builder.sub(a, b)
            if op == '*':
                if isinstance(a.type, ir.DoubleType) or isinstance(b.type, ir.DoubleType):
                    return self.builder.fmul(a, b)
                return self.builder.mul(a, b)
            if op == '/':
                if isinstance(a.type, ir.DoubleType) or isinstance(b.type, ir.DoubleType):
                    return self.builder.fdiv(a, b)
                return self.builder.sdiv(a, b)
            if op == '%':
                return self.builder.srem(a, b)
            if op == '==':
                if isinstance(a.type, ir.DoubleType):
                    return self.builder.fcmp_ordered('==', a, b)
                return self.builder.icmp_signed('==', a, b)
            if op == '!=':
                if isinstance(a.type, ir.DoubleType):
                    return self.builder.fcmp_ordered('!=', a, b)
                return self.builder.icmp_signed('!=', a, b)
            if op == '<': return self.builder.icmp_signed('<', a, b)
            if op == '>': return self.builder.icmp_signed('>', a, b)
            if op == '<=': return self.builder.icmp_signed('<=', a, b)
            if op == '>=': return self.builder.icmp_signed('>=', a, b)
            if op == '&&':
                return self.builder.and_(a, b)
            if op == '||':
                return self.builder.or_(a, b)

        if t == 'unary':
            op = e[1]
            v = self._emit_expr(e[2])
            if op == '-':
                if isinstance(v.type, ir.DoubleType):
                    return self.builder.fsub(ir.Constant(self.f64, 0.0), v)
                return self.builder.sub(ir.Constant(self.i32, 0), v)
            if op == '!':
                return self.builder.icmp_signed('==', v, ir.Constant(self.i32, 0))

        if t == 'assign':
            op, target, value_expr = e[1], e[2], e[3]
            # Deref assign: *p = val
            if target[0] == 'deref':
                ptr = self._emit_expr(target[1])
                if not isinstance(ptr.type, ir.PointerType):
                    raise CodegenError(f'*: expected pointer')
                value = self._emit_expr(value_expr)
                if value.type != ptr.type.pointee:
                    if isinstance(value.type, ir.IntType) and isinstance(ptr.type.pointee, ir.IntType):
                        if value.type.width < ptr.type.pointee.width:
                            value = self.builder.sext(value, ptr.type.pointee)
                        elif value.type.width > ptr.type.pointee.width:
                            value = self.builder.trunc(value, ptr.type.pointee)
                self.builder.store(value, ptr)
                return value
            # Index assign: arr[i] = val
            if target[0] == 'index':
                obj_expr = target[1]
                idx_expr = target[2]
                if obj_expr[0] == 'var':
                    name = obj_expr[1]
                    alloca, ty = self.env[name]
                    if isinstance(ty, ir.ArrayType):
                        obj_ptr = self.builder.gep(alloca, [ir.Constant(self.i32, 0), ir.Constant(self.i32, 0)], inbounds=True)
                    else:
                        obj_ptr = alloca
                else:
                    obj_ptr = self._emit_expr(obj_expr)
                idx = self._emit_expr(idx_expr)
                if isinstance(idx.type, ir.IntType) and idx.type.width != 64:
                    idx = self.builder.sext(idx, self.i64) if idx.type.width < 64 else self.builder.trunc(idx, self.i64)
                ptr = self.builder.gep(obj_ptr, [idx], inbounds=True)
                value = self._emit_expr(value_expr)
                # Cast if needed
                if value.type != ptr.type.pointee:
                    if isinstance(value.type, ir.IntType) and isinstance(ptr.type.pointee, ir.IntType):
                        if value.type.width < ptr.type.pointee.width:
                            value = self.builder.sext(value, ptr.type.pointee)
                        elif value.type.width > ptr.type.pointee.width:
                            value = self.builder.trunc(value, ptr.type.pointee)
                self.builder.store(value, ptr)
                return value
            if target[0] == 'member':
                obj_expr = target[1]
                field_name = target[2]
                if obj_expr[0] == 'me':
                    cls_name = self._current_class
                    alloca, _ = self.env['me']
                    obj = self.builder.load(alloca, name='me')
                else:
                    cls_name = self._infer_obj_class(obj_expr)
                    if obj_expr[0] == 'var':
                        obj = self.env[obj_expr[1]][0]
                    else:
                        obj = self._emit_expr(obj_expr)
                if cls_name and cls_name in self._class_types:
                    all_fields = self._get_all_fields(cls_name)
                    if field_name in all_fields:
                        idx = all_fields.index(field_name)
                        ptr = self.builder.gep(obj, [ir.Constant(self.i32, 0), ir.Constant(self.i32, idx)], inbounds=True)
                        value = self._emit_expr(value_expr)
                        if value.type != ptr.type.pointee:
                            if isinstance(value.type, ir.IntType) and isinstance(ptr.type.pointee, ir.IntType):
                                if value.type.width < ptr.type.pointee.width:
                                    value = self.builder.sext(value, ptr.type.pointee)
                                elif value.type.width > ptr.type.pointee.width:
                                    value = self.builder.trunc(value, ptr.type.pointee)
                        self.builder.store(value, ptr)
                        return value
                raise CodegenError('Unknown field: ' + field_name)
            if target[0] != 'var':
                raise CodegenError('assign only to var')
            name = target[1]
            if name not in self.env:
                raise CodegenError(f'Undefined: {name}')
            alloca, ctype = self.env[name]
            value = self._emit_expr(value_expr)
            if op != '=':
                cur = self.builder.load(alloca)
                if op == 'ADD_EQ': value = self.builder.add(cur, value)
                elif op == 'SUB_EQ': value = self.builder.sub(cur, value)
                elif op == 'MUL_EQ': value = self.builder.mul(cur, value)
                elif op == 'DIV_EQ': value = self.builder.sdiv(cur, value)
            self.builder.store(value, alloca)
            return value

        if t == 'arrow':
            obj_expr = e[1]
            field_name = e[2]
            # Get the POINTER value (load from alloca if var, or use as-is if expr)
            if obj_expr[0] == 'var':
                alloca, ty = self.env[obj_expr[1]]
                if isinstance(ty, ir.PointerType):
                    # Load the pointer stored in alloca
                    obj_ptr = self.builder.load(alloca, name=obj_expr[1])
                else:
                    obj_ptr = alloca
            else:
                obj_ptr = self._emit_expr(obj_expr)
            cls_name = self._infer_obj_class(obj_expr)
            if cls_name:
                all_fields = self._get_all_fields(cls_name)
                if field_name in all_fields:
                    idx = all_fields.index(field_name)
                    ptr = self.builder.gep(obj_ptr, [ir.Constant(self.i32, 0), ir.Constant(self.i32, idx)], inbounds=True)
                    return self.builder.load(ptr, name=field_name)
            raise CodegenError(f'->: unknown field {field_name}')

        if t == 'member':
            obj_expr = e[1]
            field_name = e[2]
            # Enum access: Color.red -> Color_red (constant int)
            if obj_expr[0] == 'var' and obj_expr[1] in self._enum_names:
                enum_name = obj_expr[1]
                const_name = f'{enum_name}_{field_name}'
                if const_name in self._enum_values:
                    return ir.Constant(self.i32, self._enum_values[const_name])
                raise CodegenError(f'Unknown enum member: {const_name}')
            # Determine class
            if obj_expr[0] == 'me':
                cls_name = self._current_class
                alloca, _ = self.env['me']
                obj_ptr = self.builder.load(alloca, name='me')
            else:
                cls_name = self._infer_obj_class(obj_expr)
                if obj_expr[0] == 'var':
                    obj_ptr = self.env[obj_expr[1]][0]
                else:
                    obj_ptr = self._emit_expr(obj_expr)
            if cls_name and cls_name in self._class_types:
                all_fields = self._get_all_fields(cls_name)
                if field_name in all_fields:
                    idx = all_fields.index(field_name)
                    ptr = self.builder.gep(obj_ptr, [ir.Constant(self.i32, 0), ir.Constant(self.i32, idx)], inbounds=True)
                    return self.builder.load(ptr, name=field_name)
            raise CodegenError('Unknown member: ' + field_name)

        if t == 'call':
            fn_expr = e[1]
            args = [self._emit_expr(a) for a in e[2]]
            # Method call: p->sum()
            if fn_expr[0] == 'arrow':
                obj_expr = fn_expr[1]
                method_name = fn_expr[2]
                if obj_expr[0] == 'var':
                    alloca, ty = self.env[obj_expr[1]]
                    if isinstance(ty, ir.PointerType):
                        obj_ptr = self.builder.load(alloca, name=obj_expr[1])
                    else:
                        obj_ptr = alloca
                else:
                    obj_ptr = self._emit_expr(obj_expr)
                cls_name = self._infer_obj_class(obj_expr)
                if not cls_name:
                    raise CodegenError('arrow: unknown class')
                found_cls, fn = self._find_method(cls_name, method_name)
                if fn is None:
                    raise CodegenError(f'Unknown method: {method_name}')
                fn_me_ty = fn.function_type.args[0]
                if obj_ptr.type != fn_me_ty:
                    obj_ptr = self.builder.bitcast(obj_ptr, fn_me_ty)
                return self.builder.call(fn, [obj_ptr] + args)

            # Method call: p.sum() -> ClassName__sum(&p)
            if fn_expr[0] == 'member':
                obj_expr = fn_expr[1]
                method_name = fn_expr[2]
                cls_name = self._infer_obj_class(obj_expr)
                if not cls_name:
                    raise CodegenError('Unknown class for method: ' + method_name)
                # Pass POINTER to obj
                if obj_expr[0] == 'var':
                    alloca, _ = self.env[obj_expr[1]]
                    obj_ptr = alloca
                elif obj_expr[0] == 'me':
                    alloca, _ = self.env['me']
                    obj_ptr = self.builder.load(alloca, name='me')
                else:
                    obj_ptr = self._emit_expr(obj_expr)
                # Find method in class chain (inheritance)
                found_cls, fn = self._find_method(cls_name, method_name)
                if fn is None:
                    raise CodegenError(f'Unknown method: {method_name} in class {cls_name}')
                # Cast obj_ptr to correct type if method in parent
                fn_me_ty = fn.function_type.args[0]
                if obj_ptr.type != fn_me_ty:
                    obj_ptr = self.builder.bitcast(obj_ptr, fn_me_ty)
                return self.builder.call(fn, [obj_ptr] + args)
            if fn_expr[0] == 'var':
                name = fn_expr[1]
                if name in self.funcs:
                    return self.builder.call(self.funcs[name], args)
                # Builtins
                return self._emit_builtin(name, args, e[2])
            raise CodegenError(f'Unknown function: {fn_expr}')

        raise CodegenError(f'Unknown expr: {t}')

    def _global_string(self, s, name='.str'):
        """Create a global string constant, return pointer."""
        self.str_count += 1
        name = f'{name}.{self.str_count}'
        # Encode UTF-8
        b = s.encode('utf-8')
        str_const = ir.Constant(ir.ArrayType(self.i8, len(b)), bytearray(b))
        global_var = ir.GlobalVariable(self.module, str_const.type, name=name)
        global_var.linkage = 'private'
        global_var.global_constant = True
        global_var.initializer = str_const
        return self.builder.gep(global_var, [ir.Constant(self.i32, 0), ir.Constant(self.i32, 0)], inbounds=True)



    def _to_i1(self, val):
        """Convert value to i1 (bool) for branching."""
        if isinstance(val.type, ir.IntType) and val.type.width == 1:
            return val
        if isinstance(val.type, ir.IntType):
            return self.builder.icmp_signed('!=', val, ir.Constant(val.type, 0))
        if isinstance(val.type, ir.PointerType):
            return self.builder.icmp_signed('!=', val, ir.Constant(val.type, None))
        # Fallback
        return val

    def _str_concat(self, a, b):
        """Concat 2 strings using malloc + strcat."""
        # Ensure both are i8*
        if isinstance(a.type, ir.PointerType) and a.type.pointee != self.i8:
            a = self.builder.bitcast(a, self.i8ptr)
        if isinstance(b.type, ir.PointerType) and b.type.pointee != self.i8:
            b = self.builder.bitcast(b, self.i8ptr)
        # Get lengths
        strlen = self._get_or_declare('strlen', self.i64, [self.i8ptr])
        malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
        strcpy = self._get_or_declare('strcpy', self.i8ptr, [self.i8ptr, self.i8ptr])
        strcat = self._get_or_declare('strcat', self.i8ptr, [self.i8ptr, self.i8ptr])
        len_a = self.builder.call(strlen, [a])
        len_b = self.builder.call(strlen, [b])
        total = self.builder.add(self.builder.add(len_a, len_b), ir.Constant(self.i64, 1))
        buf = self.builder.call(malloc, [total])
        self.builder.call(strcpy, [buf, a])
        self.builder.call(strcat, [buf, b])
        return buf

    def _str_cmp(self, a, b):
        """strcmp(a, b) == 0"""
        strcmp = self._get_or_declare('strcmp', self.i32, [self.i8ptr, self.i8ptr])
        result = self.builder.call(strcmp, [a, b])
        return self.builder.icmp_signed('==', result, ir.Constant(self.i32, 0))

    def _emit_builtin(self, name, args, args_expr):
        """Emit LLVM IR for builtin function."""
        if name == 'strlen':
            fn = self._get_or_declare('strlen', self.i64, [self.i8ptr])
            return self.builder.call(fn, [args[0]])
        if name == 'length':
            if args and isinstance(args[0].type, ir.PointerType):
                fn = self._get_or_declare('strlen', self.i64, [self.i8ptr])
                return self.builder.call(fn, [args[0]])
            return ir.Constant(self.i32, 0)
        if name == 'strcmp':
            fn = self._get_or_declare('strcmp', self.i32, [self.i8ptr, self.i8ptr])
            return self.builder.call(fn, args[:2])
        if name == 'atoi':
            fn = self._get_or_declare('atoi', self.i32, [self.i8ptr])
            return self.builder.call(fn, [args[0]])
        if name == 'atof':
            fn = self._get_or_declare('atof', self.f64, [self.i8ptr])
            return self.builder.call(fn, [args[0]])
        if name == 'sqrt':
            fn = self._get_or_declare('sqrt', self.f64, [self.f64])
            v = args[0]
            if isinstance(v.type, ir.IntType): v = self.builder.sitofp(v, self.f64)
            return self.builder.call(fn, [v])
        if name == 'pow':
            fn = self._get_or_declare('pow', self.f64, [self.f64, self.f64])
            a, b = args[0], args[1]
            if isinstance(a.type, ir.IntType): a = self.builder.sitofp(a, self.f64)
            if isinstance(b.type, ir.IntType): b = self.builder.sitofp(b, self.f64)
            return self.builder.call(fn, [a, b])
        if name in ('abs', 'fabs'):
            if isinstance(args[0].type, ir.DoubleType):
                fn = self._get_or_declare('fabs', self.f64, [self.f64])
                return self.builder.call(fn, [args[0]])
            v = args[0]
            zero = ir.Constant(v.type, 0)
            neg = self.builder.sub(zero, v)
            cond = self.builder.icmp_signed('<', v, zero)
            return self.builder.select(cond, neg, v)
        if name == 'floor':
            fn = self._get_or_declare('floor', self.f64, [self.f64])
            v = args[0]
            if isinstance(v.type, ir.IntType): v = self.builder.sitofp(v, self.f64)
            return self.builder.call(fn, [v])
        if name == 'ceil':
            fn = self._get_or_declare('ceil', self.f64, [self.f64])
            v = args[0]
            if isinstance(v.type, ir.IntType): v = self.builder.sitofp(v, self.f64)
            return self.builder.call(fn, [v])
        if name == 'sin':
            fn = self._get_or_declare('sin', self.f64, [self.f64])
            v = args[0]
            if isinstance(v.type, ir.IntType): v = self.builder.sitofp(v, self.f64)
            return self.builder.call(fn, [v])
        if name == 'cos':
            fn = self._get_or_declare('cos', self.f64, [self.f64])
            v = args[0]
            if isinstance(v.type, ir.IntType): v = self.builder.sitofp(v, self.f64)
            return self.builder.call(fn, [v])
        if name == 'to_int':
            v = args[0]
            if isinstance(v.type, ir.DoubleType):
                return self.builder.fptosi(v, self.i32)
            return v
        if name == 'to_float':
            v = args[0]
            if isinstance(v.type, ir.IntType):
                return self.builder.sitofp(v, self.f64)
            return v
        if name == 'malloc':
            fn = self._get_or_declare('malloc', self.i8ptr, [self.i64])
            return self.builder.call(fn, [args[0]])
        if name == 'free':
            fn = self._get_or_declare('free', ir.VoidType(), [self.i8ptr])
            if isinstance(args[0].type, ir.PointerType):
                raw = self.builder.bitcast(args[0], self.i8ptr)
                self.builder.call(fn, [raw])
            return ir.Constant(self.i32, 0)
        if name == 'upper':
            # toupper each char - simplest: strdup + loop
            s = args[0]
            strlen = self._get_or_declare('strlen', self.i64, [self.i8ptr])
            malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
            n = self.builder.call(strlen, [s])
            size = self.builder.add(n, ir.Constant(self.i64, 1))
            buf = self.builder.call(malloc, [size])
            strcpy = self._get_or_declare('strcpy', self.i8ptr, [self.i8ptr, self.i8ptr])
            self.builder.call(strcpy, [buf, s])
            # Loop and uppercase
            toupper = self._get_or_declare('toupper', self.i32, [self.i32])
            i_alloca = self.builder.alloca(self.i64, name='i')
            self.builder.store(ir.Constant(self.i64, 0), i_alloca)
            loop_bb = self.builder.function.append_basic_block(name='upper.loop')
            body_bb = self.builder.function.append_basic_block(name='upper.body')
            end_bb = self.builder.function.append_basic_block(name='upper.end')
            self.builder.branch(loop_bb)
            self.builder.position_at_end(loop_bb)
            i_val = self.builder.load(i_alloca)
            cond = self.builder.icmp_signed('<', i_val, n)
            self.builder.cbranch(cond, body_bb, end_bb)
            self.builder.position_at_end(body_bb)
            ch_ptr = self.builder.gep(buf, [i_val])
            ch = self.builder.load(ch_ptr)
            ch_ext = self.builder.zext(ch, self.i32)
            upper_ch = self.builder.call(toupper, [ch_ext])
            upper_ch_trunc = self.builder.trunc(upper_ch, self.i8)
            self.builder.store(upper_ch_trunc, ch_ptr)
            i_next = self.builder.add(i_val, ir.Constant(self.i64, 1))
            self.builder.store(i_next, i_alloca)
            self.builder.branch(loop_bb)
            self.builder.position_at_end(end_bb)
            return buf

        if name == 'lower':
            s = args[0]
            strlen = self._get_or_declare('strlen', self.i64, [self.i8ptr])
            malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
            n = self.builder.call(strlen, [s])
            size = self.builder.add(n, ir.Constant(self.i64, 1))
            buf = self.builder.call(malloc, [size])
            strcpy = self._get_or_declare('strcpy', self.i8ptr, [self.i8ptr, self.i8ptr])
            self.builder.call(strcpy, [buf, s])
            tolower = self._get_or_declare('tolower', self.i32, [self.i32])
            i_alloca = self.builder.alloca(self.i64, name='i')
            self.builder.store(ir.Constant(self.i64, 0), i_alloca)
            loop_bb = self.builder.function.append_basic_block(name='lower.loop')
            body_bb = self.builder.function.append_basic_block(name='lower.body')
            end_bb = self.builder.function.append_basic_block(name='lower.end')
            self.builder.branch(loop_bb)
            self.builder.position_at_end(loop_bb)
            i_val = self.builder.load(i_alloca)
            cond = self.builder.icmp_signed('<', i_val, n)
            self.builder.cbranch(cond, body_bb, end_bb)
            self.builder.position_at_end(body_bb)
            ch_ptr = self.builder.gep(buf, [i_val])
            ch = self.builder.load(ch_ptr)
            ch_ext = self.builder.zext(ch, self.i32)
            lower_ch = self.builder.call(tolower, [ch_ext])
            lower_ch_trunc = self.builder.trunc(lower_ch, self.i8)
            self.builder.store(lower_ch_trunc, ch_ptr)
            i_next = self.builder.add(i_val, ir.Constant(self.i64, 1))
            self.builder.store(i_next, i_alloca)
            self.builder.branch(loop_bb)
            self.builder.position_at_end(end_bb)
            return buf

        if name == 'substr':
            # substr(s, start, len) -> strncpy to new buffer
            s = args[0]
            start = args[1]
            length = args[2]
            if isinstance(start.type, ir.IntType) and start.type.width != 64:
                start = self.builder.sext(start, self.i64)
            if isinstance(length.type, ir.IntType) and length.type.width != 64:
                length = self.builder.sext(length, self.i64)
            malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
            size = self.builder.add(length, ir.Constant(self.i64, 1))
            buf = self.builder.call(malloc, [size])
            memcpy = self._get_or_declare('memcpy', self.i8ptr, [self.i8ptr, self.i8ptr, self.i64])
            src_ptr = self.builder.gep(s, [start])
            self.builder.call(memcpy, [buf, src_ptr, length])
            # null terminate
            end_ptr = self.builder.gep(buf, [length])
            self.builder.store(ir.Constant(self.i8, 0), end_ptr)
            return buf

        if name == 'replace' or name == 'swap':
            # replace(s, old, new) — simplified: only replace first
            # For now, return original
            return args[0]

        if name == 'find':
            # strstr(s, sub) -> returns pointer; convert to int offset
            s = args[0]
            sub = args[1]
            strstr = self._get_or_declare('strstr', self.i8ptr, [self.i8ptr, self.i8ptr])
            result = self.builder.call(strstr, [s, sub])
            # Return 0 if found, -1 if not (simplified)
            cond = self.builder.icmp_signed('!=', result, ir.Constant(self.i8ptr, None))
            return self.builder.select(cond, ir.Constant(self.i32, 1), ir.Constant(self.i32, 0))

        if name == 'read_file':
            # read_file(path) -> str
            path = args[0]
            fopen = self._get_or_declare('fopen', self.i8ptr, [self.i8ptr, self.i8ptr])
            mode = self._global_string('r\0', name='.mode_r')
            f = self.builder.call(fopen, [path, mode])
            fseek = self._get_or_declare('fseek', self.i32, [self.i8ptr, self.i64, self.i32])
            ftell = self._get_or_declare('ftell', self.i64, [self.i8ptr])
            fread = self._get_or_declare('fread', self.i64, [self.i8ptr, self.i64, self.i64, self.i8ptr])
            fclose = self._get_or_declare('fclose', self.i32, [self.i8ptr])
            malloc = self._get_or_declare('malloc', self.i8ptr, [self.i64])
            self.builder.call(fseek, [f, ir.Constant(self.i64, 0), ir.Constant(self.i32, 2)])
            size = self.builder.call(ftell, [f])
            self.builder.call(fseek, [f, ir.Constant(self.i64, 0), ir.Constant(self.i32, 0)])
            one = self.builder.add(size, ir.Constant(self.i64, 1))
            buf = self.builder.call(malloc, [one])
            self.builder.call(fread, [buf, ir.Constant(self.i64, 1), size, f])
            # null-terminate
            end_ptr = self.builder.gep(buf, [size])
            self.builder.store(ir.Constant(self.i8, 0), end_ptr)
            self.builder.call(fclose, [f])
            return buf

        if name == 'write_file':
            # write_file(path, content) -> int (bytes)
            path = args[0]
            content = args[1]
            fopen = self._get_or_declare('fopen', self.i8ptr, [self.i8ptr, self.i8ptr])
            mode = self._global_string('w\0', name='.mode_w')
            f = self.builder.call(fopen, [path, mode])
            strlen = self._get_or_declare('strlen', self.i64, [self.i8ptr])
            n = self.builder.call(strlen, [content])
            fwrite = self._get_or_declare('fwrite', self.i64, [self.i8ptr, self.i64, self.i64, self.i8ptr])
            written = self.builder.call(fwrite, [content, ir.Constant(self.i64, 1), n, f])
            fclose = self._get_or_declare('fclose', self.i32, [self.i8ptr])
            self.builder.call(fclose, [f])
            return written

        if name == 'append_file':
            path = args[0]
            content = args[1]
            fopen = self._get_or_declare('fopen', self.i8ptr, [self.i8ptr, self.i8ptr])
            mode = self._global_string('a\0', name='.mode_a')
            f = self.builder.call(fopen, [path, mode])
            strlen = self._get_or_declare('strlen', self.i64, [self.i8ptr])
            n = self.builder.call(strlen, [content])
            fwrite = self._get_or_declare('fwrite', self.i64, [self.i8ptr, self.i64, self.i64, self.i8ptr])
            written = self.builder.call(fwrite, [content, ir.Constant(self.i64, 1), n, f])
            fclose = self._get_or_declare('fclose', self.i32, [self.i8ptr])
            self.builder.call(fclose, [f])
            return written

        if name == 'printf':
            # printf(fmt, args...) — first arg must be str
            printf_fn = self._get_or_declare_printf()
            return self.builder.call(printf_fn, args)

        if name == 'exit':
            exit_fn = self._get_or_declare('exit', ir.VoidType(), [self.i32])
            self.builder.call(exit_fn, [args[0] if args else ir.Constant(self.i32, 0)])
            return ir.Constant(self.i32, 0)

        if name == 'sizeof':
            # sizeof(expr) at runtime — approximate
            if args:
                a = args[0]
                if isinstance(a.type, ir.IntType):
                    return ir.Constant(self.i32, max(1, a.type.width // 8))
                if isinstance(a.type, ir.DoubleType):
                    return ir.Constant(self.i32, 8)
            return ir.Constant(self.i32, 8)

        raise CodegenError(f'Unknown builtin: {name}')

    def _get_or_declare(self, name, ret, args):
        """Get or declare an external C function."""
        if name in self.funcs:
            return self.funcs[name]
        fn_ty = ir.FunctionType(ret, args)
        fn = ir.Function(self.module, fn_ty, name=name)
        self.funcs[name] = fn
        return fn

    def _get_or_declare_printf(self):
        if 'printf' in self.funcs:
            return self.funcs['printf']
        fn_ty = ir.FunctionType(self.i32, [self.i8ptr], var_arg=True)
        fn = ir.Function(self.module, fn_ty, name='printf')
        self.funcs['printf'] = fn
        return fn

    def _get_or_declare_puts(self):
        if 'puts' in self.funcs:
            return self.funcs['puts']
        fn_ty = ir.FunctionType(self.i32, [self.i8ptr])
        fn = ir.Function(self.module, fn_ty, name='puts')
        self.funcs['puts'] = fn
        return fn


def compile_to_llvm(source):
    ast = parse(source)
    return LLVMCodegen().compile(ast)




# ═══ Optimization passes (safe — no segfault) ═══
def optimize_module(mod, level=3):
    """Optimization passes skipped (llvmlite API buggy). Uses tm(opt=N) instead."""
    return []
def jit_run(source, fn_name='main', opt_level=2):
    """Compile and run with JIT, return exit value."""
    llvm_ir = compile_to_llvm(source)
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()

    if opt_level > 0:
        optimize_module(mod, opt_level)

    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine(opt=opt_level)
    engine = llvm.create_mcjit_compiler(mod, target_machine)
    engine.finalize_object()
    addr = engine.get_function_address(fn_name)
    fn = ctypes.CFUNCTYPE(ctypes.c_int32)(addr)
    return fn()


def compile_to_binary(source, out_name='a.out', opt_level=3):
    """Compile to native binary."""
    import subprocess, os
    llvm_ir = compile_to_llvm(source)

    # Parse + verify
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()

    if opt_level > 0:
        optimize_module(mod, opt_level)

    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine(opt=opt_level)
    obj = target_machine.emit_object(mod)

    obj_file = out_name + '.o'
    with open(obj_file, 'wb') as f:
        f.write(obj)

    # Link with system libc
    r = subprocess.run(['cc', '-o', out_name, obj_file, '-lm'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print('Link failed:', r.stderr)
        return False
    if not os.path.exists(out_name + '.keep.o'):
        os.remove(obj_file)
    print(f'✓ Built {out_name}')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: codegen_llvm_v3.py <file.cat> [--ir|--run|--build output]')
        sys.exit(1)
    src = open(sys.argv[1]).read()
    try:
        if '--ir' in sys.argv or len(sys.argv) == 2:
            print(compile_to_llvm(src))
        elif '--run' in sys.argv:
            result = jit_run(src)
            print(f'Exit: {result}')
        elif '--build' in sys.argv:
            out = sys.argv[sys.argv.index('--build') + 1]
            compile_to_binary(src, out)
    except (ParseError, CodegenError) as e:
        print(f'Error: {e}')
        sys.exit(1)
