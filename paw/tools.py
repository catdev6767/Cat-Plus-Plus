"""paw tools — fmt, lint, check cho Cat++."""
import sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def format_catpp(code):
    lines = code.split('\n')
    result = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            result.append('')
            continue
        content = stripped.lstrip(' ')
        indent = len(stripped) - len(content)
        new_indent = (indent // 4) * 4
        result.append(' ' * new_indent + content)

    out, blank_run = [], 0
    for line in result:
        if not line.strip():
            blank_run += 1
            if blank_run == 1:
                out.append('')
        else:
            blank_run = 0
            out.append(line)

    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out) + '\n'


def lint_catpp(code, filename='<input>'):
    issues = []

    try:
        from interpreter import tokenize, Parser, CatError
        try:
            Parser(tokenize(code)).parse()
        except CatError as e:
            issues.append((e.line, 'error', f'Syntax: {e}'))
            return issues
    except ImportError:
        pass

    lines = code.split('\n')
    for ln, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        if '\t' in line:
            issues.append((ln, 'warn', 'Tab character — use spaces (4)'))
        if line != line.rstrip():
            issues.append((ln, 'warn', 'Trailing whitespace'))
        if len(line) > 100:
            issues.append((ln, 'warn', f'Line too long ({len(line)} > 100)'))

    seen = {}
    for ln, line in enumerate(lines, 1):
        m = re.match(r'^(\s*)paw\s+(\w+)', line)
        if m:
            key = (len(m.group(1)), m.group(2))
            if key in seen:
                issues.append((ln, 'warn',
                    f"'{m.group(2)}' redefined at same scope (first at line {seen[key]})"))
            else:
                seen[key] = ln
    return issues


def check_catpp(code, filename='<input>'):
    issues = []
    stats = {
        'total_funcs': 0, 'typed_funcs': 0,
        'total_params': 0, 'typed_params': 0,
        'total_vars': 0, 'typed_vars': 0,
    }

    try:
        from interpreter import tokenize, Parser, CatError
        try:
            ast = Parser(tokenize(code)).parse()
        except CatError as e:
            return False, [(e.line, 'error', f'Syntax: {e}')], stats
    except ImportError:
        return False, [(0, 'error', 'Cannot import interpreter')], stats

    for node in ast:
        if node[0] == 'func':
            stats['total_funcs'] += 1
            name = node[1]
            params = node[2]
            ptypes = node[6] if len(node) > 6 else {}
            rtype = node[7] if len(node) > 7 else None
            ln = node[5] if len(node) > 5 else 0
            typed = rtype is not None
            for p in params:
                stats['total_params'] += 1
                if p in ptypes:
                    stats['typed_params'] += 1
                else:
                    typed = False
            if typed:
                stats['typed_funcs'] += 1
            else:
                missing = [p for p in params if p not in ptypes]
                parts = []
                if missing: parts.append(f"params: {', '.join(missing)}")
                if not rtype: parts.append('return type')
                issues.append((ln, 'info',
                    f"Function '{name}' missing types ({'; '.join(parts)}) "
                    f"— cannot compile native"))
        elif node[0] == 'let':
            stats['total_vars'] += 1
            ann = node[4] if len(node) > 4 else None
            if ann:
                stats['typed_vars'] += 1
            else:
                issues.append((node[3] if len(node) > 3 else 0, 'info',
                    f"Variable '{node[1]}' has no type annotation"))

    native_ok = False
    try:
        from transpiler_c_native import transpile, Unsupported
        try:
            transpile(code)
            native_ok = True
        except Unsupported as e:
            issues.append((0, 'warn', f'Native compile blocked: {e}'))
    except ImportError:
        pass

    return native_ok, issues, stats
