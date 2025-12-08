#!/bin/bash
# Auto-install local-brain Python package

set -e

# Check if already installed
if command -v local-brain &> /dev/null; then
    echo "local-brain is already installed: $(which local-brain)"
    local-brain --version
    exit 0
fi

# Try different installation methods in order of preference
install_with_uv() {
    if command -v uv &> /dev/null; then
        echo "Installing with uv..."
        uv pip install local-brain
        return 0
    fi
    return 1
}

install_with_pipx() {
    if command -v pipx &> /dev/null; then
        echo "Installing with pipx..."
        pipx install local-brain
        return 0
    fi
    return 1
}

install_with_pip() {
    if command -v pip3 &> /dev/null; then
        echo "Installing with pip3..."
        pip3 install --user local-brain
        return 0
    elif command -v pip &> /dev/null; then
        echo "Installing with pip..."
        pip install --user local-brain
        return 0
    fi
    return 1
}

# Try installation methods
if install_with_uv; then
    echo "Done!"
elif install_with_pipx; then
    echo "Done!"
elif install_with_pip; then
    echo "Done!"
    echo ""
    echo "NOTE: You may need to add ~/.local/bin to your PATH:"
    echo "  export PATH=\"\$PATH:\$HOME/.local/bin\""
else
    echo "Error: Could not find uv, pipx, or pip."
    echo "Please install Python and pip first, then run:"
    echo "  pip install local-brain"
    exit 1
fi

# Verify installation
if command -v local-brain &> /dev/null; then
    echo ""
    echo "Installed successfully!"
    local-brain --version
else
    echo ""
    echo "Installation completed, but 'local-brain' not found in PATH."
    echo "You may need to restart your shell or add the install location to PATH."
fi
