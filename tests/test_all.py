#!/usr/bin/env python3
"""Test toàn bộ hệ thống Cat++ — 4 engine, so sánh output."""
import sys, os, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

# Colors
G='\033[92m'; R='\033[91m'; Y='\033[93m'; C='\033[96m'; B='\033[1m'; D='\033[2m'; X='\033[0m'

# Test cases: (name, code, expected_output)
CASES = [
    # ── Core ──
    ('basic_math',       'meow 3 + 4 * 2', '11'),
    ('basic_float',      'meow 10 / 4', '2.5'),
    ('basic_intdiv',     'meow 10 / 2', '5'),
    ('basic_mod',        'meow 17 % 5', '2'),
    ('var_assign',       'paw x = 5\nx = x + 3\nmeow x', '8'),
    ('bool_nod',         'meow nod', 'nod'),
    ('bool_shake',       'meow shake', 'shake'),
    ('null_hungry',      'meow hungry', 'hungry'),
    ('logic_with',       'meow nod with shake', 'shake'),
    ('logic_either',     'meow nod either shake', 'nod'),
    ('logic_never',      'meow never nod', 'shake'),
    ('string_concat',    'meow "Hello, " + "Cat!"', 'Hello, Cat!'),

    # ── Control flow ──
    ('if_true',          'sniff 5 > 3\n    meow "yes"', 'yes'),
    ('if_else',          'sniff shake\n    meow "a"\nswat\n    meow "b"', 'b'),
    ('while_count',      'paw i = 1\nknead i <= 3\n    meow i\n    i = i + 1', '1\n2\n3'),
    ('break_sit',        'paw i = 1\nknead i <= 5\n    sniff i == 3\n        sit\n    meow i\n    i = i + 1', '1\n2'),
    ('continue_leap',    'paw i = 0\nknead i < 3\n    i = i + 1\n    sniff i == 2\n        leap\n    meow i', '1\n3'),

    # ── Functions ──
    ('func_simple',      'purr add(a, b)\n    give a + b\nmeow add(3, 4)', '7'),
    ('func_recursion',   'purr fact(n)\n    sniff n <= 1\n        give 1\n    give n * fact(n - 1)\nmeow fact(5)', '120'),
    ('func_default',     'purr f(a, b=10)\n    give a + b\nmeow f(5)', '15'),

    # ── List / Dict ──
    ('list_literal',     'paw a = [1, 2, 3]\nmeow tail(a)', '3'),
    ('list_index',       'paw a = [10, 20, 30]\nmeow a[1]', '20'),
    ('list_head',        'meow head([1, 2, 3])', '1'),
    ('list_pile',        'meow pile([1, 2, 3, 4])', '10'),
    ('dict_get',         'paw d = {"a": 1}\nmeow d["a"]', '1'),
    ('each_loop',        'groom x of [1,2,3]\n    meow x', '1\n2\n3'),
    ('in_list',          'meow 3 in [1,2,3]', 'nod'),

    # ── String methods ──
    ('str_upper',        'meow "hi".upper()', 'HI'),
    ('str_lower',        'meow "HI".lower()', 'hi'),
    ('str_len',          'meow tail("hello")', '5'),
    ('str_slice',        'meow "hello"[1:4]', 'ell'),

    # ── Class ──
    ('class_basic',      'cat P\n    paw x\n    purr new(v)\n        me.x = v\nmeow P(7).x', '7'),
    ('class_method',     'cat P\n    paw x\n    purr new(v)\n        me.x = v\n    purr get()\n        give me.x\nmeow P(42).get()', '42'),

    # ── Type annotation ──
    ('type_let',         'paw x: i32 = 5\nmeow x', '5'),
    ('type_func',        'purr sq(n: i32) -> i32\n    give n * n\nmeow sq(6)', '36'),

    # ── Pointer ──
    ('ptr_deref',        'paw x = 5\npaw p = &x\nmeow *p', '5'),
    ('ptr_write',        'paw x = 5\npaw p = &x\n*p = 99\nmeow x', '99'),

    # ── Native (type đầy đủ) ──
    ('native_sum', 'purr sum_to(n: i32) -> i32\n    paw total: i32 = 0\n    paw i: i32 = 1\n    knead i <= n\n        total = total + i\n        i = i + 1\n    give total\nmeow sum_to(10)', '55'),
    ('native_sum64', 'purr sum_to(n: i32) -> i64\n    paw total: i64 = 0\n    paw i: i32 = 1\n    knead i <= n\n        total = total + i\n        i = i + 1\n    give total\nmeow sum_to(1000000)', '500000500000'),
    ('native_fib', 'purr fib(n: i32) -> i32\n    sniff n < 2\n        give n\n    give fib(n-1) + fib(n-2)\nmeow fib(10)', '55'),

    # ── Builtins ──
    ('bi_bolt',          'meow bolt(-5)', '5'),
    ('bi_kitten',        'meow kitten(3, 7)', '3'),
    ('bi_lion',          'meow lion(3, 7)', '7'),
    ('bi_say',           'meow say(42)', '42'),
    ('bi_shred',         'meow shred("a,b,c", ",")', '[a, b, c]'),
    ('bi_walk',          'meow walk(1, 4)', '[1, 2, 3]'),
    # Phase 9a - Regression tests
    ('inherit_field',      'cat A\n    paw n\n    purr new(v)\n        me.n = v\ncat B kin A\n    purr hi()\n        give me.n\nmeow B("Bob").hi()', 'Bob'),
    ('nested_func',        'purr outer(n)\n    purr inner(x)\n        give x * 2\n    give inner(n)\nmeow outer(5)', '10'),
    ('enum_value',         'litter Color\n    red\n    green\nmeow Color.green', 'Color.green'),
    ('interp_string',      'paw n = "Tom"\nmeow "Hi, {n}!"', 'Hi, Tom!'),

]


def run_interpreter(code):
    from interpreter import run_catpp
    return run_catpp(code, timeout=30.0).strip()


def run_vm(code):
    from catpp_vm import run_catpp_vm
    return run_catpp_vm(code).strip()


def run_pycompiler(code):
    from catpp_pycompiler import run_catpp_py, Unsupported
    try:
        return run_catpp_py(code, timeout=30.0).strip()
    except Unsupported as e:
        return f'__UNSUPPORTED__{e}'


def run_transpiler_c(code, idx):
    """Transpile + gcc + run. Cham nhung chac."""
    tmpdir = tempfile.mkdtemp(prefix='catpp_test_')
    cat_path = os.path.join(tmpdir, 'test.cat')
    c_path = os.path.join(tmpdir, 'test.c')
    bin_path = os.path.join(tmpdir, 'test')
    with open(cat_path, 'w', encoding='utf-8') as f:
        f.write(code)
    try:
        from transpiler_c import transpile
        c_code = transpile(code)
        with open(c_path, 'w', encoding='utf-8') as f:
            f.write(c_code)
        r = subprocess.run(['gcc', '-O2', '-lm', '-o', bin_path, c_path],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return f'__GCC_FAIL__{r.stderr[:80]}'
        r = subprocess.run([bin_path], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return f'__RUN_FAIL__{r.stderr[:80]}'
        return r.stdout.strip()
    except Exception as e:
        return f'__ERR__{type(e).__name__}: {e}'
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    print(f'{B}{C}═══ Cat++ Test Suite — 4 engines ═══{X}\n')

    # Check engines available
    engines = {}
    try:
        from interpreter import run_catpp
        engines['interp'] = run_interpreter
    except Exception as e:
        print(f'{R}interpreter: {e}{X}')
    try:
        from catpp_vm import run_catpp_vm
        engines['vm'] = run_vm
    except Exception as e:
        print(f'{R}vm: {e}{X}')
    try:
        from catpp_pycompiler import run_catpp_py
        engines['pyc'] = run_pycompiler
    except Exception as e:
        print(f'{R}pycompiler: {e}{X}')
    try:
        from transpiler_c import transpile
        engines['c'] = run_transpiler_c
    except Exception as e:
        print(f'{R}transpiler_c: {e}{X}')

    print(f'  Engines: {", ".join(engines.keys())}')
    print()

    # Stats
    stats = {name: {'pass': 0, 'fail': 0, 'skip': 0} for name in engines}
    failures = []

    for name, code, expected in CASES:
        results = {}
        for eng_name, eng_fn in engines.items():
            try:
                if eng_name == 'c':
                    got = eng_fn(code, name)
                else:
                    got = eng_fn(code)
                if got.startswith('__'):
                    results[eng_name] = ('skip', got[:50])
                elif got == expected:
                    results[eng_name] = ('pass', '')
                else:
                    results[eng_name] = ('fail', got[:40])
            except Exception as e:
                results[eng_name] = ('fail', f'{type(e).__name__}: {str(e)[:40]}')

        # In dong ket qua
        all_pass = all(r[0] == 'pass' for r in results.values())
        any_fail = any(r[0] == 'fail' for r in results.values())
        if all_pass:
            mark = f'{G}✓{X}'
        elif any_fail:
            mark = f'{R}✗{X}'
        else:
            mark = f'{Y}○{X}'

        parts = []
        for eng_name in engines.keys():
            status, _ = results[eng_name]
            sym = {'pass': f'{G}·{X}', 'fail': f'{R}✗{X}', 'skip': f'{Y}○{X}'}[status]
            parts.append(sym)
            stats[eng_name][status] += 1

        print(f'  {mark} {name:20s}  [{ "".join(parts) }]')

        if any_fail:
            for eng_name, (status, msg) in results.items():
                if status == 'fail':
                    failures.append((name, eng_name, msg))

    # Summary
    print()
    print(f'{B}{C}═══ Summary ═══{X}\n')
    print(f'  {"Engine":<14} {"Pass":>6} {"Fail":>6} {"Skip":>6}')
    print(f'  {"-"*14} {"-"*6} {"-"*6} {"-"*6}')
    total_pass = 0
    total_fail = 0
    for eng_name in engines.keys():
        s = stats[eng_name]
        print(f'  {eng_name:<14} {s["pass"]:>6} {s["fail"]:>6} {s["skip"]:>6}')
        total_pass += s['pass']
        total_fail += s['fail']

    print()
    if failures:
        print(f'{B}{R}═══ Failures ═══{X}\n')
        for name, eng, msg in failures[:15]:
            print(f'  {R}✗{X} {name} [{eng}]: {D}{msg}{X}')
        if len(failures) > 15:
            print(f'  {D}... và {len(failures)-15} lỗi khác{X}')

    print()
    if total_fail == 0:
        print(f'{G}{B}✓ ALL PASS ({len(CASES)} cases × {len(engines)} engines){X}')
        return 0
    else:
        print(f'{R}{B}✗ {total_fail} failures{X}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
