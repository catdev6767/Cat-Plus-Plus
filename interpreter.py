from dataclasses import dataclass
import os, time, math, random as _random, sys

KEYWORDS = {'paw','meow','purr','give','hiss','tap','sit','leap','listen',
            'sniff','swat','knead','groom','of','nod','shake','hungry',
            'with','either','never','cat','me','kin','kit','litter','in',
            'match','case','use','in',
            'struct','volatile','cast','sizeof','asm','ptr','null','packed'}

class CatError(Exception):
    def __init__(self, msg, line=0): super().__init__(msg); self.line = line

@dataclass
class Tok:
    type: str; value: object; line: int

def tokenize(src):
    toks, indent_stack = [], [0]
    lines = src.split('\n')
    for ln, line in enumerate(lines, 1):
        stripped = line.lstrip(' \t')
        if not stripped or stripped.startswith('#'): continue
        indent = len(line) - len(line.lstrip(' \t'))
        if indent > indent_stack[-1]:
            indent_stack.append(indent); toks.append(Tok('INDENT','',ln))
        while indent < indent_stack[-1]:
            indent_stack.pop(); toks.append(Tok('DEDENT','',ln))
        i = 0
        while i < len(line):
            c = line[i]
            if c in ' \t': i += 1; continue
            if c == '#': break
            if c.isdigit():
                j = i
                if i+1 < len(line) and line[i+1] in 'xX':
                    j = i + 2
                    while j < len(line) and line[j] in '0123456789abcdefABCDEF': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 16)), ln)); i = j; continue
                if i+1 < len(line) and line[i+1] in 'bB':
                    j = i + 2
                    while j < len(line) and line[j] in '01': j += 1
                    toks.append(Tok('NUMBER', float(int(line[i:j], 2)), ln)); i = j; continue
                while j < len(line) and (line[j].isdigit() or line[j]=='.'): j += 1
                ns = line[i:j]
                toks.append(Tok('NUMBER', float(ns) if '.' in ns else int(ns), ln))
                i = j; continue
            if c == '"':
                j, s = i+1, ''
                while j < len(line) and line[j] != '"':
                    if line[j]=='\\' and j+1<len(line):
                        s += {'n':'\n','t':'\t','"':'"','\\':'\\'}.get(line[j+1], line[j+1]); j += 2
                    else: s += line[j]; j += 1
                toks.append(Tok('STRING', s, ln)); i = j+1; continue
            if c.isalpha() or c == '_':
                j = i
                while j < len(line) and (line[j].isalnum() or line[j]=='_'): j += 1
                w = line[i:j]
                toks.append(Tok(w.upper() if w in KEYWORDS else 'IDENT', w, ln)); i = j; continue
            two = line[i:i+2]
            if two == '<<': toks.append(Tok('SHL', '<<', ln)); i += 2; continue
            if two == '>>': toks.append(Tok('SHR', '>>', ln)); i += 2; continue
            if two == '->': toks.append(Tok('ARROW_R', '->', ln)); i += 2; continue
            if two == '??': toks.append(Tok('COALESCE', '??', ln)); i += 2; continue
            if two in ('+=','-=','*=','/=','%='):
                toks.append(Tok('OP_ASSIGN', two, ln)); i += 2; continue
            if two == '++': toks.append(Tok('INC', '++', ln)); i += 2; continue
            if two == '--': toks.append(Tok('DEC', '--', ln)); i += 2; continue
            if two == '=>': toks.append(Tok('ARROW', '=>', ln)); i += 2; continue
            if two in ('==','!=','<=','>='): toks.append(Tok(two, two, ln)); i += 2; continue
            if c == '&': toks.append(Tok('AMP', '&', ln)); i += 1; continue
            if c == '|': toks.append(Tok('PIPE', '|', ln)); i += 1; continue
            if c == '^': toks.append(Tok('CARET', '^', ln)); i += 1; continue
            if c == '~': toks.append(Tok('TILDE', '~', ln)); i += 1; continue
            if c == '?': toks.append(Tok('QUESTION', '?', ln)); i += 1; continue
            if c in '+-*/%=<>()[]{}.,:': toks.append(Tok(c, c, ln)); i += 1; continue
            i += 1
        toks.append(Tok('NEWLINE','',ln))
    while len(indent_stack) > 1:
        indent_stack.pop(); toks.append(Tok('DEDENT','',len(lines)))
    toks.append(Tok('EOF','',0))
    return toks


class Parser:
    def __init__(self, toks): self.toks, self.pos = toks, 0
    def peek(self, off=0):
        i = self.pos + off
        return self.toks[i] if i < len(self.toks) else self.toks[-1]
    def next(self): t = self.toks[self.pos]; self.pos += 1; return t
    def expect(self, tp):
        t = self.next()
        if t.type != tp: raise CatError(f"Can '{tp}', gap '{t.type}'", t.line)
        return t
    def skip_nl(self):
        while self.peek().type == 'NEWLINE': self.next()
    def parse(self):
        stmts = []; self.skip_nl()
        while self.peek().type != 'EOF':
            stmts.append(self.stmt()); self.skip_nl()
        return stmts
    def block(self):
        self.expect('NEWLINE'); self.expect('INDENT')
        stmts = []; self.skip_nl()
        while self.peek().type not in ('DEDENT','EOF'):
            stmts.append(self.stmt()); self.skip_nl()
        if self.peek().type == 'DEDENT': self.next()
        return stmts
    def class_body(self):
        self.expect('NEWLINE'); self.expect('INDENT')
        fields, methods = [], {}
        self.skip_nl()
        while self.peek().type not in ('DEDENT','EOF'):
            t = self.peek()
            if t.type == 'PAW':
                self.next(); name = self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(name)
            elif t.type == 'PURR':
                self.next(); mname = self.expect('IDENT').value
                params = []
                while self.peek().type == 'IDENT': params.append(self.next().value)
                if self.peek().type == '(':
                    self.next()
                    if self.peek().type != ')':
                        params.append(self.expect('IDENT').value)
                        while self.peek().type == ',': self.next(); params.append(self.expect('IDENT').value)
                    self.expect(')')
                body = self.block()
                methods[mname] = (params, body)
            else: raise CatError(f"Cat chi chua paw hoac purr", t.line)
            self.skip_nl()
        if self.peek().type == 'DEDENT': self.next()
        return fields, methods
    def parse_target(self):
        t = self.peek()
        if t.type == 'IDENT': e = ('var', self.next().value)
        elif t.type == 'ME': self.next(); e = ('var', 'me')
        else: return None
        while True:
            if self.peek().type == '[':
                self.next(); idx = self.expr(); self.expect(']')
                e = ('index', e, idx)
            elif self.peek().type == '.':
                self.next(); name = self.expect('IDENT').value
                e = ('dot', e, name)
            else: break
        return e
    def stmt(self):
        t = self.peek()
        if t.type == 'PAW':
            self.next(); name = self.expect('IDENT').value
            type_name = None
            if self.peek().type == ':':
                self.next()
                if self.peek().type in ('NEWLINE', '=', ','):
                    raise CatError("Thieu type sau ':'", self.peek().line)
                type_name = self.next().value
            if self.peek().type == '=':
                self.next(); e = self.expr(); self.expect('NEWLINE')
                return ('let', name, e, t.line, type_name)
            self.expect('NEWLINE'); return ('let', name, ('null',), t.line, type_name)
        if t.type == 'MEOW':
            self.next(); e = self.expr(); self.expect('NEWLINE'); return ('print', e, t.line)
        if t.type == 'LISTEN':
            self.next(); name = self.expect('IDENT').value
            self.expect('NEWLINE'); return ('listen', name, t.line)
        if t.type == 'PURR':
            self.next(); name = self.expect('IDENT').value
            params = []
            defaults = {}
            param_types = {}

            # Params ngoai ngoac: purr f a b
            while self.peek().type == 'IDENT':
                pname = self.next().value
                params.append(pname)
                if self.peek().type == '=':
                    self.next()
                    defaults[pname] = self.expr()
                elif self.peek().type == ':':
                    self.next()
                    if self.peek().type in ('NEWLINE', '=', ',', ')'):
                        raise CatError("Thieu type sau ':'", self.peek().line)
                    param_types[pname] = self.next().value
                    if self.peek().type == '=':
                        self.next()
                        defaults[pname] = self.expr()

            # Params trong ngoac: purr f(a, b)
            if self.peek().type == '(':
                self.next()
                if self.peek().type != ')':
                    pname = self.expect('IDENT').value
                    params.append(pname)
                    if self.peek().type == '=':
                        self.next()
                        defaults[pname] = self.expr()
                    elif self.peek().type == ':':
                        self.next()
                        if self.peek().type in ('NEWLINE', '=', ',', ')'):
                            raise CatError("Thieu type sau ':'", self.peek().line)
                        param_types[pname] = self.next().value
                        if self.peek().type == '=':
                            self.next()
                            defaults[pname] = self.expr()
                    while self.peek().type == ',':
                        self.next()
                        pname = self.expect('IDENT').value
                        params.append(pname)
                        if self.peek().type == '=':
                            self.next()
                            defaults[pname] = self.expr()
                        elif self.peek().type == ':':
                            self.next()
                            if self.peek().type in ('NEWLINE', '=', ',', ')'):
                                raise CatError("Thieu type sau ':'", self.peek().line)
                            param_types[pname] = self.next().value
                            if self.peek().type == '=':
                                self.next()
                                defaults[pname] = self.expr()
                self.expect(')')

            # Return type: -> i32
            return_type = None
            if self.peek().type == 'ARROW_R':
                self.next()
                if self.peek().type == 'NEWLINE':
                    raise CatError("Thieu return type sau '->'", self.peek().line)
                return_type = self.next().value

            body = self.block()
            return ('func', name, params, defaults, body, t.line, param_types, return_type)

        if t.type == 'STRUCT':
            self.next()
            if self.peek().type == 'PACKED': self.next()
            name = self.expect('IDENT').value
            self.expect('NEWLINE'); self.expect('INDENT')
            fields = []; self.skip_nl()
            while self.peek().type not in ('DEDENT','EOF'):
                fname = self.expect('IDENT').value
                if self.peek().type == ':': self.next(); self.expect('IDENT').value
                self.expect('NEWLINE'); fields.append(fname); self.skip_nl()
            if self.peek().type == 'DEDENT': self.next()
            return ('struct', name, fields, t.line)
        if t.type == 'VOLATILE':
            self.next()
            if self.peek().type == 'PAW': return self.stmt()
            e = self.expr(); self.expect('NEWLINE'); return ('expr', e, t.line)
        if t.type == 'CAT':
            self.next(); name = self.expect('IDENT').value; parent = None
            if self.peek().type == 'KIN':
                self.next(); parent = self.expect('IDENT').value
            fields, methods = self.class_body()
            return ('class', name, parent, fields, methods, t.line)
        if t.type == 'LITTER':
            self.next(); name = self.expect('IDENT').value
            self.expect('NEWLINE'); self.expect('INDENT')
            members = []; self.skip_nl()
            while self.peek().type not in ('DEDENT','EOF'):
                members.append(self.expect('IDENT').value)
                self.skip_nl()
            if self.peek().type == 'DEDENT': self.next()
            return ('enum', name, members, t.line)
        if t.type == 'GIVE':
            self.next(); e = self.expr(); self.expect('NEWLINE'); return ('return', e, t.line)
        if t.type == 'SNIFF':
            self.next(); cond = self.expr(); then = self.block(); els = None
            if self.peek().type == 'SWAT': self.next(); els = self.block()
            return ('if', cond, then, els, t.line)
        if t.type == 'KNEAD':
            self.next(); cond = self.expr(); body = self.block()
            return ('while', cond, body, t.line)
        if t.type == 'GROOM':
            self.next(); name = self.expect('IDENT').value
            self.expect('OF'); e = self.expr(); body = self.block()
            return ('each', name, e, body, t.line)
        if t.type == 'TAP':
            self.next(); body = self.block()
            errname = None; handler = None
            if self.peek().type == 'HISS':
                self.next()
                if self.peek().type == 'IDENT': errname = self.next().value
                handler = self.block()
            return ('try', body, errname, handler, t.line)
        if t.type == 'MATCH' and self.peek(1).type != '(':
            self.next(); subject = self.expr()
            self.expect('NEWLINE'); self.expect('INDENT')
            cases = []; self.skip_nl()
            while self.peek().type not in ('DEDENT','EOF'):
                if self.peek().type == 'CASE':
                    self.next()
                    pat = self.expr()
                    body = self.block()
                    cases.append((pat, body))
                else:
                    raise CatError("Match chi chua case", self.peek().line)
                self.skip_nl()
            if self.peek().type == 'DEDENT': self.next()
            return ('match', subject, cases, t.line)
        if t.type == 'USE':
            self.next()
            path_tok = self.expect('STRING')
            self.expect('NEWLINE')
            return ('use', path_tok.value, t.line)
        if t.type == 'SIT': self.next(); self.expect('NEWLINE'); return ('stop', t.line)
        if t.type == 'LEAP': self.next(); self.expect('NEWLINE'); return ('skip', t.line)
        if t.type == '*':
            save = self.pos
            target_expr = self.unary()
            nt = self.peek()
            if nt.type == '=':
                self.next(); e = self.expr(); self.expect('NEWLINE')
                return ('assign_target', target_expr, e, t.line)
            elif nt.type == 'OP_ASSIGN':
                op = self.next().value
                e = self.expr(); self.expect('NEWLINE')
                return ('op_assign', target_expr, op, e, t.line)
            self.pos = save

        if t.type in ('IDENT','ME'):
            save = self.pos
            target = self.parse_target()
            if target:
                nt = self.peek()
                if nt.type == '=':
                    self.next(); e = self.expr(); self.expect('NEWLINE')
                    if target[0] == 'var': return ('assign', target[1], e, t.line)
                    return ('assign_target', target, e, t.line)
                elif nt.type == 'OP_ASSIGN':
                    op = self.next().value
                    e = self.expr(); self.expect('NEWLINE')
                    return ('op_assign', target, op, e, t.line)
                elif nt.type == 'INC':
                    self.next(); self.expect('NEWLINE')
                    return ('op_assign', target, '+=', ('num', 1), t.line)
                elif nt.type == 'DEC':
                    self.next(); self.expect('NEWLINE')
                    return ('op_assign', target, '-=', ('num', 1), t.line)
            self.pos = save
        e = self.expr(); self.expect('NEWLINE'); return ('expr', e, t.line)
    def expr(self):
        e = self.or_()
        # Coalesce: x ?? y
        while self.peek().type == 'COALESCE':
            self.next()
            e = ('coalesce', e, self.or_())
        # Ternary: cond ? a : b
        if self.peek().type == 'QUESTION':
            self.next()
            then = self.expr()
            self.expect(':')
            els = self.expr()
            return ('ternary', e, then, els)
        return e
    def or_(self):
        l = self.and_()
        while self.peek().type == 'EITHER': self.next(); l = ('or', l, self.and_())
        return l
    def and_(self):
        l = self.not_()
        while self.peek().type == 'WITH': self.next(); l = ('and', l, self.not_())
        return l
    def not_(self):
        if self.peek().type == 'NEVER': self.next(); return ('not', self.not_())
        return self.in_()
    def in_(self):
        l = self.bit_or()
        while self.peek().type == 'IN':
            self.next(); l = ('in', l, self.bit_or())
        return l
    def bit_or(self):
        l = self.bit_xor()
        while self.peek().type == 'PIPE':
            self.next(); l = ('|', l, self.bit_xor())
        return l
    def bit_xor(self):
        l = self.bit_and()
        while self.peek().type == 'CARET':
            self.next(); l = ('^', l, self.bit_and())
        return l
    def bit_and(self):
        l = self.shift()
        while self.peek().type == 'AMP':
            self.next(); l = ('&', l, self.shift())
        return l
    def shift(self):
        l = self.cmp()
        while self.peek().type in ('SHL','SHR'):
            op = self.next().type; l = (op, l, self.cmp())
        return l
    def cmp(self):
        l = self.add()
        while self.peek().type in ('==','!=','<','>','<=','>='):
            op = self.next().type; l = (op, l, self.add())
        return l
    def add(self):
        l = self.mul()
        while self.peek().type in ('+','-'): op = self.next().type; l = (op, l, self.mul())
        return l
    def mul(self):
        l = self.unary()
        while self.peek().type in ('*','/','%'): op = self.next().type; l = (op, l, self.unary())
        return l
    def unary(self):
        if self.peek().type == '-': self.next(); return ('neg', self.unary())
        if self.peek().type == 'TILDE': self.next(); return ('bitnot', self.unary())
        if self.peek().type == 'AMP':
            self.next()
            t = self.next()
            if t.type != 'IDENT':
                raise CatError("& chi ho tro ten bien", t.line)
            return ('addr', ('var', t.value))
        if self.peek().type == '*':
            self.next()
            return ('deref', self.unary())
        return self.postfix()
    def postfix(self):
        e = self.primary()
        while True:
            if self.peek().type == '(':
                self.next(); args = []
                if self.peek().type != ')':
                    args.append(self.expr())
                    while self.peek().type == ',': self.next(); args.append(self.expr())
                self.expect(')')
                if e[0] == 'var': e = ('call', e[1], args)
                elif e[0] == 'dot': e = ('method_call', e[1], e[2], args)
                else: raise CatError("Khong goi duoc")
            elif self.peek().type == '[':
                self.next()
                if self.peek().type == ':':
                    self.next(); high = None
                    if self.peek().type != ']': high = self.expr()
                    self.expect(']'); e = ('slice', e, None, high)
                else:
                    first = self.expr()
                    if self.peek().type == ':':
                        self.next(); high = None
                        if self.peek().type != ']': high = self.expr()
                        self.expect(']'); e = ('slice', e, first, high)
                    else:
                        self.expect(']'); e = ('index', e, first)
            elif self.peek().type == '.':
                self.next(); name = self.expect('IDENT').value
                e = ('dot', e, name)
            else: break
        return e
    def primary(self):
        t = self.next()
        if t.type == 'NUMBER': return ('num', t.value)
        if t.type == 'STRING': return ('str', t.value)
        if t.type == 'NOD': return ('bool', True)
        if t.type == 'SHAKE': return ('bool', False)
        if t.type == 'HUNGRY': return ('null',)
        if t.type == 'NULL': return ('num', 0)
        if t.type == 'PTR': return ('var', 'ptr')
        if t.type == 'CAST':
            self.expect('(')
            tn = self.expect('IDENT').value
            self.expect(',')
            v = self.expr()
            self.expect(')')
            return ('cast', tn, v)
        if t.type == 'SIZEOF':
            self.expect('(')
            if self.peek().type == 'IDENT' and self.peek(1).type == ')':
                nm = self.next().value; self.expect(')')
                return ('sizeof_type', nm)
            e = self.expr(); self.expect(')')
            return ('sizeof', e)
        if t.type == 'ASM':
            self.expect('(')
            s = self.expect('STRING').value
            self.expect(')')
            return ('asm', s)
        if t.type == 'ME': return ('var', 'me')
        if t.type == 'IDENT': return ('var', t.value)
        if t.type == 'MATCH': return ('var', 'match')
        if t.type == 'KIT':
            self.expect('(')
            params = []
            if self.peek().type != ')':
                params.append(self.expect('IDENT').value)
                while self.peek().type == ',': self.next(); params.append(self.expect('IDENT').value)
            self.expect(')'); self.expect('ARROW')
            body = self.expr()
            return ('lambda', params, body)
        if t.type == '(':
            e = self.expr(); self.expect(')'); return e
        if t.type == '[':
            elems = []
            if self.peek().type != ']':
                elems.append(self.expr())
                while self.peek().type == ',': self.next(); elems.append(self.expr())
            self.expect(']'); return ('list', elems)
        if t.type == '{':
            pairs = []
            if self.peek().type != '}':
                key = self.expr(); self.expect(':'); val = self.expr()
                pairs.append((key, val))
                while self.peek().type == ',':
                    self.next()
                    if self.peek().type == '}': break
                    key = self.expr(); self.expect(':'); val = self.expr()
                    pairs.append((key, val))
            self.expect('}'); return ('dict', pairs)
        raise CatError(f"Khong hieu '{t.value or t.type}'", t.line)

class Env:
    def __init__(self, parent=None): self.vars, self.parent = {}, parent
    def get(self, n):
        if n in self.vars: return self.vars[n]
        if self.parent: return self.parent.get(n)
        raise CatError(f"Bien chua khai bao: '{n}'")
    def define(self, n, v): self.vars[n] = v
    def set(self, n, v):
        e = self
        while e:
            if n in e.vars: e.vars[n] = v; return
            e = e.parent
        self.vars[n] = v

class ClassObj:
    def __init__(self, name, parent, fields, methods, env):
        self.name=name; self.parent=parent
        self.fields=fields; self.methods=methods; self.env=env
class Instance:
    def __init__(self, cls):
        self.cls = cls; self.data = {}
        for f in cls.fields: self.data[f] = None
class EnumObj:
    def __init__(self, name, members):
        self.name = name; self.members = members
        self.values = {m: f"{name}.{m}" for m in members}

class Ptr:
    def __init__(self, env, name):
        self.env = env
        self.name = name
    def get(self):
        return self.env.get(self.name)
    def set(self, value):
        e = self.env
        while e:
            if self.name in e.vars:
                e.vars[self.name] = value
                return
            e = e.parent
        raise CatError(f"Bien chua khai bao: '{self.name}'")


class ReturnEx(Exception):
    def __init__(self, v): self.v = v
class StopEx(Exception): pass
class SkipEx(Exception): pass

class Runtime:
    def __init__(self, timeout=5.0):
        self.start=time.time(); self.timeout=timeout
        self.depth=0; self.max_depth=500
        self.read_input=None
    def tick(self):
        if time.time() - self.start > self.timeout:
            raise CatError(f"Chay qua {self.timeout}s")

def make_builtins():
    return {
        'tail': lambda x: len(x) if x is not None else 0,
        'puff': lambda s: str(s).upper(),
        'melt': lambda s: str(s).lower(),
        'nip': lambda s, a, b: s[int(a):int(b)],
        'bolt': lambda x: abs(x),
        'kitten': lambda a, b: min(a, b),
        'lion': lambda a, b: max(a, b),
        'scratch': lambda x: math.sqrt(x),
        'flop': lambda x: math.floor(x),
        'perch': lambda x: math.ceil(x),
        'say': lambda x: str(x),
        'tally': lambda x: int(x),
        'drip': lambda x: float(x),
        'collar': lambda d: list(d.keys()),
        'kits': lambda d: list(d.values()),
        'seek': lambda d, k: k in d,
        'shred': lambda s, sep: str(s).split(sep),
        'weave': lambda arr, sep: sep.join(str(x) for x in arr),
        'swap': lambda s, a, b: str(s).replace(a, b),
        'lick': lambda s: str(s).strip(),
        'hunt': lambda s, sub: sub in s,
        'stash': lambda a, v: (a.append(v), a)[1],
        'snatch': lambda a: a.pop() if a else (_ for _ in ()).throw(CatError("Rong")),
        'line': lambda a: sorted(a),
        'flip': lambda a: list(reversed(a)),
        'head': lambda a: a[0] if a else (_ for _ in ()).throw(CatError("Rong")),
        'rear': lambda a: a[-1] if a else (_ for _ in ()).throw(CatError("Rong")),
        'pile': lambda a: sum(a) if a else 0,
        'walk': lambda a, b=None, s=1: list(range(int(a))) if b is None else list(range(int(a), int(b), int(s))),
        'chase': lambda arr, f: [f(x) for x in arr],
        'sift': lambda arr, f: [x for x in arr if f(x)],
        'curl': lambda arr, f, i: __import__('functools').reduce(f, arr, i),
        'sway': lambda x: math.sin(x),
        'wave': lambda x: math.cos(x),
        'slant': lambda x: math.tan(x),
        'grow': lambda x: math.log(x),
        'bound': lambda a, b: a ** b,
        'wander': lambda: _random.random(),
        'dice': lambda a, b: _random.randint(int(a), int(b)),
        'match': _regex_match,
        'find_all': _regex_find_all,
        'replace_all': _regex_replace_all,
        'log2': lambda x: math.log2(x),
        'log10': lambda x: math.log10(x),
        'asin': lambda x: math.asin(x),
        'acos': lambda x: math.acos(x),
        'atan': lambda x: math.atan(x),
        'atan2': lambda y, x: math.atan2(y, x),
        'sinh': lambda x: math.sinh(x),
        'cosh': lambda x: math.cosh(x),
        'tanh': lambda x: math.tanh(x),
        'hypot': lambda a, b: math.hypot(a, b),
        'degrees': lambda x: math.degrees(x),
        'radians': lambda x: math.radians(x),
        'pi': 3.14159265358979,
        'e': 2.718281828459045,
        'pad_left': lambda s, n, c=' ': str(s).rjust(int(n), c),
        'pad_right': lambda s, n, c=' ': str(s).ljust(int(n), c),
        'substring': lambda s, a, b=None: str(s)[int(a):int(b) if b is not None else None],
        'char_code': lambda c: ord(str(c)[0]),
        'char_from': lambda n: chr(int(n)),
        'repeat': lambda s, n: str(s) * int(n),
        'reverse_str': lambda s: str(s)[::-1],
        'is_digit': lambda s: str(s).isdigit(),
        'is_alpha': lambda s: str(s).isalpha(),
        'read_file': _read_file,
        'write_file': _write_file,
        'append_file': _append_file,
        'exists': lambda p: os.path.exists(str(p)),
        'is_file': lambda p: os.path.isfile(str(p)),
        'is_dir': lambda p: os.path.isdir(str(p)),
        'list_dir': lambda p='.': sorted(os.listdir(str(p))),
        'remove_file': _remove_file,
        'make_dir': lambda p: (os.makedirs(str(p), exist_ok=True), True)[1],
        'read_lines': _read_lines,
        'write_lines': _write_lines,
        'env': lambda k: os.environ.get(str(k), ''),
        'cmd_args': lambda: sys.argv[1:],
        'cwd': lambda: os.getcwd(),
        'now': lambda: time.time(),
        'sleep': lambda t: (time.sleep(float(t)), True)[1],
        'timestamp': lambda: int(time.time()),
        'to_set': lambda x: list(set(x)),
        'union': lambda a, b: list(set(a) | set(b)),
        'intersect': lambda a, b: list(set(a) & set(b)),
        'difference': lambda a, b: list(set(a) - set(b)),
        'unique': lambda a: list(dict.fromkeys(a)),
        'cpp': _cpp_call,
        'spawn': _spawn,
        'wait_all': lambda: _wait_all() or True,
    
        # ═══ Stdlib extended (v1.0) ═══
        'clamp': lambda x, lo, hi: max(lo, min(hi, x)),
        'sign': lambda x: (1 if x > 0 else (-1 if x < 0 else 0)),
        'lerp': lambda a, b, t: a + (b - a) * t,
        'gcd': lambda a, b: __import__('math').gcd(int(a), int(b)),
        'lcm': lambda a, b: abs(int(a) * int(b)) // __import__('math').gcd(int(a), int(b)) if a and b else 0,
        'factorial': lambda n: __import__('math').factorial(int(n)),
        'is_prime': lambda n: (int(n) > 1) and all(int(n) % i for i in range(2, int(int(n)**0.5) + 1)),
        'round_to': lambda x, n: round(float(x), int(n)),
        'square': lambda x: x * x,
        'cube': lambda x: x * x * x,
        'format_str': lambda tmpl, *args: str(tmpl).format(*args),
        'title_case': lambda s: str(s).title(),
        'capitalize_str': lambda s: str(s).capitalize(),
        'count_sub': lambda s, sub: str(s).count(str(sub)),
        'starts_with': lambda s, p: str(s).startswith(str(p)),
        'ends_with': lambda s, p: str(s).endswith(str(p)),
        'split_lines': lambda s: str(s).split(chr(10)),
        'chars': lambda s: list(str(s)),
        'is_empty': lambda s: len(s) == 0,
        'join_str': lambda lst, sep: str(sep).join(str(x) for x in lst),
        'zip_lists': lambda a, b: [[x, y] for x, y in zip(a, b)],
        'enumerate_list': lambda a: [[i, v] for i, v in enumerate(a)],
        'flatten': lambda a: [x for sub in a for x in (sub if isinstance(sub, list) else [sub])],
        'chunk': lambda a, n: [a[i:i+int(n)] for i in range(0, len(a), int(n))],
        'range_list': lambda n: list(range(int(n))),
        'range_from_to': lambda a, b: list(range(int(a), int(b))),
        'insert_at': lambda a, i, v: (a.insert(int(i), v), a)[1],
        'remove_at': lambda a, i: a.pop(int(i)) if 0 <= int(i) < len(a) else None,
        'index_of': lambda a, v: a.index(v) if v in a else -1,
        'clear_list': lambda a: (a.clear(), a)[1],
        'merge_dict': lambda a, b: {**a, **b},
        'invert_dict': lambda d: {v: k for k, v in d.items()},
        'from_pairs': lambda lst: {k: v for k, v in lst},
        'dict_get': lambda d, k, default=None: d.get(k, default),
        'dict_has': lambda d, k: k in d,
        'json_parse': lambda s: __import__('json').loads(str(s)),
        'json_stringify': lambda v: __import__('json').dumps(v, ensure_ascii=False),
        'json_pretty': lambda v: __import__('json').dumps(v, ensure_ascii=False, indent=2),
        'path_join': lambda a, b: __import__('os').path.join(str(a), str(b)),
        'path_basename': lambda p: __import__('os').path.basename(str(p)),
        'path_dirname': lambda p: __import__('os').path.dirname(str(p)),
        'path_ext': lambda p: __import__('os').path.splitext(str(p))[1],
        'format_time': lambda ts, fmt='%Y-%m-%d %H:%M:%S': __import__('datetime').datetime.fromtimestamp(float(ts)).strftime(str(fmt)),
        'now_ms': lambda: int(__import__('time').time() * 1000),
        'sleep_ms': lambda ms: (__import__('time').sleep(float(ms) / 1000.0), True)[1],
        'chdir': lambda p: (__import__('os').chdir(str(p)), True)[1],
        'shell': lambda cmd: __import__('subprocess').run(str(cmd), shell=True, capture_output=True, text=True).stdout,
        'getenv': lambda k, default='': __import__('os').environ.get(str(k), default),
        'setenv': lambda k, v: __import__('os').environ.__setitem__(str(k), str(v)),
        'assert_eq': lambda a, b: (a == b) or (_ for _ in ()).throw(Exception(f'assert_eq: {a!r} != {b!r}')),
        'assert_true': lambda x: bool(x) or (_ for _ in ()).throw(Exception(f'assert_true: {x!r} is falsy')),
        'assert_false': lambda x: (not x) or (_ for _ in ()).throw(Exception(f'assert_false: {x!r} is truthy')),
        'type_of': lambda x: type(x).__name__,
        'is_null': lambda x: x is None,
        'copy_shallow': lambda x: x.copy() if hasattr(x, 'copy') else x,
        'to_str': lambda x: str(x),
        'to_int': lambda x: int(x),
        'to_float': lambda x: float(x),

        # ═══ Phase 12b: HTTP ═══
        'http_get': _http_get,
        'http_post': _http_post,
        'http_json': _http_json,

        # ═══ Phase 12b: File ops nang cao ═══
        'glob': _glob,
        'walk_dir': _walk,
        'copy_file': _copy_file,
        'move_file': _move_file,
        'mkdir_p': _mkdir_p,
        'file_size': lambda p: os.path.getsize(str(p)),
        'file_mtime': lambda p: os.path.getmtime(str(p)),
        'basename': lambda p: os.path.basename(str(p)),
        'dirname': lambda p: os.path.dirname(str(p)),
        'ext': lambda p: os.path.splitext(str(p))[1],
        'abs_path': lambda p: os.path.abspath(str(p)),

        # ═══ Phase 12b: Process ═══
        'sh': _sh,
        'sh_code': _sh_code,
    }


# ═══ Phase 12b: HTTP helpers ═══
def _http_get(url, headers=None):
    import urllib.request
    req = urllib.request.Request(str(url), headers=headers or {})
    req.add_header('User-Agent', 'Cat++/2.0')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        raise CatError(f'http_get failed: {e}')

def _http_post(url, data='', headers=None):
    import urllib.request
    body = data.encode('utf-8') if isinstance(data, str) else data
    req = urllib.request.Request(str(url), data=body, method='POST')
    req.add_header('User-Agent', 'Cat++/2.0')
    if headers:
        for k, v in headers.items():
            req.add_header(str(k), str(v))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        raise CatError(f'http_post failed: {e}')

def _http_json(url, headers=None):
    import json as _json
    text = _http_get(url, headers=headers)
    try:
        return _json.loads(text)
    except Exception as e:
        raise CatError(f'http_json parse failed: {e}')

# ═══ Phase 12b: File ops ═══
def _glob(pattern):
    import glob as _g
    return sorted(_g.glob(str(pattern), recursive=True))

def _walk(path):
    result = []
    for root, dirs, files in os.walk(str(path)):
        for f in sorted(files):
            result.append(os.path.join(root, f))
    return result

def _copy_file(src, dst):
    import shutil as _s
    _s.copy2(str(src), str(dst))
    return True

def _move_file(src, dst):
    import shutil as _s
    _s.move(str(src), str(dst))
    return True

def _mkdir_p(path):
    os.makedirs(str(path), exist_ok=True)
    return True

# ═══ Phase 12b: Process ═══
def _sh(cmd):
    import subprocess as _sp
    try:
        r = _sp.run(str(cmd), shell=True, capture_output=True, text=True, timeout=300)
        return r.stdout
    except Exception as e:
        raise CatError(f'sh failed: {e}')

def _sh_code(cmd):
    import subprocess as _sp
    try:
        r = _sp.run(str(cmd), shell=True, capture_output=True, text=True, timeout=300)
        return r.returncode
    except Exception as e:
        raise CatError(f'sh_code failed: {e}')

_threads = []

def _spawn(fn, *args):
    import threading
    def wrapper():
        try: fn(*args)
        except Exception as e: print(f'[spawn] {e}')
    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    _threads.append(t)
    return len(_threads) - 1

def _wait_all():
    for t in _threads: t.join()
    _threads.clear()

def _read_file(path):
    with open(str(path), encoding='utf-8') as f: return f.read()

def _write_file(path, content):
    with open(str(path), 'w', encoding='utf-8') as f: f.write(str(content))
    return True

def _append_file(path, content):
    with open(str(path), 'a', encoding='utf-8') as f: f.write(str(content))
    return True

def _remove_file(path):
    p = str(path)
    if os.path.isfile(p): os.remove(p)
    elif os.path.isdir(p): os.rmdir(p)
    return True

def _read_lines(path):
    with open(str(path), encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f.readlines()]

def _write_lines(path, lines):
    with open(str(path), 'w', encoding='utf-8') as f:
        for line in lines: f.write(str(line) + '\n')
    return True

def _cpp_call(lib, func, *args):
    import ctypes
    try:
        dll = ctypes.CDLL(lib)
    except OSError:
        try:
            dll = ctypes.CDLL('lib' + str(lib) + '.so')
        except OSError as e:
            raise CatError(f'Không load được {lib}: {e}')
    fn = getattr(dll, str(func), None)
    if fn is None:
        raise CatError(f'{lib} không có hàm {func}')
    fn.restype = ctypes.c_double
    return fn(*[ctypes.c_double(float(a)) for a in args])

import re as _re_mod

def _regex_match(pattern, s):
    return _re_mod.search(pattern, str(s)) is not None

def _regex_find_all(pattern, s):
    return _re_mod.findall(pattern, str(s))

def _regex_replace_all(pattern, s, sub):
    return _re_mod.sub(pattern, sub, str(s))

def interp_str(s, env):
    if '{' not in s: return s
    result = ''; i = 0
    while i < len(s):
        if s[i] == '{':
            j = s.find('}', i)
            if j == -1: result += s[i]; i += 1; continue
            expr = s[i+1:j].strip()
            try: result += fmt(env.get(expr))
            except Exception: result += s[i:j+1]
            i = j + 1
        else: result += s[i]; i += 1
    return result

# ============ STRING METHODS ============
def str_method(obj, name, args):
    s = str(obj)
    if name == 'upper': return s.upper()
    if name == 'lower': return s.lower()
    if name == 'trim': return s.strip()
    if name == 'split': return s.split(args[0] if args else ' ')
    if name == 'replace': return s.replace(args[0], args[1])
    if name == 'starts_with': return s.startswith(args[0])
    if name == 'ends_with': return s.endswith(args[0])
    if name == 'contains': return args[0] in s
    if name == 'index_of':
        idx = s.find(args[0]); return idx if idx >= 0 else -1
    if name == 'repeat': return s * int(args[0])
    if name == 'length' or name == 'len': return len(s)
    if name == 'char_at': return s[int(args[0])]
    if name == 'to_upper': return s.upper()
    if name == 'to_lower': return s.lower()
    raise CatError(f"Chuoi khong co method '{name}'")

# ============ LIST METHODS ============
def list_method(obj, name, args):
    if name == 'push': obj.append(args[0]); return obj
    if name == 'pop':
        if not obj: raise CatError("Danh sach rong")
        return obj.pop()
    if name == 'sort': obj.sort(); return obj
    if name == 'reverse': obj.reverse(); return obj
    if name == 'find':
        for x in obj:
            if x == args[0]: return x
        return None
    if name == 'index_of':
        try: return obj.index(args[0])
        except ValueError: return -1
    if name == 'contains': return args[0] in obj
    if name == 'length' or name == 'len': return len(obj)
    if name == 'first': return obj[0] if obj else None
    if name == 'last': return obj[-1] if obj else None
    if name == 'remove':
        if args[0] in obj: obj.remove(args[0])
        return obj
    if name == 'clear': obj.clear(); return obj
    if name == 'insert': obj.insert(int(args[0]), args[1]); return obj
    if name == 'count': return obj.count(args[0])
    if name == 'sum': return sum(obj)
    raise CatError(f"Danh sach khong co method '{name}'")

# ============ DICT METHODS ============
def dict_method(obj, name, args):
    if name == 'get': return obj.get(args[0])
    if name == 'keys': return list(obj.keys())
    if name == 'values': return list(obj.values())
    if name == 'items': return [[k, v] for k, v in obj.items()]
    if name == 'has': return args[0] in obj
    if name == 'set': obj[args[0]] = args[1]; return obj
    if name == 'remove':
        if args[0] in obj: del obj[args[0]]
        return obj
    if name == 'size' or name == 'len': return len(obj)
    if name == 'clear': obj.clear(); return obj
    raise CatError(f"Dict khong co method '{name}'")

def eval_(n, env, out, rt):
    t = n[0]
    if t == 'num': return n[1]
    if t == 'str': return interp_str(n[1], env)
    if t == 'bool': return n[1]
    if t == 'null': return None
    if t == 'var': return env.get(n[1])
    if t == 'list': return [eval_(e, env, out, rt) for e in n[1]]
    if t == 'dict':
        d = {}
        for k, v in n[1]: d[eval_(k, env, out, rt)] = eval_(v, env, out, rt)
        return d
    if t == 'lambda':
        params, body = n[1], n[2]
        def fn(*args, _p=params, _b=body, _e=env, _rt=rt):
            local = Env(_e)
            for p, a in zip(_p, args): local.define(p, a)
            return eval_(_b, local, out, _rt)
        return fn
    if t == 'index':
        obj = eval_(n[1], env, out, rt); idx = eval_(n[2], env, out, rt)
        try:
            if isinstance(idx, float): idx = int(idx)
            if isinstance(obj, dict): return obj.get(idx)
            return obj[idx]
        except (IndexError, KeyError, TypeError): raise CatError(f"Truy cap khong hop le")
    if t == 'slice':
        obj = eval_(n[1], env, out, rt)
        lo = eval_(n[2], env, out, rt) if n[2] else None
        hi = eval_(n[3], env, out, rt) if n[3] else None
        if isinstance(obj, (str, list)):
            a = int(lo) if lo is not None else 0
            b = int(hi) if hi is not None else len(obj)
            return obj[a:b]
        raise CatError("Nip chi dung cho chuoi hoac danh sach")
    if t == 'dot':
        obj = eval_(n[1], env, out, rt); name = n[2]
        if isinstance(obj, dict): return obj.get(name)
        if isinstance(obj, Instance):
            if name in obj.data: return obj.data[name]
            cls = obj.cls
            while cls:
                if name in cls.methods: return ('bound', obj, name)
                cls = cls.parent
            raise CatError(f"Instance khong co '{name}'")
        if isinstance(obj, EnumObj):
            if name in obj.members: return obj.values[name]
            raise CatError(f"Litter khong co '{name}'")
        raise CatError(f"Khong truy cap duoc '.{name}'")
    if t == 'ternary':
        cond = eval_(n[1], env, out, rt)
        return eval_(n[2], env, out, rt) if cond else eval_(n[3], env, out, rt)
    if t == 'coalesce':
        left = eval_(n[1], env, out, rt)
        return left if left is not None else eval_(n[2], env, out, rt)
    if t == 'neg': return -eval_(n[1], env, out, rt)
    if t == 'not': return not eval_(n[1], env, out, rt)
    if t == 'and': return eval_(n[1], env, out, rt) and eval_(n[2], env, out, rt)
    if t == 'or':  return eval_(n[1], env, out, rt) or  eval_(n[2], env, out, rt)
    if t == 'in':
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        try:
            if isinstance(r, dict): return l in r
            return l in r
        except TypeError:
            return False
    if t == 'call':
        name = n[1]; fn = env.get(name)
        args = [eval_(a, env, out, rt) for a in n[2]]
        if isinstance(fn, ClassObj): return make_instance(fn, args, out, rt)
        if not callable(fn): raise CatError(f"'{name}' khong phai ham")
        try: return fn(*args)
        except CatError: raise
        except Exception as e: raise CatError(str(e))
    if t == 'method_call':
        obj = eval_(n[1], env, out, rt); name = n[2]
        args = [eval_(a, env, out, rt) for a in n[3]]
        if isinstance(obj, Instance): return call_method(obj, name, args, out, rt)
        if isinstance(obj, str): return str_method(obj, name, args)
        if isinstance(obj, list): return list_method(obj, name, args)
        if isinstance(obj, dict): return dict_method(obj, name, args)
        raise CatError(f"Khong goi duoc '{name}'")
    if t in ('&','|','^','<<','>>','SHL','SHR'):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        try: a = int(l); b = int(r)
        except (ValueError, TypeError): raise CatError("Bit op yeu cau so nguyen")
        return {'&': a&b, '|': a|b, '^': a^b,
                '<<': a<<b, '>>': a>>b,
                'SHL': a<<b, 'SHR': a>>b}[t]
    if t == 'bitnot':
        v = eval_(n[1], env, out, rt)
        try: return ~int(v)
        except (ValueError, TypeError): raise CatError("~ yeu cau so nguyen")
    if t == 'addr':
        inner = n[1]
        if inner[0] != 'var':
            raise CatError("& chi ho tro bien")
        return Ptr(env, inner[1])
    if t == 'deref':
        p = eval_(n[1], env, out, rt)
        if not isinstance(p, Ptr):
            raise CatError("Khong phai con tro")
        return p.get()
    if t == 'cast': return do_cast(n[1], eval_(n[2], env, out, rt))
    if t == 'sizeof': return size_of_value(eval_(n[1], env, out, rt))
    if t == 'sizeof_type': return size_of_type(n[1])
    if t == 'asm': return None
    if t in ('+','-','*','/','%','==','!=','<','>','<=','>='):
        l = eval_(n[1], env, out, rt); r = eval_(n[2], env, out, rt)
        if t == '+':
            if isinstance(l, str) or isinstance(r, str): return str(l) + str(r)
            if isinstance(l, list) and isinstance(r, list): return l + r
            return l + r
        if t == '/' and r == 0: raise CatError("Chia cho 0")
        return {'-': lambda:l-r, '*': lambda:l*r, '/': lambda:l/r, '%': lambda:l%r,
                '==': lambda:l==r, '!=': lambda:l!=r, '<': lambda:l<r,
                '>': lambda:l>r, '<=': lambda:l<=r, '>=': lambda:l>=r}[t]()
    raise CatError(f"Khong hieu bieu thuc: {t}")

def make_instance(cls, args, out, rt):
    inst = Instance(cls)
    # Tim 'new' trong parent chain
    c = cls
    new_method = None
    while c:
        if 'new' in c.methods:
            new_method = c.methods['new']
            break
        c = c.parent
    if new_method:
        params, body = new_method
        local = Env(cls.env); local.define('me', inst)
        for p, a in zip(params, args): local.define(p, a)
        try:
            for s in body: exec_(s, local, out, rt)
        except ReturnEx: pass
    return inst

TYPE_SIZES = {'i8':1,'u8':1,'i16':2,'u16':2,'i32':4,'u32':4,
              'i64':8,'u64':8,'int':8,'float':8,'bool':1,'ptr':8,
              'char':1,'byte':1,'str':8}

def do_cast(t, v):
    t = t.lower()
    if t in ('i8','i16','i32','i64','int','u8','u16','u32','u64','byte','char'):
        try: return int(v) if v is not None else 0
        except: return 0
    if t == 'float':
        try: return float(v) if v is not None else 0.0
        except: return 0.0
    if t == 'bool': return bool(v)
    if t == 'str':
        if isinstance(v, float) and v == int(v): return str(int(v))
        return str(v)
    if t == 'ptr':
        try: return int(v) if v is not None else 0
        except: return 0
    return v

def size_of_value(v):
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 8
    if isinstance(v, float): return 8
    if isinstance(v, str): return len(v)
    if isinstance(v, list): return len(v) * 8
    if isinstance(v, dict): return len(v) * 8
    return 8

def size_of_type(n):
    return TYPE_SIZES.get(n.lower(), 8)

def call_method(inst, name, args, out, rt):
    cls = inst.cls
    while cls:
        if name in cls.methods:
            params, body = cls.methods[name]
            local = Env(cls.env); local.define('me', inst)
            for p, a in zip(params, args): local.define(p, a)
            try:
                for s in body: exec_(s, local, out, rt)
            except ReturnEx as r: return r.v
            return None
        cls = cls.parent
    raise CatError(f"Method '{name}' khong ton tai")

def get_target_value(target, env, out, rt):
    """Đọc giá trị hiện tại của target để tính toán += -= ..."""
    if target[0] == 'deref':
        p = eval_(target[1], env, out, rt)
        if not isinstance(p, Ptr):
            raise CatError("Khong phai con tro")
        return p.get()
    if target[0] == 'var':
        return env.get(target[1])
    elif target[0] == 'index':
        obj = eval_(target[1], env, out, rt)
        idx = eval_(target[2], env, out, rt)
        if isinstance(idx, float): idx = int(idx)
        return obj[idx]
    elif target[0] == 'dot':
        obj = eval_(target[1], env, out, rt)
        name = target[2]
        if isinstance(obj, dict): return obj.get(name)
        if isinstance(obj, Instance): return obj.data.get(name)
    raise CatError("Target khong hop le")

def assign_to(target, value, env, out, rt):
    if target[0] == 'deref':
        p = eval_(target[1], env, out, rt)
        if not isinstance(p, Ptr):
            raise CatError("Khong phai con tro")
        p.set(value)
        return
    if target[0] == 'var': env.set(target[1], value)
    elif target[0] == 'index':
        obj = eval_(target[1], env, out, rt)
        idx = eval_(target[2], env, out, rt)
        if isinstance(idx, float): idx = int(idx)
        try: obj[idx] = value
        except TypeError: raise CatError("Khong the gan")
    elif target[0] == 'dot':
        obj = eval_(target[1], env, out, rt); name = target[2]
        if isinstance(obj, dict): obj[name] = value
        elif isinstance(obj, Instance): obj.data[name] = value
        else: raise CatError(f"Khong the gan '{name}'")
    else: raise CatError("Target khong hop le")

def exec_(s, env, out, rt):
    rt.tick()
    t = s[0]
    line = s[-1] if isinstance(s[-1], int) else 0
    try:
        if t == 'let': env.define(s[1], eval_(s[2], env, out, rt))
        elif t == 'assign': env.set(s[1], eval_(s[2], env, out, rt))
        elif t == 'assign_target': assign_to(s[1], eval_(s[2], env, out, rt), env, out, rt)
        elif t == 'op_assign':
            target, op, rhs = s[1], s[2], s[3]
            cur = get_target_value(target, env, out, rt)
            rv = eval_(rhs, env, out, rt)
            if op == '+=':
                result = cur + rv
            elif op == '-=':
                result = cur - rv
            elif op == '*=':
                result = cur * rv
            elif op == '/=':
                if rv == 0: raise CatError("Chia cho 0")
                result = cur / rv
            elif op == '%=':
                result = cur % rv
            else:
                raise CatError(f"Toan tu khong hop le '{op}'")
            assign_to(target, result, env, out, rt)
        elif t == 'expr': eval_(s[1], env, out, rt)
        elif t == 'print': out.append(fmt(eval_(s[1], env, out, rt)))
        elif t == 'listen':
            val = rt.read_input() if rt.read_input else ''
            try: val = float(val)
            except: pass
            env.define(s[1], val)
        elif t == 'return': raise ReturnEx(eval_(s[1], env, out, rt))
        elif t == 'if':
            if eval_(s[1], env, out, rt):
                for x in s[2]: exec_(x, env, out, rt)
            elif s[3]:
                for x in s[3]: exec_(x, env, out, rt)
        elif t == 'while':
            count = 0
            while eval_(s[1], env, out, rt):
                count += 1
                if count > 1_000_000: raise CatError("Knead qua 1 trieu lan", line)
                try:
                    for x in s[2]: exec_(x, env, out, rt)
                except StopEx: break
                except SkipEx: continue
        elif t == 'each':
            for item in eval_(s[2], env, out, rt):
                local = Env(env); local.define(s[1], item)
                try:
                    for x in s[3]: exec_(x, local, out, rt)
                except StopEx: break
                except SkipEx: continue
        elif t == 'stop': raise StopEx()
        elif t == 'skip': raise SkipEx()
        elif t == 'try':
            body, errname, handler = s[1], s[2], s[3]
            try:
                for x in body: exec_(x, env, out, rt)
            except (ReturnEx, StopEx, SkipEx): raise
            except CatError as e:
                if handler is None: pass
                else:
                    local = Env(env)
                    if errname: local.define(errname, str(e))
                    for x in handler: exec_(x, local, out, rt)
        elif t == 'func':
            name, params, defaults, body = s[1], s[2], s[3], s[4]
            def fn(*args, _p=params, _d=defaults, _b=body, _e=env, _rt=rt, _o=out):
                _rt.depth += 1
                if _rt.depth > _rt.max_depth:
                    _rt.depth -= 1
                    raise CatError(f"Meo qua sau (>{_rt.max_depth})")
                local = Env(_e)
                for i, p in enumerate(_p):
                    if i < len(args):
                        local.define(p, args[i])
                    elif p in _d:
                        local.define(p, eval_(_d[p], _e, _o, _rt))
                    else:
                        raise CatError(f"Thieu tham so '{p}'")
                try:
                    for x in _b: exec_(x, local, out, _rt)
                except ReturnEx as r:
                    _rt.depth -= 1; return r.v
                _rt.depth -= 1
                return None
            env.define(name, fn)
        elif t == 'struct':
            name, fields = s[1], s[2]
            env.define(name, ClassObj(name, None, fields, {}, env))
        elif t == 'class':
            name, parent, fields, methods = s[1], s[2], s[3], s[4]
            parent_obj = env.get(parent) if parent else None
            env.define(name, ClassObj(name, parent_obj, fields, methods, env))
        elif t == 'enum':
            env.define(s[1], EnumObj(s[1], s[2]))
        elif t == 'match':
            subject = eval_(s[1], env, out, rt)
            matched = False
            for pat, body in s[2]:
                if pat[0] == 'var' and pat[1] == '_':
                    matched = True
                else:
                    val = eval_(pat, env, out, rt)
                    if val == subject: matched = True
                if matched:
                    for x in body: exec_(x, env, out, rt)
                    break
        elif t == 'use':
            fname = s[1]
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(base_dir, 'examples', fname),
                os.path.join(base_dir, fname), fname
            ]
            loaded = False
            for path in candidates:
                if os.path.exists(path):
                    with open(path, encoding='utf-8') as fh:
                        lib_code = fh.read()
                    lib_ast = Parser(tokenize(lib_code)).parse()
                    for stmt in lib_ast:
                        exec_(stmt, env, out, rt)
                    loaded = True
                    break
            if not loaded:
                raise CatError(f"Khong tim thay file '{fname}'")
    except CatError as e:
        if not e.line: e.line = line
        raise

def fmt(v):
    if v is True: return 'nod'
    if v is False: return 'shake'
    if v is None: return 'hungry'
    if isinstance(v, float) and v == int(v): return str(int(v))
    if isinstance(v, list): return '[' + ', '.join(fmt(x) for x in v) + ']'
    if isinstance(v, dict): return '{' + ', '.join(f'{fmt(k)}: {fmt(val)}' for k, val in v.items()) + '}'
    if isinstance(v, Instance): return f"<{v.cls.name} meow>"
    if isinstance(v, ClassObj): return f"<cat {v.name}>"
    if isinstance(v, EnumObj): return f"<litter {v.name}>"
    if callable(v): return '<purr>'
    if isinstance(v, Ptr): return f'<ptr {v.name}>'
    return str(v)

def run_catpp(code, timeout=5.0, read_input=None):
    ast = Parser(tokenize(code)).parse()
    env = Env()
    for k, v in make_builtins().items(): env.define(k, v)
    out = []
    rt = Runtime(timeout=timeout); rt.read_input = read_input
    for s in ast: exec_(s, env, out, rt)
    return '\n'.join(out)
