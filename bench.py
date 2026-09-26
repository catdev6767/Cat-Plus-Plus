import time, os, subprocess, sys, tempfile

# Đảm bảo import từ catpp
sys.path.insert(0, os.path.expanduser('~/catpp'))
os.chdir(os.path.expanduser('~/catpp'))

CODE_V2 = '''
purr sum_to(n)
    paw total = 0
    paw i = 1
    knead i <= n
        total = total + i
        paw i = i + 1
    give total

meow sum_to(1000000)
'''

CODE_V3 = '''
purr long sum_to(long n) {
    paw long total = 0;
    for (paw long i = 1; i <= n; i = i + 1) {
        total = total + i;
    }
    give total;
}

purr int main() {
    meow(sum_to(1000000));
    give 0;
}
'''

print('=== Benchmark: sum_to(1,000,000) ===')
print()

results = {}

# Interpreter v2
try:
    from interpreter import run_catpp
    t0 = time.perf_counter()
    run_catpp(CODE_V2)
    t = (time.perf_counter() - t0) * 1000
    results['Interpreter v2'] = t
    print(f'Interpreter v2: {t:.1f} ms')
except Exception as e:
    print(f'Interpreter v2 FAIL: {str(e)[:80]}')

# VM v2
try:
    from catpp_vm import run_catpp_vm
    t0 = time.perf_counter()
    run_catpp_vm(CODE_V2)
    t = (time.perf_counter() - t0) * 1000
    results['Bytecode VM'] = t
    print(f'Bytecode VM: {t:.1f} ms')
except Exception as e:
    print(f'Bytecode VM FAIL: {str(e)[:80]}')

# PyCompiler v2
try:
    from catpp_pycompiler import run_catpp_py
    t0 = time.perf_counter()
    run_catpp_py(CODE_V2)
    t = (time.perf_counter() - t0) * 1000
    results['PyCompiler'] = t
    print(f'PyCompiler: {t:.1f} ms')
except Exception as e:
    print(f'PyCompiler FAIL: {str(e)[:80]}')

# LLVM v3
try:
    from codegen_llvm_v3 import compile_to_binary
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cat', delete=False) as f:
        f.write(CODE_V3)
        cat_file = f.name
    bin_file = cat_file.replace('.cat', '')

    t0 = time.perf_counter()
    ok = compile_to_binary(CODE_V3, bin_file, opt_level=3)
    compile_ms = (time.perf_counter() - t0) * 1000

    if ok:
        subprocess.run([bin_file], capture_output=True)
        t0 = time.perf_counter()
        for _ in range(5):
            subprocess.run([bin_file], capture_output=True)
        run_ms = (time.perf_counter() - t0) * 1000 / 5
        results['LLVM v3'] = run_ms
        print(f'LLVM v3: {run_ms:.2f} ms (compile: {compile_ms:.0f} ms)')

    for f in [cat_file, bin_file]:
        if os.path.exists(f): os.remove(f)
except Exception as e:
    print(f'LLVM v3 FAIL: {str(e)[:150]}')

# C -O3
c_code = '#include <stdio.h>\nlong sum_to(long n){long t=0;for(long i=1;i<=n;i++)t+=i;return t;}\nint main(){printf("%ld\\n",sum_to(1000000));return 0;}\n'
with open('/tmp/bench.c', 'w') as f:
    f.write(c_code)
r = subprocess.run(['gcc', '-O3', '-o', '/tmp/bench_c', '/tmp/bench.c'],
                   capture_output=True, text=True)
if os.path.exists('/tmp/bench_c'):
    subprocess.run(['/tmp/bench_c'], capture_output=True)
    t0 = time.perf_counter()
    for _ in range(5):
        subprocess.run(['/tmp/bench_c'], capture_output=True)
    t = (time.perf_counter() - t0) * 1000 / 5
    results['C -O3'] = t
    print(f'C -O3: {t:.2f} ms')

print()
print('=== Summary ===')
if results:
    base = results.get('Interpreter v2', results.get('PyCompiler', 1))
    for name, t in results.items():
        print(f'  {name:20s} {t:8.2f} ms  ({base/t:>7.1f}×)')
