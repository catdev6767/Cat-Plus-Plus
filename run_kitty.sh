#!/bin/bash
# Kitty OS — Verify + Boot

G='\033[92m'; R='\033[91m'; Y='\033[93m'; C='\033[96m'; B='\033[1m'; X='\033[0m'

echo ""
echo -e "${B}${C}═══════════════════════════════════════════════${X}"
echo -e "${B}${C}  Kitty OS — Verify + Boot                        ${X}"
echo -e "${B}${C}═══════════════════════════════════════════════${X}"
echo ""

# ═══ 1. VERIFY KERNEL ═══
echo -e "${B}1. Verify kernel${X}"

if [ ! -f kernel/kitty.elf ]; then
    echo -e "  ${R}✗ Chưa có kitty.elf${X}"
    echo "  Chạy: bash build_kitty.sh"
    exit 1
fi

echo "  ELF info:"
file kernel/kitty.elf | sed 's/^/    /'

echo ""
echo "  Size:"
size kernel/kitty.elf | sed 's/^/    /'

echo ""
echo "  Entry point:"
readelf -h kernel/kitty.elf | grep "Entry" | sed 's/^/    /'

echo ""
echo "  Multiboot header:"
MAGIC=$(xxd -p -l 4 kernel/kitty.elf 2>/dev/null)
# Tìm magic 0x1BADB002 trong 8KB đầu
if xxd kernel/kitty.elf 2>/dev/null | head -512 | grep -q "02b0ad1b\|1badb002"; then
    echo -e "    ${G}✓ Multiboot magic found${X}"
else
    # Kiểm tra section .multiboot
    if readelf -S kernel/kitty.elf | grep -q multiboot; then
        echo -e "    ${G}✓ Section .multiboot tồn tại${X}"
    else
        echo -e "    ${Y}⚠ Không tìm thấy magic (có thể OK)${X}"
    fi
fi

echo ""
echo "  Strings trong kernel:"
strings kernel/kitty.elf 2>/dev/null | grep -i "catos\|cat++\|hello\|kernel" | head -10 | sed 's/^/    /'

echo ""
echo -e "${G}✓ Kernel OK${X}"

# ═══ 2. CHECK QEMU ═══
echo ""
echo -e "${B}2. Kiểm tra QEMU${X}"

if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    echo -e "  ${G}✓ QEMU có sẵn${X}"
    echo "  $(qemu-system-x86_64 --version | head -1)"
    QEMU_CMD="qemu-system-x86_64"
else
    echo -e "  ${Y}⚠ Chưa có QEMU${X}"
    
    # Kiểm tra distrobox
    if command -v distrobox >/dev/null 2>&1; then
        echo ""
        echo -e "  ${C}Distrobox có sẵn → cài QEMU trong container${X}"
        
        # Kiểm tra container đã có chưa
        if distrobox list 2>/dev/null | grep -q catos; then
            echo -e "  ${G}✓ Container 'catos' đã có${X}"
        else
            echo "  Đang tạo container..."
            distrobox create --name catos --image registry.fedoraproject.org/fedora:latest --yes 2>&1 | tail -3
        fi
        
        echo ""
        echo "  Cài QEMU trong container (mất 1-2 phút)..."
        distrobox enter catos -- sudo dnf install -y qemu-system-x86 2>&1 | tail -5
        
        echo ""
        echo -e "  ${G}✓ QEMU đã cài trong container 'catos'${X}"
        echo ""
        echo -e "  ${Y}→ Sẽ chạy Kitty OS trong container${X}"
        QEMU_MODE="distrobox"
    else
        echo ""
        echo -e "  ${R}✗ Không có QEMU và không có Distrobox${X}"
        echo ""
        echo "  Cài Distrobox:"
        echo "    curl -s https://raw.githubusercontent.com/89luca89/distrobox/main/install | sh -s -- --prefix ~/.local"
        echo ""
        echo "  Hoặc dùng rpm-ostree (cần reboot):"
        echo "    sudo rpm-ostree install qemu-system-x86-core"
        echo "    sudo systemctl reboot"
        echo ""
        echo "  Kernel đã build OK. Chỉ cần QEMU để demo."
        exit 0
    fi
fi

# ═══ 3. BOOT Kitty OS ═══
echo ""
echo -e "${B}3. Boot Kitty OS${X}"
echo ""
echo -e "  ${Y}QEMU sẽ chạy kernel. Output hiện trên terminal nhờ -serial stdio.${X}"
echo -e "  ${Y}Để thoát: nhấn Ctrl+C${X}"
echo ""
echo "  ────────────────────────────────────────────"
echo ""

sleep 2

if [ "$QEMU_MODE" = "distrobox" ]; then
    # Chạy qua distrobox
    distrobox enter catos -- qemu-system-x86_64 \
        -kernel $PWD/kernel/kitty.elf \
        -m 128M \
        -display none \
        -serial stdio \
        -no-reboot
else
    # Chạy trực tiếp
    qemu-system-x86_64 \
        -kernel kernel/kitty.elf \
        -m 128M \
        -display none \
        -serial stdio \
        -no-reboot
fi

echo ""
echo "  ────────────────────────────────────────────"
echo ""
echo -e "${G}✓ Kitty OS đã dừng${X}"
echo ""

# ═══ 4. Nếu muốn xem giao diện đồ họa ═══
echo -e "${B}Muốn xem cửa sổ đồ họa?${X}"
echo "  Chạy:"
echo "    qemu-system-x86_64 -kernel kernel/kitty.elf -m 128M"
echo ""
