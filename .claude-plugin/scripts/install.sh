#!/bin/bash
# Auto-install local-brain binary from GitHub releases

set -e

REPO="IsmaelMartinez/local-brain"
INSTALL_DIR="${HOME}/.local/bin"

# Check if already installed
if command -v local-brain &> /dev/null; then
    echo "local-brain is already installed: $(which local-brain)"
    exit 0
fi

# Detect platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$OS" in
    linux)
        case "$ARCH" in
            x86_64) TARGET="x86_64-unknown-linux-gnu" ;;
            aarch64) TARGET="aarch64-unknown-linux-gnu" ;;
            *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
        esac
        EXT="tar.gz"
        ;;
    darwin)
        case "$ARCH" in
            x86_64) TARGET="x86_64-apple-darwin" ;;
            arm64) TARGET="aarch64-apple-darwin" ;;
            *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
        esac
        EXT="tar.gz"
        ;;
    *)
        echo "Unsupported OS: $OS (only macOS and Linux are supported)"
        exit 1
        ;;
esac

# Get latest release version
VERSION=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$VERSION" ]; then
    echo "Could not determine latest version. Please install manually."
    echo "See: https://github.com/$REPO/releases"
    exit 1
fi

# Download URL
FILENAME="local-brain-${TARGET}.${EXT}"
URL="https://github.com/$REPO/releases/download/$VERSION/$FILENAME"

echo "Installing local-brain $VERSION for $TARGET..."

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download and extract
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "Downloading from $URL..."
curl -sL "$URL" -o "$FILENAME"

if [ "$EXT" = "tar.gz" ]; then
    tar -xzf "$FILENAME"
else
    unzip -q "$FILENAME"
fi

# Install binary
chmod +x local-brain
mv local-brain "$INSTALL_DIR/"

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo "Installed local-brain to $INSTALL_DIR/local-brain"

# Check if in PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo ""
    echo "NOTE: Add $INSTALL_DIR to your PATH:"
    echo "  export PATH=\"\$PATH:$INSTALL_DIR\""
fi

echo "Done!"
