#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🐱 Felis OS build v0.2"
echo ""

CFLAGS="-m32 -ffreestanding -fno-pic -fno-stack-protector -fno-builtin -nostdlib -nostdinc -Wall -Wno-unused-function -O2 -DCATPP_FREESTANDING"
CFLAGS="$CFLAGS -I libc -I runtime -I kernel"

echo "Compile:"
for f in entry.s irq.s idt.c keyboard.c string.c fs.c commands.c shell.c utils.c main.c; do
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
   kernel/utils.o kernel/main.o \
   $GCC_LIB \
   -o kernel/felis.elf

echo "  ✓ kernel/felis.elf"
size kernel/felis.elf
echo ""
echo "Chạy:"
echo "  qemu-system-x86_64 -kernel kernel/felis.elf -m 128M -display curses"
