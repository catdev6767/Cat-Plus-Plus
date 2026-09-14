# Changelog

## [1.0.0] — 2026-09-14

Phiên bản đầu tiên. Cat++ là ngôn ngữ lập trình cú pháp tiếng mèo, chạy trong browser, có IDE tích hợp và transpiler sang C để viết OS.

### Ngôn ngữ

- Cú pháp tiếng mèo: `meow`, `paw`, `purr`, `give`, `sniff`, `swat`, `knead`, `groom`, `tap`, `hiss`
- Giá trị: `nod`, `shake`, `hungry`
- Logic: `with`, `either`, `never`, `in`
- OOP: `cat`, `kin`, `me`, `litter`, `static`, `get`, `set`, `abstract`, operator overload
- Advanced: `kit` (lambda), `match/case`, `use` (import), regex
- Low-level: bit ops, `cast`, `sizeof`, `struct`, `volatile`, `asm`, `ptr`
- Operators: `+= -= *= /= %=`, `++ --`, ternary `?:`, coalesce `??`
- **Default params**: `purr f(a, b=10)`
- 100+ built-in functions (math, string, file, system, set, functional)

### IDE

- Monaco Editor với syntax highlight
- Terminal xterm.js
- Command Palette (Ctrl+Shift+P)
- Search toàn dự án (Ctrl+Shift+F)
- Format code (Ctrl+Shift+I)
- Đổi tên biến (F2)
- Learn Mode — 10 bài tập tương tác
- Quiz trắc nghiệm
- Dashboard tiến độ
- Certificate
- Gallery code hay
- Theme: dark, light, cat (mèo đêm)
- Song ngữ VI / EN
- Hệ thống dự án
- Export / Import `.catpp`
- Chia sẻ link

### CLI

- `catpp run <file>` — chạy file
- `catpp repl` — REPL tương tác
- `catpp fmt` — format code
- `catpp lint` — kiểm tra
- `catpp test` — chạy tests

### Docs

- 156 trang/language (VI + EN)
- Tutorial (15 bài)
- Reference (keyword + builtin)
- Cookbook (30 công thức)
- Error reference (20 lỗi)
- Guide (Felis OS, Best Practices, Internals, Performance)
- Tải về: MD, TXT, ZIP

### Felis OS

- Transpiler Cat++ → C (`tools/transpiler.py`)
- Freestanding runtime (`runtime/`)
- Kernel C với Multiboot (`kernel/`)
- Boot trên QEMU bare metal
- Chạy `meow`, `paw`, `sniff`, `knead`, `purr`, `struct`, `cast`

### Hạ tầng

- Kiến trúc module: `core/` + `modules/`
- 40 tests tự động (pass hết)
- Self-healing (`heal.py`)
- Doctor (`doctor.py`)
- Log system (`catpplog.py`)
- Patch engine (`patch_engine.py`)
