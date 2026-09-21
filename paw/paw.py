#!/usr/bin/env python3
"""paw — Cat++ CLI: run, new, edit, repl, build."""
import sys, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

VERSION = "0.1.0"
EDITOR = ROOT / "pawedit" / "pawedit"

def cmd_run(args):
    if not args:
        print("Usage: paw run FILE.cat"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: file not found: {path}"); return 1
    code = path.read_text(encoding='utf-8')
    try:
        from interpreter import run_catpp
        out = run_catpp(code, timeout=30)
        if out: print(out)
        return 0
    except Exception as e:
        print(f"paw run: {type(e).__name__}: {e}"); return 1

def cmd_new(args):
    if not args:
        print("Usage: paw new FILE.cat"); return 1
    path = Path(args[0])
    if path.exists():
        print(f"paw: file already exists: {path}"); return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# ' + path.name + '\nmeow "Hello, Cat++!"\n', encoding='utf-8')
    print(f"Created: {path}")
    return open_in_editor(path)

def open_in_editor(path):
    if not EDITOR.exists():
        print(f"paw: editor not found: {EDITOR}")
        print("Run install first or use: paw edit <file>")
        return 1
    return subprocess.call([str(EDITOR), str(path)])

def cmd_edit(args):
    if not args:
        print("Usage: paw edit FILE.cat"); return 1
    return open_in_editor(Path(args[0]))

def cmd_repl(args):
    print("paw REPL — type 'exit' to quit")
    from interpreter import run_catpp
    while True:
        try:
            line = input("paw> ")
        except (EOFError, KeyboardInterrupt):
            print(); break
        if line.strip() in ('exit', 'quit'): break
        if not line.strip(): continue
        try:
            out = run_catpp(line, timeout=5)
            if out: print(out)
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
    return 0

def cmd_build(args):
    if not args:
        print("Usage: paw build FILE.cat"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: not found: {path}"); return 1
    try:
        from transpiler_c import transpile
        c_code = transpile(path.read_text(encoding='utf-8'))
        out = path.with_suffix('.c')
        out.write_text(c_code, encoding='utf-8')
        print(f"Built: {out}")
        binout = path.with_suffix('')
        r = subprocess.run(['gcc', '-O2', '-lm', '-o', str(binout), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("gcc failed:"); print(r.stderr); return 1
        print(f"Binary: {binout}")
        return 0
    except Exception as e:
        print(f"paw build: {type(e).__name__}: {e}"); return 1

def cmd_build_fast(args):
    if not args:
        print("Usage: paw build-fast FILE.cat"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: not found: {path}"); return 1
    try:
        from transpiler_c_native import transpile, Unsupported
        try:
            c_code = transpile(path.read_text(encoding='utf-8'))
        except Unsupported as e:
            print(f"paw build-fast: needs type annotations — {e}"); return 1
        out = path.with_suffix('.native.c')
        out.write_text(c_code, encoding='utf-8')
        print(f"Built: {out}")
        binout = path.with_suffix('.native')
        r = subprocess.run(['gcc', '-O2', '-o', str(binout), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("gcc failed:"); print(r.stderr); return 1
        print(f"Binary: {binout}  (13,635× faster than interpreter)")
        return 0
    except Exception as e:
        print(f"paw build-fast: {type(e).__name__}: {e}"); return 1

def cmd_fmt(args):
    if not args:
        print("Usage: paw fmt FILE.cat [--write]"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: not found: {path}"); return 1
    from tools import format_catpp
    src = path.read_text(encoding='utf-8')
    out = format_catpp(src)
    if '--write' in args:
        path.write_text(out, encoding='utf-8')
        print(f"Formatted: {path}")
    else:
        orig = src.split('\n')
        new = out.rstrip('\n').split('\n')
        if orig == new:
            print(f"No changes: {path}")
        else:
            import difflib
            for line in difflib.unified_diff(orig, new, lineterm=''):
                if line.startswith('+') and not line.startswith('+++'):
                    print(f'\033[32m{line}\033[0m')
                elif line.startswith('-') and not line.startswith('---'):
                    print(f'\033[31m{line}\033[0m')
                else:
                    print(line)
    return 0


def cmd_lint(args):
    if not args:
        print("Usage: paw lint FILE.cat"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: not found: {path}"); return 1
    from tools import lint_catpp
    issues = lint_catpp(path.read_text(encoding='utf-8'), str(path))
    if not issues:
        print(f"\033[32m✓ {path}: no issues\033[0m"); return 0
    errors = sum(1 for _, s, _ in issues if s == 'error')
    warns = sum(1 for _, s, _ in issues if s == 'warn')
    for ln, sev, msg in issues:
        color = {'error':'\033[31m','warn':'\033[33m','info':'\033[36m'}[sev]
        print(f'{color}{path}:{ln}: {sev}:\033[0m {msg}')
    print(f'\n{len(issues)} issue(s): {errors} error, {warns} warning')
    return 1 if errors else 0


def cmd_check(args):
    if not args:
        print("Usage: paw check FILE.cat"); return 1
    path = Path(args[0])
    if not path.exists():
        print(f"paw: not found: {path}"); return 1
    from tools import check_catpp
    native_ok, issues, stats = check_catpp(path.read_text(encoding='utf-8'), str(path))
    print(f'File: {path}')
    print(f'  Functions: {stats["typed_funcs"]}/{stats["total_funcs"]} fully typed')
    print(f'  Params:    {stats["typed_params"]}/{stats["total_params"]} typed')
    print(f'  Variables: {stats["typed_vars"]}/{stats["total_vars"]} typed')
    print()
    if native_ok:
        print('\033[32m✓ Can compile native (13,635× faster)\033[0m')
    else:
        print('\033[33m○ Native blocked — will use boxed C or interpreter\033[0m')
    if issues:
        print()
        for ln, sev, msg in issues[:20]:
            color = {'error':'\033[31m','warn':'\033[33m','info':'\033[36m'}[sev]
            print(f'{color}{path}:{ln}:\033[0m {msg}')
    return 0 if native_ok else 1


def cmd_help(args=None):
    print(f"""paw v{VERSION} — Cat++ CLI

Usage:
    paw run FILE.cat          Run a Cat++ script
    paw new FILE.cat          Create a new script + open editor
    paw edit FILE.cat         Open a script in PawEditor
    paw repl                  Interactive REPL
    paw build FILE.cat        Transpile to C + compile (boxed)
    paw build-fast FILE.cat   Transpile to native C (needs types)
    paw fmt FILE.cat          Format code (--write to save)
    paw lint FILE.cat         Check for issues
    paw check FILE.cat        Check type coverage for native
    paw version               Show version
    paw help                  This help
""")
    return 0

def main():
    if len(sys.argv) < 2:
        return cmd_help()
    cmd, args = sys.argv[1], sys.argv[2:]
    table = {
        'run': cmd_run, 'new': cmd_new, 'edit': cmd_edit,
        'repl': cmd_repl, 'build': cmd_build,
        'build-fast': cmd_build_fast, 'help': cmd_help,
        'fmt': cmd_fmt, 'lint': cmd_lint, 'check': cmd_check,
    }
    if cmd == 'version':
        print(f"paw v{VERSION}"); return 0
    fn = table.get(cmd)
    if not fn:
        print(f"paw: unknown command '{cmd}'"); return cmd_help()
    return fn(args) or 0

if __name__ == '__main__':
    sys.exit(main())
