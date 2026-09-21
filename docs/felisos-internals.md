# FelisOS Internals — Kernel Lessons

Architecture notes and lessons learned building the Kitty kernel.
For anyone wanting to understand a 32-bit x86 kernel.

## 1. Boot flow

    GRUB (multiboot1)
      │
      ├─ Loads kernel/kitty.elf at 0x100000 (1 MB)
      ├─ Sets up protected mode
      └─ Jumps to _start
           │
           └─ kernel/entry.s
                ├─ cli               # disable interrupts
                ├─ set up 16KB stack
                ├─ push EAX (magic 0x2BADB002)
                ├─ push EBX (multiboot info address)
                └─ call kmain

**Lesson:** Multiboot header must be within the first 8 KB of the file
and in a LOAD segment. Linker script must place `.multiboot` first.

## 2. Interrupts — IDT + PIC

- **IDT**: 256 entries, each pointing to a handler.
- **PIC** (8259): two chips, remap so IRQ0 -> 32, IRQ8 -> 40.
- **IRQ handlers must send EOI** to the PIC, otherwise no further interrupts arrive.

    IRQ0  (timer)    -> 32 -> (masked, unused)
    IRQ1  (keyboard) -> 33 -> irq1_stub -> keyboard_handler
    IRQ2  (cascade)  -> 34 -> (must be unmasked for slave to work)
    IRQ12 (mouse)    -> 44 -> irq12_stub -> mouse_handler

**Lesson:** IRQ12 is on the slave PIC. Master must unmask IRQ2 (cascade line).
Forget this and the mouse never fires.

## 3. Framebuffer vs VGA text

- **VGA text** (0xB8000): 80x25 chars, 2 bytes per cell (char + attr).
- **Framebuffer**: GRUB provides it via multiboot info when flag bit 2 is set.
  - Addr: usually 0xFD000000
  - BPP: 24 or 32
  - Pitch: bytes per row (NOT width * bpp/8)

**Lesson:** Draw a pixel as addr + y*pitch + x*bpp/8.
Never assume pitch == width * bpp / 8.

## 4. Filesystem — RAM FS

Simplest form: static array of 64 entries with name, data, size, used,
is_dir, parent fields.

- fs_create_at(parent, name, is_dir)
- fs_resolve(cwd, path) — handles `..`, `.`, absolute/relative
- fs_path_of(idx, out) — reverse: get path from index

**Lesson:** A recursive parent field is enough for a directory tree. No inodes needed.

## 5. Shell + line editor

The C shell has a hand-written line editor:
- read_line() loops reading chars from keyboard
- Supports: backspace, delete, arrow left/right, home/end, tab complete, history
- Redraws via ANSI escape codes

**Lesson:** No need for readline. With a raw-scancode keyboard driver,
you can implement it yourself.

## 6. Cat++ mini interpreter

The kernel includes a mini Cat++ interpreter (catpp_mini.c), ~700 lines of C:
- Lexer, recursive-descent parser, evaluator
- Supports: meow, paw, purr, give, sniff/swat, knead, sit/leap
- Builtins: say, tally, exec, readline, read_file, write_file
- Uses long (not double) — kernel does not link libgcc, no floating point

**Lesson:** Freestanding C has no libgcc. Avoid double, float, large modulo.
If needed, write soft-float or link libgcc.a.

## 7. IRQ race conditions

**Critical trap:** Never call heavy functions inside an IRQ handler.

Example: the keyboard handler must NOT run the Cat++ interpreter.
Meanwhile another IRQ fires — state corruption, stack overflow.

**Correct pattern:** IRQ handler only queues events. Main loop pops and processes.

    /* keyboard IRQ: */
    gui_key_push(c);

    /* main loop: */
    while (gui_key_has()) {
        char k = gui_key_pop();
        dispatch(k);
    }

**Lesson:** This is why real kernels have bottom halves / tasklets / work queues.

## 8. GUI Window Manager — failed lesson

Attempted a GUI window manager. Failed because:
- No compositor: each window needs a back buffer (~800 KB at 800x600x4)
- No memory allocator to hand out buffers
- No layer/z-order
- Redrawing wallpaper on every action — slow
- Race conditions when IRQs fire mid-draw

**Conclusion:** Proper GUI requires:
1. Page allocator
2. Per-window off-screen framebuffer
3. Composite blit: buffer -> screen
4. Dirty region tracking

Not feasible without memory management.

## 9. References

- OSDev Wiki — osdev.org
- Crafting Interpreters — for interpreters
- Intel SDM Vol 3 — IDT, page tables
- SerenityOS — most successful modern hobby OS
- ToaruOS — C kernel with simple GUI
- MenuetOS / KolibriOS — assembly OS

## 10. If continuing

Correct order to continue development:
1. Page allocator — 4KB bitmap
2. Heap — kmalloc / kfree
3. Processes — fork / exec / wait
4. Disk driver — ATA PIO mode
5. ext2-like FS — inode + block
6. Ethernet — RTL8139
7. TCP/IP — port uIP
8. Compositor — do GUI properly
