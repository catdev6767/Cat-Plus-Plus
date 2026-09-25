# Cat++

A programming language with cat-themed syntax.
**4 engines**, **149 builtins**, **native C compilation**,
**terminal editor**, and **CLI tooling**.

> 🌐 **Website:** https://catdev6767.github.io/Cat-Plus-Plus/
> 📦 **GitHub:** https://github.com/catdev6767/Cat-Plus-Plus

## v3 - C++-like syntax + LLVM native

Cat++ v3 compiles to native binary via LLVM. No C transpilation, no gcc needed.

```cpp
purr int main() {
    meow("Hello, v3!");
    give 0;
}

cat Point {
    paw int x;
    paw int y;
    purr Point(int a, int b) {
        me.x = a;
        me.y = b;
    }
    purr int sum() {
        give me.x + me.y;
    }
};
```

Compile native:

    catpp build hello.cat -o hello
    ./hello

v3 features:
- C++ syntax with braces, semicolons, line comments
- Types: int, float, bool, str, void, char
- Classes + inheritance + methods
- Pointers (int*, &x, *p)
- Arrays, structs, enums
- new / delete + arrow operator
- Stdlib: sqrt, pow, read_file, upper, substr, ...
- Speed: ~2x slower than C, 1000x faster than interpreter

## Quick install

One line (Linux / macOS):

    curl -fsSL https://raw.githubusercontent.com/catdev6767/Cat-Plus-Plus/main/install.sh | bash

Or clone manually:

    git clone https://github.com/catdev6767/Cat-Plus-Plus
    cd Cat-Plus-Plus
    ./install.sh

This installs three commands to `~/.local/bin`:

| Command   | Description                                 |
|-----------|---------------------------------------------|
| catpp     | CLI - run, repl, fmt, lint, test            |
| paw       | Project tools - new, build, check, lint     |
| pawedit   | Terminal editor with Cat++ syntax highlight |

## PawEditor

Terminal editor for Cat++, written in Python + curses.
Nano-like with full Cat++ syntax highlighting.

    pawedit hello.cat        # open a file
    pawedit                  # empty buffer

| Key      | Action       |
|----------|--------------|
| Ctrl+S   | Save         |
| Ctrl+O   | Save as      |
| Ctrl+G   | Go to line   |
| Ctrl+K   | Delete line  |
| Ctrl+X   | Exit         |

## Usage

CLI `catpp`:

    catpp run FILE.cat        # Run script
    catpp repl                # REPL
    catpp fmt FILE.cat        # Format
    catpp lint FILE.cat       # Lint
    catpp test FILE.cat       # Tests
    catpp --version

Project tools `paw`:

    paw run FILE.cat
    paw new FILE.cat
    paw edit FILE.cat
    paw build FILE.cat
    paw build-fast FILE.cat   # Native C (needs types)
    paw check FILE.cat        # Type coverage
    paw lint FILE.cat
    paw fmt FILE.cat
    paw help

## Language

    meow "Hello, Cat++!"

    paw x = 42
    paw name = "Tom"

    purr add(a, b)
        give a + b

    meow add(x, 10)        # 52

    # Optional types enable native compile
    purr square(n: i32) -> i32
        give n * n

    meow square(5)         # 25

### Keywords (37)

- **I/O**: `meow` (print), `listen` (input)
- **Variables**: `paw` (let)
- **Functions**: `purr` (fn), `give` (return)
- **Control**: `sniff` / `swat` (if / else), `knead` (while),
  `groom` / `of` (for-each), `sit` (break), `leap` (continue)
- **Error**: `tap` / `hiss` (try / catch)
- **Logic**: `nod` (true), `shake` (false), `hungry` (null),
  `with` (and), `either` (or), `never` (not)
- **OOP**: `cat` (class), `me` (self), `kin` (extends), `litter` (enum)
- **Lambda**: `kit`
- **Advanced**: `match` / `case`, `use`, `in`, `struct`, `volatile`,
  `cast`, `sizeof`, `asm`, `ptr`, `null`, `packed`

## Engines

| Engine      | Speed         | File                    |
|-------------|---------------|-------------------------|
| Interpreter | 1x            | interpreter.py          |
| Bytecode VM | 2-3x          | catpp_vm.py             |
| PyCompiler  | 20-50x        | catpp_pycompiler.py     |
| Native C    | up to 13,635x | transpiler_c_native.py  |

## Builtins (149)

Math (`clamp`, `factorial`, `is_prime`, `gcd`, `lerp`),
string (`title_case`, `starts_with`, `count_sub`),
list (`flatten`, `chunk`, `zip_lists`),
dict (`merge_dict`, `invert_dict`),
JSON (`json_parse`, `json_stringify`),
path (`path_basename`, `path_ext`),
time, system, testing (`assert_eq`), and more.

## Development

    python3 tests/test_all.py     # 46 cases x 4 engines

## Uninstall

    rm -f ~/.local/bin/catpp ~/.local/bin/paw ~/.local/bin/pawedit
    rm -rf ~/.catpp

## License

MIT
