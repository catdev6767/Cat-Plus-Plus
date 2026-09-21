# Cat++

A programming language with cat-themed syntax. **4 engines**, **149 builtins**,
**native C compilation**, **CLI tooling**, and a **web IDE**.

## Quick start

    # Web IDE
    python3 catpp.py
    # Open http://localhost:5000

    # CLI
    paw run hello.cat
    paw new game.cat
    paw repl

## Engines

| Engine | Speed | File |
|---|---|---|
| Interpreter | 1x | interpreter.py |
| Bytecode VM | 2-3x | catpp_vm.py |
| PyCompiler | 20-50x | catpp_pycompiler.py |
| Native C | **13,635x** | transpiler_c_native.py |

## CLI — paw

    paw run FILE.cat          # Run a script
    paw new FILE.cat          # Create + open editor
    paw edit FILE.cat         # Open in PawEditor
    paw repl                  # Interactive REPL
    paw build FILE.cat        # Transpile -> C (boxed)
    paw build-fast FILE.cat   # Transpile -> native C (needs types)
    paw fmt FILE.cat          # Format code
    paw lint FILE.cat         # Check for issues
    paw check FILE.cat        # Type coverage check

Install: `ln -sf ~/catpp/paw/paw ~/.local/bin/paw`

## PawEditor

Nano-like editor for Cat++ with syntax highlight. Written in Python + curses.

    pawedit hello.cat

Shortcuts: ^S Save, ^O Save-As, ^W Find, ^G Goto, ^K Cut, ^U Paste, ^X Exit.

## Language

    meow "Hello, Cat++!"

    paw x = 42
    purr add(a, b)
        give a + b

    meow add(x, 10)   # 52

    # Types (optional, enables native compile)
    purr sq(n: i32) -> i32
        give n * n

    meow sq(5)        # 25

## Builtins (149)

Math (clamp, factorial, is_prime, gcd, lerp), string (title_case,
starts_with, count_sub), list (flatten, chunk, zip_lists), dict
(merge_dict, invert_dict), JSON (json_parse, json_stringify), path
(path_basename, path_ext), time, system, testing (assert_eq), and more.

## Tests

    python3 tests/test_all.py

46 cases x 4 engines.

## Docs

    python3 gen_docs.py     # build static/docs/
    python3 gen_text.py     # build .md / .txt for download

## FelisOS

The kernel `felisos/` is archived (hobby OS in C freestanding, 32-bit x86).
See `felisos/README.md` and `docs/felisos-internals.md`.

## License

MIT
