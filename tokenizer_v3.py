"""Cat++ v3 Tokenizer — C++ syntax + cat keywords."""
from dataclasses import dataclass

KEYWORDS = {
    # Cat keywords (giữ identity)
    'purr', 'paw', 'meow', 'give', 'sniff', 'swat',
    'knead', 'groom', 'sit', 'leap', 'tap', 'hiss',
    'cat', 'kin', 'me', 'kit', 'litter', 'use',
    'nod', 'shake', 'hungry', 'with', 'either', 'never',
    'match', 'case', 'in', 'of',
    # Types
    'int', 'float', 'str', 'bool', 'void', 'char',
    'long', 'short', 'double', 'unsigned', 'signed',
    'ptr', 'null',
    # Control
    'if', 'else', 'while', 'for', 'return', 'break', 'continue',
    'class', 'struct', 'enum', 'namespace',
    'new', 'delete', 'this', 'print', 'exit', 'sizeof', 'static', 'const',
    'true', 'false', 'nullptr', 'include',
}

@dataclass
class Token:
    type: str
    value: object
    line: int
    col: int

class TokenizerError(Exception):
    def __init__(self, msg, line=0, col=0):
        super().__init__(msg)
        self.line, self.col = line, col


def tokenize(src):
    tokens, i, line, col, n = [], 0, 1, 1, len(src)
    def peek(off=0):
        idx = i + off
        return src[idx] if idx < n else ''
    def add(t, v):
        tokens.append(Token(t, v, line, col))

    while i < n:
        c = src[i]
        if c in ' \t\r': i += 1; col += 1; continue
        if c == '\n': i += 1; line += 1; col = 1; continue

        # Preprocessor directive (#include, #define, ...)
        if c == '#':
            j = i
            while j < n and src[j] != '\n': j += 1
            directive = src[i:j].strip()
            add('DIRECTIVE', directive)
            i = j
            continue

        # Line comment
        if c == '/' and peek(1) == '/':
            j = i + 2
            while j < n and src[j] != '\n': j += 1
            i = j; continue

        # Block comment
        if c == '/' and peek(1) == '*':
            i += 2; col += 2; closed = False
            while i < n:
                if src[i] == '*' and peek(1) == '/':
                    i += 2; col += 2; closed = True; break
                if src[i] == '\n': line += 1; col = 1
                else: col += 1
                i += 1
            if not closed: raise TokenizerError('Unterminated block comment', line, col)
            continue

        # String
        if c == '"':
            start_line, start_col = line, col
            i += 1; col += 1; s = ''
            while i < n and src[i] != '"':
                if src[i] == '\\' and i + 1 < n:
                    esc = src[i+1]
                    s += {'n':'\n','t':'\t','r':'\r','\\':'\\','"':'"','0':'\0'}.get(esc, esc)
                    i += 2; col += 2
                else:
                    s += src[i]; i += 1; col += 1
            if i >= n: raise TokenizerError('Unterminated string', start_line, start_col)
            i += 1; col += 1
            add('STRING', s); continue

        # Char literal
        if c == "'":
            i += 1; col += 1
            if i < n and src[i] == '\\' and i+1 < n:
                esc = src[i+1]
                ch = {'n':'\n','t':'\t','r':'\r','\\':'\\',"'":"'",'0':'\0'}.get(esc, esc)
                i += 2; col += 2
            else:
                ch = src[i] if i < n else ''
                i += 1; col += 1
            if i < n and src[i] == "'": i += 1; col += 1
            add('CHAR', ch); continue

        # Number
        if c.isdigit() or (c == '.' and peek(1).isdigit()):
            start = i; is_float = False
            # Hex
            if c == '0' and peek(1) in 'xX':
                i += 2; col += 2
                while i < n and src[i] in '0123456789abcdefABCDEF': i += 1; col += 1
                add('NUMBER', int(src[start:i], 16)); continue
            # Binary
            if c == '0' and peek(1) in 'bB':
                i += 2; col += 2
                while i < n and src[i] in '01': i += 1; col += 1
                add('NUMBER', int(src[start+2:i], 2)); continue
            # Decimal
            while i < n and src[i].isdigit(): i += 1; col += 1
            if i < n and src[i] == '.':
                is_float = True; i += 1; col += 1
                while i < n and src[i].isdigit(): i += 1; col += 1
            # Exponent
            if i < n and src[i] in 'eE':
                is_float = True; i += 1; col += 1
                if i < n and src[i] in '+-': i += 1; col += 1
                while i < n and src[i].isdigit(): i += 1; col += 1
            # Suffix
            while i < n and src[i] in 'fFlLuU':
                if src[i] in 'fF': is_float = True
                i += 1; col += 1
            num_str = src[start:i].rstrip('fFlLuU')
            add('NUMBER', float(num_str) if is_float else int(num_str))
            continue

        # Identifier / Keyword
        if c.isalpha() or c == '_':
            start = i
            while i < n and (src[i].isalnum() or src[i] == '_'): i += 1; col += 1
            w = src[start:i]
            add(w.upper() if w in KEYWORDS else 'IDENT', w)
            continue

        # Three-char ops
        three = src[i:i+3]
        if three == '<<=':
            add('SHL_EQ', '<<='); i += 3; col += 3; continue
        if three == '>>=':
            add('SHR_EQ', '>>='); i += 3; col += 3; continue
        if three == '...':
            add('DOTS', '...'); i += 3; col += 3; continue

        # Two-char ops
        two = src[i:i+2]
        op_map = {'==':'EQ','!=':'NEQ','<=':'LTE','>=':'GTE','&&':'AND','||':'OR',
                  '<<':'SHL','>>':'SHR','++':'INC','--':'DEC','+=':'ADD_EQ',
                  '-=':'SUB_EQ','*=':'MUL_EQ','/=':'DIV_EQ','%=':'MOD_EQ',
                  '&=':'AND_EQ','|=':'OR_EQ','^=':'XOR_EQ','->':'ARROW','::':'SCOPE'}
        if two in op_map:
            add(op_map[two], two); i += 2; col += 2; continue

        # Single char
        if c in '{}()[];,:.<>+-*/%=&|^!~?':
            add(c, c); i += 1; col += 1; continue

        raise TokenizerError(f'Unknown char: {c!r}', line, col)

    add('EOF', None)
    return tokens


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: tokenizer_v3.py <file.cat>'); sys.exit(1)
    src = open(sys.argv[1]).read()
    for t in tokenize(src):
        print(f'{t.line:3}:{t.col:2}  {t.type:12} {t.value!r}')
