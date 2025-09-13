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
    local dev_mode="$1"
    
    if pip3 show hexapod-voice-control >/dev/null 2>&1; then
        echo "Package 'hexapod-voice-control' is already installed."
        if [[ "$dev_mode" == true ]]; then
            echo "Installing development dependencies..."
            pip3 install -e .[dev]
            echo "Development dependencies installed successfully!"
        else
            echo "Skipping installation."
        fi
    else
        if [[ "$dev_mode" == true ]]; then
            echo "Installing hexapod package with development dependencies..."
            pip3 install -e .[dev]
        else
            echo "Installing hexapod package..."
            pip3 install -e .
        fi
    fi
}

# Function to create directories
create_directories() {
    echo "Creating configuration directories..."
    mkdir -p "$CONFIG_DIR"
    echo "Configuration directory: $CONFIG_DIR"
}

# Function to validate Picovoice access key format
validate_picovoice_key() {
    local key="$1"
    
    # Check if key is not empty
    if [ -z "$key" ]; then
        echo "ERROR: Access key cannot be empty." >&2
        return 1
    fi
    
    # Check length (Picovoice keys are exactly 56 characters)
    local key_length=${#key}
    if [ "$key_length" -ne 56 ]; then
        echo "ERROR: Invalid key length. Picovoice keys are exactly 56 characters long (got $key_length)." >&2
        echo "       Your key: '$key'" >&2
        return 1
    fi
    
    # Check if key contains only valid Base64 characters
    if ! echo "$key" | grep -q '^[A-Za-z0-9+/=]*$'; then
        echo "ERROR: Invalid key format. Picovoice keys contain only letters, numbers, +, /, and = characters." >&2
        echo "       Your key: '$key'" >&2
        return 1
    fi
    
    # Check if key doesn't start with common prefixes that might be copied incorrectly
    if echo "$key" | grep -q '^PICOVOICE_ACCESS_KEY='; then
        echo "ERROR: Please enter only the key value, not the full environment variable line." >&2
        return 1
    fi
    
    echo "SUCCESS: Key format is valid!" >&2
    return 0
}

# Function to show Picovoice key requirements
show_picovoice_requirements() {
    echo ""
    echo "Get your free Picovoice Access Key from: https://console.picovoice.ai/"
    echo ""
    echo "Picovoice Access Key requirements:"
    echo "  - Length: Exactly 56 characters"
    echo "  - Characters: Letters, numbers, +, /, and = only"
    echo "  - Format: Base64 encoded string"
    echo ""
}

# Function to get Picovoice access key from user (only outputs the key)
get_picovoice_key() {
    while true; do
        read -p "Enter your Picovoice Access Key: " picovoice_key
        
        # Clean up the input - remove any extra text and keep only the key
        picovoice_key=$(echo "$picovoice_key" | sed 's/^PICOVOICE_ACCESS_KEY=//' | tr -d '[:space:]')
        
        # Validate the key
        if ! validate_picovoice_key "$picovoice_key"; then
            echo "" >&2
            echo "Please try again." >&2
            echo "" >&2
        else
            break
        fi
    done
    
    echo "$picovoice_key"
}

# Function to set up Picovoice configuration
setup_picovoice_config() {
    if [ ! -f "$CONFIG_DIR/.picovoice.env" ]; then
        echo "Setting up Picovoice configuration..."
        show_picovoice_requirements
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

# Function to display help
show_help() {
    echo "Hexapod Voice Control System - Installation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev     Install with development dependencies (black, flake8, pytest, pytest-cov, mypy)"
    echo "  --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Standard installation"
    echo "  $0 --dev          # Development installation with dev tools"
    echo "  $0 --help         # Show this help"
    echo ""
    echo "The script will:"
    echo "  - Check Python version compatibility (3.12+)"
    echo "  - Install the hexapod package"
    echo "  - Create configuration directories"
    echo "  - Prompt for Picovoice Access Key"
    echo "  - Set up configuration file"
    echo "  - Test the installation"
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
    local show_help_flag=false
    
    # Parse all arguments
    for arg in "$@"; do
        case $arg in
            --help|-h)
                show_help_flag=true
                ;;
            --dev)
                dev_mode=true
                ;;
            *)
                echo "Unknown option: $arg"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Show help if requested
    if [[ "$show_help_flag" == true ]]; then
        show_help
        exit 0
    fi
    
    # Determine installation mode
    if [[ "$dev_mode" == true ]]; then
        echo "Installing Hexapod Voice Control System (Development Mode)..."
    else
        echo "Installing Hexapod Voice Control System..."
    fi
    
    check_python_version
    install_package "$dev_mode"
    
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