#!/usr/bin/env python3
"""Cat++ -> C transpiler (A1+A2+A3+A4)."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interpreter import tokenize, Parser, CatError

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runtime_c.h'), encoding='utf-8') as _f:
    RUNTIME = _f.read()

BUILTIN_NAMES = {'tail','puff','melt','nip','bolt','kitten','lion','say','tally','drip',
    'collar','kits','seek','shred','weave','swap','lick','hunt','stash','snatch','line',
    'flip','head','rear','pile','walk','wander','dice','scratch','flop','perch','bound',
    'sway','wave','slant','grow'}

def c_esc(s):
    return s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\t','\\t').replace('\r','\\r')

class CTranspiler:
    def __init__(self):
        self.out=[]; self.indent=0; self.funcs={}; self.classes={}; self.structs={}; self.tc=0
    def line(self,s=''): self.out.append('    '*self.indent+s)
    def new_tmp(self): self.tc+=1; return f'__t{self.tc}'

    def expr(self, e):
        t=e[0]
        if t=='num':
            v=e[1]
            if isinstance(v,float): return f'V_double({repr(v)})'
            return f'V_int({int(v)}LL)'
        if t=='str': return f'V_str("{c_esc(e[1])}")'
        if t=='bool': return f'V_bool({1 if e[1] else 0})'
        if t=='null': return 'V_null()'
        if t=='var': return e[1]
        if t=='neg': return f'v_neg({self.expr(e[1])})'
        if t=='not': return f'v_not({self.expr(e[1])})'
        if t=='bitnot': return f'V_int(~v_to_int({self.expr(e[1])}))'
        if t=='and': return f'V_bool(v_truthy({self.expr(e[1])}) && v_truthy({self.expr(e[2])}))'
        if t=='or': return f'V_bool(v_truthy({self.expr(e[1])}) || v_truthy({self.expr(e[2])}))'
        if t in ('+','-','*','/','%'):
            m={'+':'v_add','-':'v_sub','*':'v_mul','/':'v_div','%':'v_mod'}
            return f'{m[t]}({self.expr(e[1])}, {self.expr(e[2])})'
        if t in ('&','|','^'):
            return f'V_int(v_to_int({self.expr(e[1])}) {t} v_to_int({self.expr(e[2])}))'
        if t in ('SHL','SHR'):
            m='<<' if t=='SHL' else '>>'
            return f'V_int(v_to_int({self.expr(e[1])}) {m} v_to_int({self.expr(e[2])}))'
        if t in ('==','!=','<','>','<=','>='):
            op={'==':0,'!=':1,'<':2,'>':3,'<=':4,'>=':5}[t]
            return f'V_bool(v_cmp({self.expr(e[1])}, {self.expr(e[2])}, {op}))'
        if t=='list':
            items=e[1]
            if not items: return 'v_list_empty()'
            return f'v_list_build({len(items)}, (Value[]){{{", ".join(self.expr(x) for x in items)}}})'
        if t=='dict':
            pairs=e[1]
            if not pairs: return 'v_dict_empty()'
            ks=', '.join(self.expr(k) for k,v in pairs)
            vs=', '.join(self.expr(v) for k,v in pairs)
            return f'v_dict_build({len(pairs)}, (Value[]){{{ks}}}, (Value[]){{{vs}}})'
        if t=='index': return f'v_index({self.expr(e[1])}, {self.expr(e[2])})'
        if t=='slice':
            obj=self.expr(e[1])
            lo=self.expr(e[2]) if e[2] else 'V_null()'
            hi=self.expr(e[3]) if e[3] else 'V_null()'
            hl='1' if e[2] else '0'; hh='1' if e[3] else '0'
            return f'v_slice({obj}, {lo}, {hi}, {hl}, {hh})'
        if t=='dot': return f'v_dot({self.expr(e[1])}, "{e[2]}")'
        if t=='call':
            name=e[1]; args_list=e[2]
            args=', '.join(self.expr(a) for a in args_list)
            if name in self.structs:
                fields = self.structs[name]
                fields_c = ', '.join('"' + f + '"' for f in fields)
                if args_list:
                    return f'v_struct_new("{name}", (const char*[]){{{fields_c}}}, {len(fields)}, (Value[]){{{args}}}, {len(args_list)})'
                return f'v_struct_new("{name}", (const char*[]){{{fields_c}}}, {len(fields)}, NULL, 0)'
            if name in self.classes:
                return f'v_new("{name}", (Value[]){{{args}}}, {len(args_list)})' if args_list else f'v_new("{name}", NULL, 0)'
            if name in BUILTIN_NAMES: return f'bi_{name}({args})'
            return f'{name}({args})'
        if t=='method_call':
            obj=self.expr(e[1]); args=e[3]
            if not args: return f'v_call_method({obj}, "{e[2]}", NULL, 0)'
            inner=', '.join(self.expr(a) for a in args)
            return f'v_call_method({obj}, "{e[2]}", (Value[]){{{inner}}}, {len(args)})'
        if t=='in': return f'V_bool(v_in({self.expr(e[1])}, {self.expr(e[2])}))'
        if t=='ternary': return f'(v_truthy({self.expr(e[1])}) ? {self.expr(e[2])} : {self.expr(e[3])})'
        if t=='coalesce':
            l=self.expr(e[1])
            return f'({l}.t != T_NULL ? {l} : {self.expr(e[2])})'
        if t=='cast':
            tn=e[1].lower(); v=self.expr(e[2])
            if tn in ('i8','i16','i32','i64','int','u8','u16','u32','u64','byte','char','ptr'):
                return f'V_int(v_cast_int({v}))'
            if tn=='float': return f'V_double(v_cast_float({v}))'
            if tn=='bool': return f'V_bool(v_truthy({v}))'
            if tn=='str':
                return f'({{ char* __cs=v_to_str({v}); Value __cr=V_str(__cs); free(__cs); __cr; }})'
            return v
        if t=='sizeof': return 'V_int(8)'
        if t=='sizeof_type': return f'V_int(v_sizeof_type("{e[1]}"))'
        if t=='asm': return 'V_null()'
        if t=='addr': raise CatError("Transpiler C chua ho tro &x")
        if t=='deref': raise CatError("Transpiler C chua ho tro *p")
        if t=='lambda': raise CatError("Transpiler C chua ho tro kit (lambda)")
        raise CatError(f"Transpiler C chua ho tro expr: {t}")

    def collect_lets(self, stmts, into):
        for s in stmts:
            tt=s[0]
            if tt=='let': into.add(s[1])
            elif tt=='if':
                self.collect_lets(s[2],into)
                if s[3]: self.collect_lets(s[3],into)
            elif tt=='while': self.collect_lets(s[2],into)
            elif tt=='each': self.collect_lets(s[3],into)
            elif tt=='try':
                self.collect_lets(s[1], into)
                if s[3]: self.collect_lets(s[3], into)
            elif tt=='match':
                for pat, body in s[2]: self.collect_lets(body, into)

    def stmt(self, s):
        t=s[0]
        if t=='let': self.line(f'{s[1]} = {self.expr(s[2])};')
        elif t=='assign': self.line(f'{s[1]} = {self.expr(s[2])};')
        elif t=='assign_target':
            target=s[1]; val=self.expr(s[2])
            if target[0]=='index': self.line(f'v_index_set({self.expr(target[1])}, {self.expr(target[2])}, {val});')
            elif target[0]=='dot': self.line(f'v_dot_set({self.expr(target[1])}, "{target[2]}", {val});')
            elif target[0]=='var': self.line(f'{target[1]} = {val};')
            else: raise CatError("assign_target")
        elif t=='op_assign':
            target=s[1]; op=s[2]; rhs=s[3]
            if target[0]!='var': raise CatError("op_assign chi ho tro bien")
            name=target[1]; py_op=op[:-1]
            m={'+':'v_add','-':'v_sub','*':'v_mul','/':'v_div','%':'v_mod'}
            self.line(f'{name} = {m[py_op]}({name}, {self.expr(rhs)});')
        elif t=='print': self.line(f'v_print({self.expr(s[1])});')
        elif t=='expr': self.line(f'(void){self.expr(s[1])};')
        elif t=='return': self.line(f'return {self.expr(s[1])};')
        elif t=='if':
            self.line(f'if (v_truthy({self.expr(s[1])})) {{')
            self.indent+=1
            for x in s[2]: self.stmt(x)
            self.indent-=1
            if s[3]:
                self.line('} else {')
                self.indent+=1
                for x in s[3]: self.stmt(x)
                self.indent-=1
            self.line('}')
        elif t=='while':
            self.line(f'while (v_truthy({self.expr(s[1])})) {{')
            self.indent+=1
            for x in s[2]: self.stmt(x)
            self.indent-=1
            self.line('}')
        elif t=='each':
            name=s[1]; it=self.expr(s[2]); body=s[3]
            tmp=self.new_tmp(); idx=self.new_tmp()
            self.line(f'{{ Value {tmp} = {it};')
            self.line(f'  for (int {idx} = 0; {idx} < {tmp}.list->len; {idx}++) {{')
            self.line(f'    Value {name} = {tmp}.list->items[{idx}];')
            self.indent+=2
            for x in body: self.stmt(x)
            self.indent-=2
            self.line('  }')
            self.line('}')
        elif t=='stop': self.line('break;')
        elif t=='skip': self.line('continue;')
        elif t=='match':
            subj=self.expr(s[1]); tmp=self.new_tmp()
            self.line(f'{{ Value {tmp} = {subj};')
            self.indent+=1
            first=True
            for pat, body in s[2]:
                if pat[0]=='var' and pat[1]=='_':
                    if not first: self.line('else {')
                    else: self.line('{')
                else:
                    pv=self.expr(pat)
                    kw='if' if first else 'else if'
                    self.line(f'{kw} (v_cmp({tmp}, {pv}, 0)) {{')
                first=False
                self.indent+=1
                for x in body: self.stmt(x)
                self.indent-=1
                self.line('}')
            self.indent-=1
            self.line('}')
        elif t=='try':
            body, errname, handler = s[1], s[2], s[3]
            depth=self.new_tmp()
            self.line(f'{{ jmp_buf __jb_{depth}; int __save_{depth} = __jmp_top; __jmp_stack[__jmp_top++] = &__jb_{depth};')
            self.line(f'  if (setjmp(__jb_{depth}) == 0) {{')
            self.indent+=2
            for x in body: self.stmt(x)
            self.indent-=2
            if handler:
                self.line('  } else {')
                self.indent+=2
                if errname:
                    self.line(f'Value {errname} = V_str(__catpp_err_msg);')
                for x in handler: self.stmt(x)
                self.indent-=2
                self.line('  }')
            else:
                self.line('  }')
            self.line(f'  __jmp_top = __save_{depth};')
            self.line('}')
        else: raise CatError(f"Transpiler C chua ho tro stmt: {t}")

    def emit_func(self, s):
        name=s[1]; params=s[2]; body=s[4]
        pd=', '.join(f'Value {p}' for p in params) if params else 'void'
        self.line(f'static Value {name}({pd}) {{')
        self.indent+=1
        lets=set(); self.collect_lets(body, lets); lets-=set(params)
        for v in sorted(lets): self.line(f'Value {v};')
        for x in body: self.stmt(x)
        self.line('return V_null();')
        self.indent-=1
        self.line('}')

    def emit_method(self, cidx, midx, params, body):
        fname=f'__meth_{cidx}_{midx}'
        self.line(f'static Value {fname}(Value me, Value* __args, int __argc) {{')
        self.indent+=1
        for i,p in enumerate(params):
            self.line(f'Value {p} = __argc > {i} ? __args[{i}] : V_null();')
        lets=set(); self.collect_lets(body, lets); lets-=set(params)
        for v in sorted(lets): self.line(f'Value {v};')
        for x in body: self.stmt(x)
        self.line('return V_null();')
        self.indent-=1
        self.line('}')
        return fname

    def emit_class(self, s, cidx):
        name=s[1]; parent=s[2]; fields=s[3]; methods=s[4]
        mnames=[]
        for mi,(mname,(params,body)) in enumerate(methods.items()):
            fname=f'__meth_{cidx}_{mi}'
            self.line(f'static Value {fname}(Value me, Value* __args, int __argc);')
            mnames.append((mname,fname))
        self.out.append('')
        for mi,(mname,(params,body)) in enumerate(methods.items()):
            self.emit_method(cidx, mi, params, body)
            self.line('')
        tbl=f'__methods_{cidx}'
        self.line(f'static MethodEntry {tbl}[] = {{')
        self.indent+=1
        for mname,fname in mnames:
            self.line(f'{{ "{mname}", {fname} }},')
        if not mnames: self.line('{ "", NULL },')
        self.indent-=1
        self.line('};')
        ftbl=f'__fields_{cidx}'
        self.line(f'static char* {ftbl}[] = {{')
        self.indent+=1
        for f in fields:
            self.line(f'"{f}",')
        if not fields: self.line('NULL,')
        self.indent-=1
        self.line('};')
        par=f'"{parent}"' if parent else 'NULL'
        self.line(f'static ClassDef __clsd_{cidx} = {{ "{name}", {par}, {tbl}, {len(mnames)}, {ftbl}, {len(fields)} }};')
        self.line('')

    def compile(self, ast):
        cidx=0
        for s in ast:
            if s[0]=='struct': self.structs[s[1]]=s[2]
        for s in ast:
            if s[0]=='func': self.funcs[s[1]]=(s[2],s[4])
            elif s[0]=='class': self.classes[s[1]]=cidx; cidx+=1

        self.out.append(RUNTIME)
        self.out.append('')

        for name,(params,_) in self.funcs.items():
            pd=', '.join(f'Value {p}' for p in params) if params else 'void'
            self.line(f'static Value {name}({pd});')
        self.out.append('')

        for s in ast:
            if s[0]=='class':
                self.emit_class(s, self.classes[s[1]])
        for s in ast:
            if s[0]=='func':
                self.emit_func(s); self.line('')

        self.line('int main(void) {')
        self.indent+=1
        for s in ast:
            if s[0]=='class':
                self.line(f'reg_class(&__clsd_{self.classes[s[1]]});')
        top=[s for s in ast if s[0] not in ('func','class','struct')]
        lets=set(); self.collect_lets(top, lets)
        for v in sorted(lets): self.line(f'Value {v};')
        for s in top: self.stmt(s)
        self.line('return 0;')
        self.indent-=1
        self.line('}')
        return '\n'.join(self.out)


def _resolve_uses(ast, base_dir):
    result = []
    for s in ast:
        if s[0] == 'use':
            fname = s[1]
            candidates = [os.path.join(base_dir, fname), os.path.join(base_dir,'examples',fname), fname]
            found = None
            for p in candidates:
                if os.path.exists(p):
                    found = p; break
            if not found:
                raise CatError(f"Khong tim thay file '{fname}'")
            with open(found, encoding='utf-8') as f:
                lib_src = f.read()
            lib_ast = Parser(tokenize(lib_src)).parse()
            result.extend(_resolve_uses(lib_ast, os.path.dirname(found) or base_dir))
        else:
            result.append(s)
    return result


def transpile(source, base_dir='.'):
    ast = Parser(tokenize(source)).parse()
    ast = _resolve_uses(ast, base_dir)
    return CTranspiler().compile(ast)


def main():
    if len(sys.argv)<2:
        print(__doc__); return 1
    src=sys.argv[1]
    with open(src, encoding='utf-8') as f: source=f.read()
    try: c_code=transpile(source, base_dir=os.path.dirname(os.path.abspath(src)))
    except CatError as e: print(f'X {e}'); return 1
    out=src.rsplit('.',1)[0]+'.c'
    if '-o' in sys.argv: out=sys.argv[sys.argv.index('-o')+1]
    with open(out,'w',encoding='utf-8') as f: f.write(c_code)
    print(f'OK {out}')
    if '--run' in sys.argv:
        binp=out.rsplit('.',1)[0]
        r=subprocess.run(['gcc','-O2','-lm','-o',binp,out], capture_output=True, text=True)
        if r.returncode!=0: print('gcc fail:'); print(r.stderr); return 1
        r=subprocess.run([binp], capture_output=True, text=True)
        print('--- Output ---'); print(r.stdout, end='')
        if r.stderr: print(r.stderr, end='')
    return 0

if __name__=='__main__': sys.exit(main())
