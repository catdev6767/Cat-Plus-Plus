"""Cat++ v3 Parser — C++ syntax + cat keywords."""
import sys
from tokenizer_v3 import tokenize, Token

class ParseError(Exception):
    def __init__(self, msg, line=0, col=0):
        super().__init__(msg)
        self.line, self.col = line, col


# ═══ C++ TYPE KEYWORDS ═══
TYPE_KEYWORDS = {'int', 'float', 'str', 'bool', 'void', 'char',
                 'long', 'short', 'double', 'unsigned', 'signed'}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    def peek(self, off=0):
        i = self.pos + off
        return self.toks[i] if i < len(self.toks) else self.toks[-1]

    def next(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def expect(self, tt):
        t = self.next()
        if t.type != tt:
            raise ParseError(f"Expected '{tt}', got '{t.type}' ({t.value!r})", t.line, t.col)
        return t

    def match(self, *types):
        if self.peek().type in types:
            return self.next()
        return None

    def at(self, *types):
        return self.peek().type in types

    # ═══ PROGRAM ═══
    def parse_program(self):
        stmts = []
        while not self.at('EOF'):
            s = self.parse_toplevel()
            if s: stmts.append(s)
        return ('program', stmts)

    def parse_toplevel(self):
        # #include directive
        if self.at('DIRECTIVE'):
            t = self.next()
            return ('directive', t.value)

        # purr <type> <name>(...) { ... }
        if self.at('PURR'):
            return self.parse_function()

        # cat <Name> { ... };
        if self.at('CAT'):
            return self.parse_class()

        # top-level statement
        return self.parse_stmt()

    # ═══ FUNCTION ═══
    def parse_function(self):
        self.expect('PURR')
        # Constructor: purr ClassName(args) { ... }
        if self.at('IDENT') and self.peek(1).type == '(':
            name_tok = self.next()
            self.expect('(')
            params = self.parse_params()
            self.expect(')')
            body = self.parse_block()
            return ('func', ('void', 0, None, None), name_tok.value, params, body)
        # Regular function: purr <type> name(args) { ... }
        ret_type = self.parse_type()
        name_tok = self.expect('IDENT')
        self.expect('(')
        params = self.parse_params()
        self.expect(')')
        body = self.parse_block()
        return ('func', ret_type, name_tok.value, params, body)

    def parse_params(self):
        params = []
        if not self.at(')'):
            while True:
                ptype = self.parse_type()
                pname = self.expect('IDENT').value
                params.append((ptype, pname))
                if not self.match(','):
                    break
        return params

    # ═══ CLASS ═══
    def parse_class(self):
        self.expect('CAT')
        name_tok = self.expect('IDENT')
        parent = None
        if self.match(':'):
            parent = self.expect('IDENT').value
        self.expect('{')
        members = []
        while not self.at('}', 'EOF'):
            if self.at('PURR'):
                members.append(self.parse_function())
            elif self.at('PAW'):
                members.append(self.parse_field())
            else:
                raise ParseError(f"Unexpected in class: {self.peek().type}", self.peek().line, self.peek().col)
        self.expect('}')
        self.match(';')
        return ('class', name_tok.value, parent, members)

    def parse_field(self):
        self.expect('PAW')
        ftype = self.parse_type()
        name = self.expect('IDENT').value
        self.expect(';')
        return ('field', ftype, name)

    # ═══ TYPE ═══
    def parse_type(self):
        # base type
        if self.at('INT', 'FLOAT', 'STR', 'BOOL', 'VOID', 'CHAR',
                   'LONG', 'SHORT', 'DOUBLE', 'UNSIGNED', 'SIGNED'):
            base = self.next().value
        else:
            base = self.expect('IDENT').value

        # pointer *
        ptr_depth = 0
        while self.match('*'):
            ptr_depth += 1

        # array [N] or []
        array_size = None
        if self.match('['):
            if not self.at(']'):
                size_tok = self.next()
                if size_tok.type == 'NUMBER':
                    array_size = int(size_tok.value)
                elif size_tok.type == 'IDENT':
                    # array of size known at runtime — for now support const only
                    array_size = 0
            self.expect(']')

        # generic <T>
        generic = None
        if self.at('<'):
            # Only treat as generic if next is IDENT and we're in type context
            nxt = self.peek(1)
            if nxt.type == 'IDENT' and self.peek(2).type == '>':
                self.next()  # <
                generic = self.expect('IDENT').value
                self.expect('>')

        return (base, ptr_depth, array_size, generic)

    # ═══ BLOCK ═══
    def parse_block(self):
        self.expect('{')
        stmts = []
        while not self.at('}', 'EOF'):
            stmts.append(self.parse_stmt())
        self.expect('}')
        return stmts

    # ═══ STATEMENTS ═══
    def parse_stmt(self):
        # { block }
        if self.at('{'):
            return ('block', self.parse_block())

        # paw <type> <name> = <expr> ;
        # paw <type> <name> ;
        if self.at('PAW'):
            return self.parse_var_decl()

        # meow(expr);
        if self.at('MEOW'):
            self.next()
            self.expect('(')
            expr = self.parse_expr()
            self.expect(')')
            self.expect(';')
            return ('meow', expr)

        # give expr;
        if self.at('GIVE'):
            self.next()
            if self.at(';'):
                self.next()
                return ('return', None)
            expr = self.parse_expr()
            self.expect(';')
            return ('return', expr)

        # for (init; cond; step) { }
        if self.at('FOR'):
            return self.parse_for()

        # sniff (cond) { } [swat { }]
        if self.at('SNIFF'):
            return self.parse_if()

        # knead (cond) { }
        if self.at('KNEAD'):
            return self.parse_while()

        # delete expr;
        if self.at('DELETE'):
            self.next()
            expr = self.parse_expr()
            self.expect(';')
            return ('delete', expr)

        # sit; leap;
        if self.at('SIT'):
            self.next(); self.expect(';')
            return ('break',)
        if self.at('LEAP'):
            self.next(); self.expect(';')
            return ('continue',)

        # expression statement: expr ;
        expr = self.parse_expr()
        self.expect(';')
        return ('expr_stmt', expr)

    def parse_var_decl(self):
        self.expect('PAW')
        vtype = self.parse_type()
        name = self.expect('IDENT').value
        # Array size after name: int arr[5]
        if self.at('['):
            self.next()
            size_expr = self.parse_expr()
            self.expect(']')
            base, ptr_depth, _, generic = vtype
            vtype = (base, ptr_depth, size_expr, generic)
        init = None
        if self.match('='):
            init = self.parse_expr()
        self.expect(';')
        return ('var_decl', vtype, name, init)

    def parse_for(self):
        self.expect('FOR')
        self.expect('(')
        # init: paw int i = 0 OR i = 0
        if self.at('PAW'):
            init = self.parse_var_decl()
        else:
            init_expr = self.parse_expr()
            self.expect(';')
            init = ('expr_stmt', init_expr)
        cond = self.parse_expr()
        self.expect(';')
        step = self.parse_expr()
        self.expect(')')
        body = self.parse_block()
        return ('for', init, cond, step, body)

    def parse_if(self):
        self.expect('SNIFF')
        self.expect('(')
        cond = self.parse_expr()
        self.expect(')')
        then = self.parse_block()
        els = None
        if self.at('SWAT'):
            self.next()
            els = self.parse_block()
        return ('if', cond, then, els)

    def parse_while(self):
        self.expect('KNEAD')
        self.expect('(')
        cond = self.parse_expr()
        self.expect(')')
        body = self.parse_block()
        return ('while', cond, body)

    # ═══ EXPRESSIONS (C++ precedence) ═══
    def parse_expr(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_or()
        if self.at('=', 'ADD_EQ', 'SUB_EQ', 'MUL_EQ', 'DIV_EQ', 'MOD_EQ'):
            op = self.next().type
            right = self.parse_assignment()
            return ('assign', op, left, right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.at('OR'):
            self.next()
            right = self.parse_and()
            left = ('binop', '||', left, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.at('AND'):
            self.next()
            right = self.parse_equality()
            left = ('binop', '&&', left, right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.at('EQ', 'NEQ'):
            op = self.next().type
            right = self.parse_comparison()
            left = ('binop', '==' if op == 'EQ' else '!=', left, right)
        return left

    def parse_comparison(self):
        left = self.parse_shift()
        while self.at('LTE', 'GTE', '<', '>'):
            op = self.next().type
            right = self.parse_shift()
            sym = {'LTE':'<=', 'GTE':'>=', '<':'<', '>':'>'}[op]
            left = ('binop', sym, left, right)
        return left

    def parse_shift(self):
        left = self.parse_additive()
        while self.at('SHL', 'SHR'):
            op = self.next().type
            right = self.parse_additive()
            left = ('binop', '<<' if op == 'SHL' else '>>', left, right)
        return left

    def parse_additive(self):
        left = self.parse_mult()
        while self.at('+', '-'):
            op = self.next().type
            right = self.parse_mult()
            left = ('binop', op, left, right)
        return left

    def parse_mult(self):
        left = self.parse_unary()
        while self.at('*', '/', '%'):
            op = self.next().type
            right = self.parse_unary()
            left = ('binop', op, left, right)
        return left

    def parse_unary(self):
        if self.at('-'):
            self.next()
            return ('unary', '-', self.parse_unary())
        if self.at('!'):
            self.next()
            return ('unary', '!', self.parse_unary())
        if self.at('&'):
            self.next()
            return ('address_of', self.parse_unary())
        if self.at('*'):
            self.next()
            return ('deref', self.parse_unary())
        if self.at('INC'):
            self.next()
            return ('pre_inc', self.parse_unary())
        if self.at('DEC'):
            self.next()
            return ('pre_dec', self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.at('('):
                self.next()
                args = []
                if not self.at(')'):
                    while True:
                        args.append(self.parse_expr())
                        if not self.match(','):
                            break
                self.expect(')')
                expr = ('call', expr, args)
            elif self.at('.'):
                self.next()
                name = self.expect('IDENT').value
                expr = ('member', expr, name)
            elif self.at('ARROW'):
                self.next()
                name = self.expect('IDENT').value
                expr = ('arrow', expr, name)
            elif self.at('['):
                self.next()
                idx = self.parse_expr()
                self.expect(']')
                expr = ('index', expr, idx)
            elif self.at('INC'):
                self.next()
                expr = ('post_inc', expr)
            elif self.at('DEC'):
                self.next()
                expr = ('post_dec', expr)
            else:
                break
        return expr

    def parse_primary(self):
        t = self.peek()

        # Numbers
        if t.type == 'NUMBER':
            self.next()
            return ('num', t.value)

        # Strings
        if t.type == 'STRING':
            self.next()
            return ('str', t.value)

        # Chars
        if t.type == 'CHAR':
            self.next()
            return ('char', t.value)

        # Booleans / null
        if t.type == 'TRUE':
            self.next(); return ('bool', True)
        if t.type == 'FALSE':
            self.next(); return ('bool', False)
        if t.type in ('NULL', 'NULLPTR'):
            self.next(); return ('null',)
        if t.type == 'HUNGRY':
            self.next(); return ('null',)
        if t.type == 'NOD':
            self.next(); return ('bool', True)
        if t.type == 'SHAKE':
            self.next(); return ('bool', False)

        # Array literal: [1, 2, 3]
        if t.type == '[':
            self.next()
            elements = []
            if not self.at(']'):
                while True:
                    elements.append(self.parse_expr())
                    if not self.match(','):
                        break
            self.expect(']')
            return ('array', elements)

        # Parenthesized
        if t.type == '(':
            self.next()
            expr = self.parse_expr()
            self.expect(')')
            return expr

        # me (this)
        if t.type == 'ME':
            self.next()
            return ('me',)

        # Identifiers (var / function name)
        if t.type == 'IDENT':
            self.next()
            return ('var', t.value)

        # new <Type>(args)
        if t.type == 'NEW':
            self.next()
            typename = self.parse_type()
            args = []
            if self.at('('):
                self.next()
                if not self.at(')'):
                    while True:
                        args.append(self.parse_expr())
                        if not self.match(','):
                            break
                self.expect(')')
            return ('new', typename, args)

        raise ParseError(f"Unexpected token: {t.type} ({t.value!r})", t.line, t.col)


# ═══ PUBLIC API ═══
def parse(source):
    tokens = tokenize(source)
    return Parser(tokens).parse_program()


def format_ast(node, indent=0):
    pad = '  ' * indent
    if not isinstance(node, tuple):
        return f'{pad}{node!r}'
    head = node[0]
    parts = [f'{pad}({head}']
    for item in node[1:]:
        if isinstance(item, tuple) and item and isinstance(item[0], str):
            parts.append(format_ast(item, indent + 1))
        elif isinstance(item, list):
            parts.append(f'{pad}  [')
            for x in item:
                if isinstance(x, tuple):
                    parts.append(format_ast(x, indent + 2))
                else:
                    parts.append(f'{pad}    {x!r}')
            parts.append(f'{pad}  ]')
        else:
            parts.append(f'{pad}  {item!r}')
    parts.append(f'{pad})')
    return '\n'.join(parts)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: parser_v3.py <file.cat>'); sys.exit(1)
    src = open(sys.argv[1]).read()
    try:
        ast = parse(src)
        print(format_ast(ast))
    except ParseError as e:
        print(f'ParseError at {e.line}:{e.col}: {e}')
        sys.exit(1)
