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
        self._var_classes = {}

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
                # Strict identity check
                for cname, cty in self._class_types.items():
                    if ir_ty is cty:
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

    def emit(self, line=''):
        self.lines.append('  ' * self.indent + line)

    def c_type(self, vtype):
        base, ptr_depth, array_size, generic = vtype
        if base in ('int', 'bool'):
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
            base_t = self.i32  # fallback
        for _ in range(ptr_depth):
            base_t = ir.PointerType(base_t)
        return base_t

    def compile(self, ast):
        # Pass 0: collect classes and functions
        self._collect(ast[1])

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
            for st in body:
                self._emit_stmt(st)
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
            for st in body: self._emit_stmt(st)
            if not self.builder.block.is_terminated:
                self.builder.branch(cond_bb)

            self.builder.position_at_end(end_bb)
            return None

        if t == 'expr_stmt':
            self._emit_expr(s[1])
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

        if t == 'str':
            s = e[1]
            if not s.endswith('\0'):
                s += '\0'
            return self._global_string(s, name='.str')

        if t == 'char':
            return ir.Constant(self.i8, ord(e[1]) if e[1] else 0)

        if t == 'null':
            return ir.Constant(self.i8ptr, None)

        if t == 'me':
            if 'me' not in self.env:
                raise CodegenError('me not in scope')
            alloca, ctype = self.env['me']
            return self.builder.load(alloca, name='me')

        if t == 'var':
            name = e[1]
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

        if t == 'member':
            obj_expr = e[1]
            field_name = e[2]
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
