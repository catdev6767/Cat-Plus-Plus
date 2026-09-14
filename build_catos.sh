#!/bin/bash
# CatOS build script
set -e
cd "$(dirname "$0")"

echo "🐱 CatOS build"
echo "=============="

# 1. Transpile Cat++ → C
echo ""
echo "1. Transpile kernel/demo.cat → C"
python3 tools/transpiler.py kernel/demo.cat -o kernel/demo.c

# Đổi tên main → catpp_main
sed -i 's/int main(void)/int catpp_main(void)/' kernel/demo.c

echo "  ✓ kernel/demo.c"

# 2. Compile kernel
echo ""
echo "2. Compile kernel (freestanding)"

CFLAGS="-m32 -ffreestanding -fno-pic -fno-stack-protector -fno-builtin -nostdlib -nostdinc -Wall -O2"
CFLAGS="$CFLAGS -I libc -I runtime"

# Entry
gcc $CFLAGS -c kernel/entry.s -o kernel/entry.o
echo "  ✓ entry.o"

# Runtime
gcc $CFLAGS -DCATPP_FREESTANDING -c runtime/catpp_freestanding.c -o kernel/rt.o
echo "  ✓ rt.o"

# Main kernel
gcc $CFLAGS -DCATPP_FREESTANDING -c kernel/main.c -o kernel/main.o
echo "  ✓ main.o"

# Cat++ demo
gcc $CFLAGS -DCATPP_FREESTANDING -c kernel/demo.c -o kernel/demo.o
echo "  ✓ demo.o"

# 3. Link
echo ""
echo "3. Link"
GCC_LIB=$(gcc -m32 -print-libgcc-file-name)
ld -m elf_i386 -T kernel/linker.ld -nostdlib \
   kernel/entry.o kernel/main.o kernel/rt.o kernel/demo.o \
   $GCC_LIB \
   -o kernel/catos.elf
echo "  ✓ catos.elf"

# 4. Kiểm tra
echo ""
echo "4. Kiểm tra binary"
file kernel/catos.elf
size kernel/catos.elf

# 5. Tạo ISO
echo ""
echo "5. Tạo ISO"
mkdir -p iso/boot/grub
cp kernel/catos.elf iso/boot/catos.elf

cat > iso/boot/grub/grub.cfg << 'GRUBEOF'
set timeout=0
set default=0

menuentry "CatOS" {
    multiboot /boot/catos.elf
    boot
}
GRUBEOF

if command -v grub2-mkrescue >/dev/null 2>&1; then
    grub2-mkrescue -o catos.iso iso 2>/dev/null
elif command -v grub-mkrescue >/dev/null 2>&1; then
    grub-mkrescue -o catos.iso iso 2>/dev/null
else
    echo "  ⚠ Không có grub-mkrescue — bỏ qua bước tạo ISO"
    echo "    Cài: sudo dnf install grub2-tools xorriso"
fi

if [ -f catos.iso ]; then
    echo "  ✓ catos.iso ($(du -h catos.iso | cut -f1))"
fi

echo ""
echo "════════════════════════════════════════"
echo "  BUILD XONG"
echo "════════════════════════════════════════"
echo ""
if [ -f catos.iso ]; then
    echo "Chạy:"
    echo "  qemu-system-x86_64 -cdrom catos.iso"
    echo ""
    echo "Hoặc:"
    echo "  make run-catos"
fi
