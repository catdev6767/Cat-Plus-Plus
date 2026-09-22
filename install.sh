
#!/bin/bash
# Cat++ + PawEditor — installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/catdev6767/Cat-Plus-Plus/main/install.sh | bash
#   OR: git clone https://github.com/catdev6767/Cat-Plus-Plus && cd Cat-Plus-Plus && ./install.sh

set -e

REPO="https://github.com/catdev6767/Cat-Plus-Plus.git"
DIR="$HOME/.catpp"
BIN="$HOME/.local/bin"

# 1. Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 required. Install Python 3.8+ first."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python: $PY_VER"

# 2. Clone or update
if [ -d "$DIR/.git" ]; then
    echo "Updating $DIR..."
    git -C "$DIR" pull --quiet --ff-only 2>/dev/null || echo "  (keep local, skip pull)"
elif [ -d "$DIR" ]; then
    echo "Warning: $DIR exists but is not a git repo"
    echo "Remove it first: rm -rf $DIR"
    exit 1
else
    echo "Cloning to $DIR..."
    git clone --depth 1 "$REPO" "$DIR"
fi

# 3. Symlinks
mkdir -p "$BIN"
ln -sf "$DIR/catpp"           "$BIN/catpp"
ln -sf "$DIR/paw/paw"         "$BIN/paw"
ln -sf "$DIR/pawedit/pawedit" "$BIN/pawedit"
chmod +x "$DIR/catpp" "$DIR/paw/paw" "$DIR/pawedit/pawedit" 2>/dev/null || true
echo "Linked: catpp paw pawedit -> $BIN"

# 4. PATH setup
SHELL_NAME=$(basename "$SHELL")
case "$SHELL_NAME" in
    fish)
        fish -c "fish_add_path $BIN" 2>/dev/null || true
        echo "fish: added $BIN to PATH"
        ;;
    zsh)
        RC="$HOME/.zshrc"
        if [ -f "$RC" ] && ! grep -q '\.local/bin' "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
            echo "zsh: added to $RC"
        fi
        ;;
    bash)
        RC="$HOME/.bashrc"
        if [ -f "$RC" ] && ! grep -q '\.local/bin' "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
            echo "bash: added to $RC"
        fi
        ;;
esac

# 5. Done
echo ""
echo "✓ Cat++ installed"
echo ""
echo "Commands:"
echo "  catpp run FILE.cat      Run a script"
echo "  catpp repl              Interactive REPL"
echo "  paw help                CLI tools"
echo "  pawedit FILE.cat        Terminal editor"
echo ""
echo "Try:"
echo "  $BIN/catpp run $DIR/examples/hello.cat"
echo "  $BIN/pawedit $DIR/examples/hello.cat"
echo ""
echo "If 'command not found', reload shell:"
echo "  bash/zsh: source ~/.bashrc (or ~/.zshrc)"
echo "  fish:     fish_add_path $BIN"
