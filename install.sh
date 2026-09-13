#!/bin/bash
# Cài catpp CLI vào ~/.local/bin
cd "$(dirname "$0")"
mkdir -p "$HOME/.local/bin"
ln -sf "$(pwd)/catpp" "$HOME/.local/bin/catpp"
echo "✓ Đã cài catpp → ~/.local/bin/catpp"
echo ""
echo "Thêm vào ~/.bashrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo ""
if ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "✓ Đã thêm vào ~/.bashrc — chạy: source ~/.bashrc"
fi
