#!/bin/bash

# Hexapod Voice Control System Installation Script
# This script installs the hexapod package and sets up the configuration

set -e  # Exit on any error

# Global variables
CONFIG_DIR="$HOME/.config/hexapod"

# Function to check Python version
check_python_version() {
    echo "Checking Python version..."
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.12"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "Error: Python 3.12 or higher is required. Found: $python_version"
        exit 1
    fi

    echo "Python version check passed: $python_version"
}

# Function to install the package
install_package() {
    if pip3 show hexapod-voice-control >/dev/null 2>&1; then
        echo "Package 'hexapod-voice-control' is already installed."
        echo "Skipping installation."
    else
        echo "Installing hexapod package..."
        pip3 install -e .
    fi
}

# Function to install development dependencies
install_dev_dependencies() {
    echo "Installing development dependencies..."
    pip3 install -e .[dev]
    echo "Development dependencies installed successfully!"
}

# Function to create directories
create_directories() {
    echo "Creating configuration directories..."
    mkdir -p "$CONFIG_DIR"
    echo "Configuration directory: $CONFIG_DIR"
}

# Function to get Picovoice access key from user
get_picovoice_key() {
    
    while true; do
        read -p "Enter your Picovoice Access Key: " picovoice_key
        if [ -n "$picovoice_key" ]; then
            break
        else
            echo "Access key cannot be empty. Please try again."
        fi
    done
    
    echo "$picovoice_key"
}

# Function to set up Picovoice configuration
setup_picovoice_config() {
    if [ ! -f "$CONFIG_DIR/.picovoice.env" ]; then
        echo "Setting up Picovoice configuration..."
        local picovoice_key=$(get_picovoice_key)
        
        # Create configuration file with the provided key
        cat > "$CONFIG_DIR/.picovoice.env" << EOF
# Picovoice Access Key Configuration
# Generated during installation

PICOVOICE_ACCESS_KEY=$picovoice_key
EOF
        
        echo "Configuration file created at: $CONFIG_DIR/.picovoice.env"
    else
        echo "Configuration file already exists at: $CONFIG_DIR/.picovoice.env"
        echo "Skipping Picovoice key setup."
    fi
}

# Function to test installation
test_installation() {
    echo "Testing installation..."
    if command -v hexapod &> /dev/null; then
        echo "Global 'hexapod' command is available"
        return 0
    else
        echo "Error: Global 'hexapod' command not found"
        echo "   Try running: source ~/.bashrc or restart your terminal"
        return 1
    fi
}

# Function to display success message
show_success_message() {
    local dev_mode="$1"
    
    echo ""
    echo "Installation completed successfully!"
    echo ""
    echo "Configuration file created at: $CONFIG_DIR/.picovoice.env"
    echo ""
    
    if [[ "$dev_mode" == true ]]; then
        echo "Development tools installed:"
        echo "  - black (code formatter)"
        echo "  - flake8 (linter)"
        echo "  - pytest (testing framework)"
        echo "  - pytest-cov (test coverage)"
        echo "  - mypy (type checker)"
        echo ""
        echo "Run development tools with:"
        echo "  black .              # Format code"
        echo "  flake8 .             # Check code style"
        echo "  pytest               # Run tests"
        echo "  pytest --cov=hexapod # Run tests with coverage"
        echo "  mypy hexapod/        # Check types"
        echo ""
    fi
    
    echo "You can now run the hexapod system with:"
    echo "  hexapod"
    echo "  hexapod --help"
    echo "  hexapod --config $CONFIG_DIR/.picovoice.env"
    echo "  hexapod --access-key YOUR_PICOVOICE_KEY --log-level INFO --clean"
}

# Main installation function
main() {
    local dev_mode=false
    
    # Check for --dev flag
    if [[ "$1" == "--dev" ]]; then
        dev_mode=true
        echo "Installing Hexapod Voice Control System (Development Mode)..."
    else
        echo "Installing Hexapod Voice Control System..."
    fi
    
    check_python_version
    install_package
    
    if [[ "$dev_mode" == true ]]; then
        install_dev_dependencies
    fi
    
    create_directories
    setup_picovoice_config
    
    if test_installation; then
        show_success_message "$dev_mode"
    else
        exit 1
    fi
}

# Run main function
main "$@"