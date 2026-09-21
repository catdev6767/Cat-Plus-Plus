# FelisOS — Archived Hobby OS

A 32-bit x86 hobby operating system written in freestanding C.
**Archived** — no longer under active development. Community is welcome to fork and continue.

## Components

| Layer | Name | File |
|---|---|---|
| OS | FelisOS | (product name) |
| Kernel | Kitty | `kernel/kitty.elf` |
| Init | SysCat | `kernel/boot/SysCat.cat` |
| Shell | Purrminal | `kernel/commands.c` |
| Language | Cat++ | `runtime/`, `kernel/catpp_mini.c` |

## Features

- Multiboot1 boot via GRUB
- Framebuffer 1024x768 (24/32 bpp) + VGA text fallback
- IDT, IRQ, PIC remap
- PS/2 keyboard driver (full keys, modifiers, extended keys)
- PS/2 mouse driver (cursor + click)
- RAM filesystem (64 files, 2KB each, subdirectories)
- Purrminal shell: 60+ commands (ls, cd, cat, cp, mv, mkdir, grep, wc, ...)
- TTY switch: Ctrl+Alt+F1 (GUI), F2 (shell), F3 (debug)
- Mini Cat++ interpreter in kernel
- GUI window manager (incomplete)
- Windowed apps: Purrminal, FileMgr, PawEditor

## Not implemented

- Processes / threads
- Virtual memory / paging
- Ethernet + TCP/IP
- Multi-user
- Persistent storage (RAM only)

## Build

    cd felisos
    bash build.sh

Output: `kernel/kitty.elf`, `felisos.iso`.

Requires: gcc (with 32-bit support), ld, grub-mkrescue, xorriso, qemu-system-x86_64.

## Run

    # Direct kernel (no GUI)
    qemu-system-x86_64 -kernel kernel/kitty.elf -m 128M -display curses

    # ISO with GRUB (has GUI)
    qemu-system-x86_64 -cdrom felisos.iso -m 128M -vga std -boot d -net none

    # VNC (mouse works)
    qemu-system-x86_64 -cdrom felisos.iso -m 128M -vga std -boot d -net none -vnc :5

## Layout

    felisos/
    ├── kernel/
    │   ├── entry.s, irq.s        # boot assembly
    │   ├── main.c                # kmain
    │   ├── idt.c                 # IDT + PIC
    │   ├── keyboard.c            # PS/2 keyboard
    │   ├── mouse.c               # PS/2 mouse
    │   ├── fb.c                  # framebuffer driver
    │   ├── fs.c                  # RAM filesystem
    │   ├── commands.c            # shell commands
    │   ├── shell.c               # shell loop + line editor
    │   ├── catpp_mini.c          # mini Cat++ interpreter
    │   ├── window.c              # window manager
    │   ├── filemgr.c             # file manager app
    │   ├── pawedit.c             # text editor app
    │   ├── tty.c                 # TTY manager
    │   ├── font8x8.h             # bitmap font
    │   └── boot/                 # Cat++ scripts
    ├── runtime/
    │   └── catpp_freestanding.c  # VGA + serial output
    ├── libc/                     # minimal stdlib
    ├── build.sh
    └── felisos.iso

## License

MIT — see LICENSE at repo root.

## Status

**Archived 2026-09.** Kernel stable at demo level.
Community can:
- Fork and continue development
- Study kernel/OS internals from source
- Read `../docs/felisos-internals.md` for architecture
