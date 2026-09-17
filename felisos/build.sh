#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🐱 Kitty OS build v0.2"
echo ""

CFLAGS="-m32 -ffreestanding -fno-pic -fno-stack-protector -fno-builtin -nostdlib -nostdinc -mno-sse -mno-sse2 -mno-mmx -mno-80387 -mno-fp-ret-in-387 -Wall -Wno-unused-function -O2 -DCATPP_FREESTANDING"
CFLAGS="$CFLAGS -I libc -I runtime -I kernel"

echo "Compile:"
for f in entry.s irq.s idt.c keyboard.c string.c fs.c commands.c shell.c utils.c main.c catpp_mini.c fb.c mouse.c tty.c window.c; do
    base="${f%.*}"
    out=$(echo "$base" | tr '/' '_')
    gcc $CFLAGS -c "kernel/$f" -o "kernel/$out.o"
    echo "  ✓ $out.o"
done

gcc $CFLAGS -c runtime/catpp_freestanding.c -o kernel/rt.o
echo "  ✓ rt.o"

echo ""
echo "Link:"
GCC_LIB=$(gcc -m32 -print-libgcc-file-name)
ld -m elf_i386 -T kernel/linker.ld -nostdlib \
   kernel/entry.o kernel/irq.o kernel/rt.o \
   kernel/idt.o kernel/keyboard.o kernel/string.o \
   kernel/fs.o kernel/commands.o kernel/shell.o \
   kernel/utils.o kernel/main.o kernel/catpp_mini.o kernel/fb.o kernel/mouse.o kernel/tty.o kernel/window.o \
   $GCC_LIB \
   -o kernel/kitty.elf

echo "  ✓ kernel/kitty.elf"
size kernel/kitty.elf
echo ""
echo "Chạy:"
echo "  qemu-system-x86_64 -kernel kernel/kitty.elf -m 128M -display curses"
