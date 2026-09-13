from dataclasses import dataclass
import time, math, random as _random

KEYWORDS = {'paw','meow','purr','give','hiss','tap','sit','leap','listen',
            'sniff','swat','knead','groom','of','nod','shake','hungry',
            'with','either','never','cat','me','kin','kit','litter','in',
            'match','case','use','in'}

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
                while j < len(line) and (line[j].isdigit() or line[j]=='.'): j += 1
                toks.append(Tok('NUMBER', float(line[i:j]), ln)); i = j; continue
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
            if two in ('+=','-=','*=','/=','%='):
                toks.append(Tok('OP_ASSIGN', two, ln)); i += 2; continue
            if two == '++': toks.append(Tok('INC', '++', ln)); i += 2; continue
            if two == '--': toks.append(Tok('DEC', '--', ln)); i += 2; continue
            if two == '=>': toks.append(Tok('ARROW', '=>', ln)); i += 2; continue
            if two in ('==','!=','<=','>='): toks.append(Tok(two, two, ln)); i += 2; continue
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
            if self.peek().type == '=':
                self.next(); e = self.expr(); self.expect('NEWLINE')
                return ('let', name, e, t.line)
            self.expect('NEWLINE'); return ('expr', ('var', name), t.line)
        if t.type == 'MEOW':
            self.next(); e = self.expr(); self.expect('NEWLINE'); return ('print', e, t.line)
        if t.type == 'LISTEN':
            self.next(); name = self.expect('IDENT').value
            self.expect('NEWLINE'); return ('listen', name, t.line)
        if t.type == 'PURR':
            self.next(); name = self.expect('IDENT').value; params = []
            while self.peek().type == 'IDENT': params.append(self.next().value)
            if self.peek().type == '(':
                self.next()
                if self.peek().type != ')':
                    params.append(self.expect('IDENT').value)
                    while self.peek().type == ',': self.next(); params.append(self.expect('IDENT').value)
                self.expect(')')
            body = self.block(); return ('func', name, params, body, t.line)
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
    def expr(self): return self.or_()
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
        l = self.cmp()
        while self.peek().type == 'IN':
            self.next(); l = ('in', l, self.cmp())
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
    }

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
    if 'new' in cls.methods:
        params, body = cls.methods['new']
        local = Env(cls.env); local.define('me', inst)
        for p, a in zip(params, args): local.define(p, a)
        try:
            for s in body: exec_(s, local, out, rt)
        except ReturnEx: pass
    return inst

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
            name, params, body = s[1], s[2], s[3]
            def fn(*args, _p=params, _b=body, _e=env, _rt=rt):
                _rt.depth += 1
                if _rt.depth > _rt.max_depth:
                    _rt.depth -= 1
                    raise CatError(f"Meo qua sau (>{_rt.max_depth})")
                local = Env(_e)
                for p, a in zip(_p, args): local.define(p, a)
                try:
                    for x in _b: exec_(x, local, out, _rt)
                except ReturnEx as r:
                    _rt.depth -= 1; return r.v
                _rt.depth -= 1
                return None
            env.define(name, fn)
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
            import os
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
    return str(v)

def run_catpp(code, timeout=5.0, read_input=None):
    ast = Parser(tokenize(code)).parse()
    env = Env()
    for k, v in make_builtins().items(): env.define(k, v)
    out = []
    rt = Runtime(timeout=timeout); rt.read_input = read_input
    for s in ast: exec_(s, env, out, rt)
    return '\n'.join(out)
