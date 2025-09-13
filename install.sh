 #!/bin/bash

# Hexapod Voice Control System Installation Script
# This script installs the hexapod package and sets up the configuration

set -e  # Exit on any error

echo "Installing Hexapod Voice Control System..."

# Check if Python 3.12+ is available
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.12"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.12 or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Install the package in development mode
echo "Installing hexapod package..."
pip3 install -e .

# Create configuration directory
config_dir="$HOME/.config/hexapod"
mkdir -p "$config_dir"

# Copy the configuration file if it doesn't exist
if [ ! -f "$config_dir/.env" ]; then
    echo "Creating configuration file..."
    cp .env.picovoice "$config_dir/.env"
    echo "Configuration file created at: $config_dir/.env"
    echo ""
    echo "IMPORTANT: You need to set your Picovoice Access Key!"
    echo "   1. Get your free access key from: https://console.picovoice.ai/"
    echo "   2. Edit the configuration file: $config_dir/.env"
    echo "   3. Replace 'your_picovoice_access_key_here' with your actual key"
    echo ""
else
    echo "Configuration file already exists at: $config_dir/.env"
fi

# Create logs directory
logs_dir="$HOME/.local/share/hexapod/logs"
mkdir -p "$logs_dir"
echo "Logs directory created at: $logs_dir"

# Test the installation
echo "Testing installation..."
if command -v hexapod &> /dev/null; then
    echo "Global 'hexapod' command is available"
    echo ""
    echo "Installation completed successfully!"
    echo ""
    echo "Usage examples:"
    echo "  hexapod --help                           # Show help"
    echo "  hexapod --access-key YOUR_KEY            # Run with access key"
    echo "  hexapod --config $config_dir/.env        # Use config file"
    echo "  PICOVOICE_ACCESS_KEY=YOUR_KEY hexapod    # Use environment variable"
    echo ""
    echo "Configuration file: $config_dir/.env"
    echo "Logs directory: $logs_dir"
else
    echo "Error: Global 'hexapod' command not found"
    echo "   Try running: source ~/.bashrc or restart your terminal"
    exit 1
fi