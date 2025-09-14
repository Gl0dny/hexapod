#!/bin/bash

# Hexapod Voice Control System Installation Script
# This script installs the hexapod package and sets up the configuration

set -e  # Exit on any error

# Global variables
CONFIG_DIR="$HOME/.config/hexapod"
PHASE_1_MARKER="$HOME/.hexapod_install_phase_1"
PHASE_2_MARKER="$HOME/.hexapod_install_phase_2"
LOG_DIR="$HOME/hexapod/logs"
LOG_FILE="$LOG_DIR/hexapod_install.log"

# Function to get current timestamp
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Function to log messages with timestamp
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(get_timestamp)
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Log to file with timestamp
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Print to appropriate output stream
    if [ "$level" = "ERROR" ]; then
        # Errors go to stderr
        echo "[$timestamp] [$level] $message" >&2
    else
        # Info, warnings, success go to stdout
        echo "[$timestamp] [$level] $message"
    fi
}

# Function to log info messages
log_info() {
    log_message "INFO" "$1"
}

# Function to log warning messages
log_warning() {
    log_message "WARN" "$1"
}

# Function to log error messages
log_error() {
    log_message "ERROR" "$1"
}

# Function to log success messages
log_success() {
    log_message "SUCCESS" "$1"
}

# Function to log step headers
log_step() {
    local step="$1"
    log_info "=========================================="
    log_info "STEP: $step"
    log_info "=========================================="
}

# Function to initialize logging
init_logging() {
    log_info "Starting Hexapod Voice Control System Installation"
    log_info "Installation script version: $(basename "$0")"
    log_info "User: $(whoami)"
    log_info "Hostname: $(hostname)"
    log_info "Working directory: $(pwd)"
    log_info "Log file: $LOG_FILE"
}

# Function to verify kernel version 6.1.21-v7l+ (after first reboot)
verify_kernel_version_6_1_21() {
    local kernel_version=$(uname -r)
    log_info "Kernel version: $kernel_version"
    
    # Check if we're on the correct kernel (6.1.21-v7l+)
    if [[ "$kernel_version" == *"6.1.21-v7l+"* ]]; then
        log_success "Correct kernel version 6.1.21-v7l+ detected"
        return 0
    else
        log_warning "Expected kernel 6.1.21-v7l+, found: $kernel_version"
        log_warning "This may cause compatibility issues with ODAS and voicecard drivers"
        log_warning "Use: raspios_lite_armhf-2023-05-03 image for stable voicecard support"
        return 1
    fi
}

# Function to verify kernel version 5.4.51-v7l+ and audio drivers (after second reboot)
verify_kernel_and_audio_drivers() {
    local kernel_version=$(uname -r)
    log_info "Kernel version: $kernel_version"
    
    # Check if we're on the correct kernel (5.4.51-v7l+)
    if [[ "$kernel_version" == *"5.4.51-v7l+"* ]]; then
        log_success "Correct kernel version 5.4.51-v7l+ detected"
    else
        log_warning "Expected kernel 5.4.51-v7l+, found: $kernel_version"
        log_warning "This may cause compatibility issues with voicecard drivers"
    fi
    
    # Check audio devices with arecord -l
    log_info "Checking audio devices with arecord -l..."
    if command -v arecord >/dev/null 2>&1; then
        log_info "Audio devices found:"
        arecord -l | while read line; do
            log_info "  $line"
        done
        
        # Check if seeed device is available
        if arecord -l | grep -q "seeed8micvoicec"; then
            log_success "Seeed 8-mic voicecard detected and working"
        else
            log_warning "Seeed 8-mic voicecard not detected"
        fi
    else
        log_warning "arecord not found, audio drivers may not be working"
    fi
}

# Function to clean up reboot markers
cleanup_phase_markers() {
    log_info "Cleaning up phase markers..."
    rm -f "$PHASE_1_MARKER"
    rm -f "$PHASE_2_MARKER"
    log_success "Phase markers cleaned up successfully"
}


# Function to check if boot configuration is already done
check_boot_config_done() {
    local config_file="/boot/config.txt"
    
    if [ ! -f "$config_file" ]; then
        return 1
    fi
    
    # Check if all required settings are already present
    if grep -q "^enable_uart=1" "$config_file" && \
       grep -q "^dtoverlay=uart2" "$config_file" && \
       grep -q "^arm_64bit=0" "$config_file"; then
        return 0
    fi
    
    return 1
}

# Function to configure boot settings and hardware interfaces
configure_boot_and_hardware() {
    log_step "CONFIGURING BOOT SETTINGS AND HARDWARE INTERFACES"
    
    local config_file="/boot/config.txt"
    
    # Check if we're on Raspberry Pi
    if [ ! -f "$config_file" ]; then
        log_warning "Not running on Raspberry Pi, skipping boot configuration"
        return 0
    fi
    
    # Check if boot configuration is already done
    if check_boot_config_done; then
        log_success "Boot configuration already complete, skipping..."
        return 0
    fi
    
    log_info "Using config file: $config_file"
    
    local needs_reboot=false
    
    # Enable UART
    if ! grep -q "^enable_uart=1" "$config_file"; then
        log_info "Enabling UART..."
        echo "enable_uart=1" | sudo tee -a "$config_file" > /dev/null
        needs_reboot=true
    fi
    
    # Enable UART2 for Maestro
    if ! grep -q "^dtoverlay=uart2" "$config_file"; then
        log_info "Enabling UART2 for Maestro..."
        echo "dtoverlay=uart2" | sudo tee -a "$config_file" > /dev/null
        needs_reboot=true
    fi
    
    # Set 32-bit kernel
    if ! grep -q "^arm_64bit=0" "$config_file"; then
        log_info "Setting 32-bit kernel..."
        echo "arm_64bit=0" | sudo tee -a "$config_file" > /dev/null
        needs_reboot=true
    fi
    
    # Configure hardware interfaces via raspi-config (also requires reboot)
    log_info "Enabling UART, I2C, and SPI interfaces..."
    sudo raspi-config nonint do_serial 0  # Enable UART
    sudo raspi-config nonint do_i2c 0     # Enable I2C
    sudo raspi-config nonint do_spi 0     # Enable SPI
    
    if [ "$needs_reboot" = true ]; then
        log_info "Boot and hardware configuration completed. Reboot required for changes to take effect."
        log_info "Creating phase 1 marker..."
        echo "phase_1_complete" > "$PHASE_1_MARKER"
        log_info "Rebooting in 5 seconds..."
        sleep 5
        sudo reboot
    else
        log_success "Boot and hardware configuration already complete."
    fi
}

# Function to check if hardware configuration is already done
check_hardware_config_done() {
    # Check if UART, I2C, and SPI are already enabled
    if [ -e /dev/ttyAMA0 ] && [ -e /dev/i2c-1 ] && [ -e /dev/spidev0.0 ]; then
        return 0
    fi
    return 1
}

# Function to check if system verification was already done
check_system_verification_done() {
    # Check if verification marker exists
    if [ -f "$HOME/.hexapod_system_verified" ]; then
        return 0
    fi
    return 1
}

# Function to verify hardware setup and kernel after reboot
verify_hardware_and_kernel() {
    log_step "VERIFYING HARDWARE SETUP AND KERNEL AFTER REBOOT"
    
    # Check kernel version 6.1.21-v7l+
    verify_kernel_version_6_1_21
    
    # Check UART devices
    log_info "Checking UART devices..."
    if [ -e /dev/ttyAMA0 ]; then
        log_success "/dev/ttyAMA0 available"
    else
        log_warning "/dev/ttyAMA0 not found"
    fi
    
    if [ -e /dev/ttyAMA2 ]; then
        log_success "/dev/ttyAMA2 available (UART2 for Maestro)"
    else
        log_warning "/dev/ttyAMA2 not found"
    fi
    
    # Check I2C devices
    log_info "Checking I2C devices..."
    if [ -e /dev/i2c-1 ]; then
        log_success "I2C device available"
        if command -v i2cdetect >/dev/null 2>&1; then
            log_info "I2C devices:"
            i2cdetect -y 1 | while read line; do
                log_info "  $line"
            done
        fi
    else
        log_warning "I2C device not found"
    fi
    
    # Check SPI devices
    log_info "Checking SPI devices..."
    if [ -e /dev/spidev0.0 ]; then
        log_success "SPI device available"
    else
        log_warning "SPI device not found"
    fi
    
    log_success "Hardware setup and kernel verification completed."
}


# Function to verify system configuration
verify_system() {
    log_step "VERIFYING SYSTEM CONFIGURATION"
    
    # Check if system verification was already done
    if check_system_verification_done; then
        log_success "System verification already completed, skipping..."
        return 0
    fi
    
    # Check if we're running on the expected Raspberry Pi OS image
    log_info "Expected Raspberry Pi OS image:"
    log_info "  Index of /raspios_lite_armhf/images/raspios_lite_armhf-2023-05-03"
    log_info "  This specific image is required for voicecard compatibility (stable)"
    log_info ""
    
    # Check audio devices
    log_info "Checking audio devices..."
    if command -v arecord >/dev/null 2>&1; then
        log_info "Audio devices found:"
        arecord -l | while read line; do
            log_info "  $line"
        done
    else
        log_warning "arecord not found, install alsa-utils"
    fi
    
    # Check UART devices
    log_info "Checking UART devices..."
    if [ -e /dev/ttyAMA0 ]; then
        log_success "/dev/ttyAMA0 available"
    else
        log_warning "/dev/ttyAMA0 not found"
    fi
    
    if [ -e /dev/ttyAMA2 ]; then
        log_success "/dev/ttyAMA2 available (UART2 for Maestro)"
    else
        log_warning "/dev/ttyAMA2 not found"
    fi
    
    # Check I2C devices
    log_info "Checking I2C devices..."
    if [ -e /dev/i2c-1 ]; then
        log_success "I2C device available"
        if command -v i2cdetect >/dev/null 2>&1; then
            log_info "I2C devices:"
            i2cdetect -y 1 | while read line; do
                log_info "  $line"
            done
        fi
    else
        log_warning "I2C device not found"
    fi
    
    # Check SPI devices
    log_info "Checking SPI devices..."
    if [ -e /dev/spidev0.0 ]; then
        log_success "SPI device available"
    else
        log_warning "SPI device not found"
    fi
    
    # Create verification marker
    log_info "System verification complete"
    log_success "System verification completed."
}

# Function to update system
update_system() {
    log_info "Updating system packages..."
    
    # Update package lists
    log_info "Updating package lists..."
    sudo apt update
    
    # Upgrade packages
    log_info "Upgrading packages..."
    sudo apt upgrade -y
    
    # Clean up
    log_info "Cleaning up packages..."
    sudo apt autoremove -y
}

# Function to fix broken packages
fix_broken_packages() {
    log_info "Fixing broken packages..."
    
    # Always try to fix broken packages first
    log_info "Attempting to fix broken packages..."
    sudo apt --fix-broken install -y
    
    # Update package lists
    log_info "Updating package lists..."
    sudo apt update
    
    # Clean up
    log_info "Cleaning up packages..."
    sudo apt autoremove -y
}


# Function to install Python compilation dependencies
install_python_dependencies() {
    log_info "Installing Python compilation dependencies..."
    
    # Fix broken packages first
    fix_broken_packages
    
    # Install pygame dependencies
    log_info "Installing pygame dependencies (SDL2)..."
    sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
    
    # Install audio compilation libraries
    log_info "Installing audio compilation libraries..."
    sudo apt install -y libportmidi-dev libfreetype6-dev libavformat-dev libswscale-dev libsmpeg-dev libjpeg-dev libtiff5-dev libx11-dev libxext-dev portaudio19-dev libopenblas0
    
    log_success "Python compilation dependencies installed successfully"
}

# Function to check and install Python version
check_python_version() {
    log_info "Checking Python version..."
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.12"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_warning "Python 3.12 or higher is required. Found: $python_version"
        log_info "Installing Python 3.12 using pyenv..."
        
        # Install Python build dependencies first
        log_info "Installing Python build dependencies..."
        sudo apt update
        sudo apt install -y \
            build-essential \
            libssl-dev \
            libbz2-dev \
            libreadline-dev \
            libsqlite3-dev \
            libncursesw5-dev \
            libffi-dev \
            liblzma-dev \
            zlib1g-dev \
            libgdbm-dev \
            libnss3-dev \
            libncurses-dev
        
        # Install pyenv if not already installed
        if ! command -v pyenv >/dev/null 2>&1; then
            log_info "Installing pyenv..."
            curl https://pyenv.run | bash
            
            # Add pyenv to bash configuration
            log_info "Configuring pyenv for bash..."
            echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
            echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
            echo 'eval "$(pyenv init -)"' >> ~/.bashrc
            
            # Load pyenv in current session
            export PYENV_ROOT="$HOME/.pyenv"
            export PATH="$PYENV_ROOT/bin:$PATH"
            eval "$(pyenv init -)"
        fi
        
        # Install Python 3.12.0
        log_info "Installing Python 3.12.0..."
        pyenv install 3.12.0
        
        # Set as global version
        pyenv global 3.12.0
        pyenv shell 3.12.0
        
        # Verify installation
        local new_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_success "Python installation complete. Version: $new_version"
    else
        log_success "Python version check passed: $python_version"
    fi
}

# Function to install the package
install_package() {
    local dev_mode="$1"
    
    if pip3 show hexapod-voice-control >/dev/null 2>&1; then
        log_info "Package 'hexapod-voice-control' is already installed."
        if [[ "$dev_mode" == true ]]; then
            log_info "Installing development dependencies..."
            pip3 install -e .[dev]
            log_success "Development dependencies installed successfully!"
        else
            log_info "Skipping installation."
        fi
    else
        if [[ "$dev_mode" == true ]]; then
            log_info "Installing hexapod package with development dependencies..."
            pip3 install -e .[dev]
        else
            log_info "Installing hexapod package..."
            pip3 install -e .
        fi
    fi
}

# Function to create configuration directories
create_config_directories() {
    log_info "Creating configuration directories..."
    mkdir -p "$CONFIG_DIR"
    log_success "Configuration directory created: $CONFIG_DIR"
}


# Function to install ODAS
install_odas() {
    log_step "INSTALLING ODAS"
    
    # Check if already installed by looking for ODAS command
        if command -v odas >/dev/null 2>&1; then
        log_info "ODAS already installed, skipping..."
        return 0
    fi
    
    cd "$HOME"
    
    # Install ODAS
    if [[ -f "hexapod/lib/odas/install.sh" ]]; then
        log_info "Installing ODAS..."
        ./hexapod/lib/odas/install.sh
        log_success "ODAS installation complete"
    else
        log_warning "ODAS install script not found, skipping..."
    fi
}

# Function to install seeed voicecard driver
install_seeed_driver() {
    log_step "INSTALLING SEED VOICECARD DRIVER"
    
    if [[ -d "hexapod/firmware/seeed-voicecard" ]]; then
        log_info "Installing seeed voicecard driver..."
        cd hexapod/firmware/seeed-voicecard
        git checkout hexapod
        sudo ./install.sh --compat-kernel
        cd "$HOME"
        
        # Create phase 2 marker and reboot
        log_info "Creating phase 2 marker..."
        echo "phase_2_complete" > "$PHASE_2_MARKER"
        log_info "Seeed voicecard driver installed. Rebooting to activate drivers..."
        log_info "The installation will continue automatically after reboot."
        log_info "Rebooting in 5 seconds..."
        sleep 5
        sudo reboot
    else
        log_warning "Seeed voicecard directory not found, skipping..."
    fi
}


# Function to verify audio setup
verify_audio_setup() {
    log_info "Verifying audio setup..."
    
    # Check if audio devices are available
    if command -v arecord >/dev/null 2>&1; then
        log_info "Audio devices found:"
        arecord -l
    else
        log_warning "arecord not found, audio may not be properly configured"
    fi
    
    # Test audio recording if seeed device is available
    if arecord -l | grep -q "seeed8micvoicec"; then
        log_info "Testing audio recording..."
        arecord -D hw:CARD=seeed8micvoicec,DEV=0 -d 3 -r 48000 -c 8 -f s32_le test.wav
        if [[ -f "test.wav" ]]; then
            log_success "Audio test successful - test.wav created"
            rm -f test.wav
        else
            log_error "Audio test failed"
        fi
    else
        log_warning "Seeed 8-mic voicecard not detected"
    fi
}

# Function to install LLVM 15 for 32-bit RPi
install_llvm() {
    log_info "Installing LLVM 15 for 32-bit RPi..."
    
    # Check if already installed
    if command -v llvm-config >/dev/null 2>&1 && [[ "$(llvm-config --version | cut -d. -f1)" == "15" ]]; then
        log_info "LLVM 15 already installed, skipping..."
        return 0
    fi
    
    # Check if we're on 32-bit system
    if [[ "$(uname -m)" != "armv7l" ]]; then
        log_info "Not on 32-bit ARM system, skipping LLVM installation..."
        return 0
    fi
    
    log_info "Setting up swap for LLVM compilation..."
    # Increase swap size
    sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    log_info "Installing build dependencies..."
    sudo apt update
    sudo apt install -y build-essential cmake ninja-build git python3-pip \
        libncurses5-dev libxml2-dev libedit-dev zlib1g-dev
    
    log_info "Cloning and building LLVM 15..."
    cd /tmp
    if [[ ! -d "llvm-project" ]]; then
        git clone https://github.com/llvm/llvm-project.git
    fi
    cd llvm-project
    git checkout llvmorg-15.0.7
    
    mkdir -p build && cd build
    cmake -G Ninja ../llvm \
        -DCMAKE_BUILD_TYPE=Release \
        -DLLVM_TARGETS_TO_BUILD="ARM" \
        -DLLVM_ENABLE_PROJECTS="clang" \
        -DCMAKE_INSTALL_PREFIX=/usr/local
    
    log_info "Building LLVM (this will take a long time)..."
    ninja -j$(nproc)
    sudo ninja install
    
    log_info "Installing Python packages that depend on LLVM..."
    export LLVM_CONFIG=/usr/local/bin/llvm-config
    pip install llvmlite numba resampy
    
    # Revert swap changes
    sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=100/' /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    log_success "LLVM 15 installation complete"
}

# Function to show controller setup instructions
show_controller_setup() {
    cat << EOF

=== CONTROLLER SETUP ===
To pair a PlayStation controller:

1. Start Bluetooth control:
   bluetoothctl

2. In bluetoothctl, run these commands:
   scan on
   # Wait for 'Wireless Controller' or 'DualSense' to appear
   # Note the MAC address (e.g., 00:11:22:33:44:55)
   scan off

3. Pair with your controller (replace XX:XX:XX:XX:XX:XX with actual MAC):
   pair XX:XX:XX:XX:XX:XX
   trust XX:XX:XX:XX:XX:XX
   connect XX:XX:XX:XX:XX:XX

4. Test the controller:
   ls /dev/input/js*
   sudo apt install joystick
   jstest /dev/input/js0

5. To disconnect:
   disconnect XX:XX:XX:XX:XX:XX
   remove XX:XX:XX:XX:XX:XX
   quit

EOF
}

# Function to validate Picovoice access key format
validate_picovoice_key() {
    local key="$1"
    
    # Check if key is not empty
    if [ -z "$key" ]; then
        log_error "Access key cannot be empty."
        return 1
    fi
    
    # Check length (Picovoice keys are exactly 56 characters)
    local key_length=${#key}
    if [ "$key_length" -ne 56 ]; then
        log_error "Invalid key length. Picovoice keys are exactly 56 characters long (got $key_length)."
        log_error "Your key: '$key'"
        return 1
    fi
    
    # Check if key contains only valid Base64 characters
    if ! echo "$key" | grep -q '^[A-Za-z0-9+/=]*$'; then
        log_error "Invalid key format. Picovoice keys contain only letters, numbers, +, /, and = characters."
        log_error "Your key: '$key'"
        return 1
    fi
    
    # Check if key doesn't start with common prefixes that might be copied incorrectly
    if echo "$key" | grep -q '^PICOVOICE_ACCESS_KEY='; then
        log_error "Please enter only the key value, not the full environment variable line."
        return 1
    fi
    
    return 0
}

# Function to show Picovoice key requirements
show_picovoice_requirements() {
    cat << EOF

Get your free Picovoice Access Key from: https://console.picovoice.ai/

Picovoice Access Key requirements:
  - Length: Exactly 56 characters
  - Characters: Letters, numbers, +, /, and = only
  - Format: Base64 encoded string

EOF
}

# Function to get Picovoice access key from user (only outputs the key)
get_picovoice_key() {
    while true; do
        read -p "Enter your Picovoice Access Key: " picovoice_key
        
        # Clean up the input - remove any extra text and keep only the key
        picovoice_key=$(echo "$picovoice_key" | sed 's/^PICOVOICE_ACCESS_KEY=//' | tr -d '[:space:]')
        
        # Validate the key
        if ! validate_picovoice_key "$picovoice_key"; then
            echo -e "\nPlease try again.\n" >&2
        else
            break
        fi
    done
    
    echo "$picovoice_key"
}

# Function to set up Picovoice configuration
setup_picovoice_config() {
    if [ ! -f "$CONFIG_DIR/.picovoice.env" ]; then
        log_info "Setting up Picovoice configuration..."
        show_picovoice_requirements
        local picovoice_key=$(get_picovoice_key)
        
        # Create configuration file with the provided key
        cat > "$CONFIG_DIR/.picovoice.env" << EOF
# Picovoice Access Key Configuration
# Generated during installation

PICOVOICE_ACCESS_KEY=$picovoice_key
EOF
        
        log_success "Configuration file created at: $CONFIG_DIR/.picovoice.env"
    else
        log_info "Configuration file already exists at: $CONFIG_DIR/.picovoice.env"
        log_info "Skipping Picovoice key setup."
    fi
}

# Function to test installation
test_installation() {
    log_info "Testing installation..."
    if command -v hexapod &> /dev/null; then
        log_success "Global 'hexapod' command is available"
        return 0
    else
        log_error "Global 'hexapod' command not found"
        log_error "Try running: source ~/.bashrc or restart your terminal"
        return 1
    fi
}

# Function to display help
show_help() {
    cat << EOF
Hexapod Voice Control System - Installation Script

Usage: $0 [OPTIONS]

Options:
  --dev     Install with development dependencies (black, flake8, pytest, pytest-cov, mypy)
  --help    Show this help message

Examples:
  $0                # Standard installation
  $0 --dev          # Development installation with dev tools
  $0 --help         # Show this help

The script will automatically:
  - Configure boot settings and hardware interfaces (UART, UART2, I2C, SPI, 32-bit kernel)
  - Verify hardware setup and kernel after first reboot
  - Install ODAS (triggers 2nd reboot)
  - Set up virtual environment and Python dependencies
  - Install pygame and audio compilation dependencies
  - Check Python version compatibility (3.12+)
  - Install the hexapod package and dependencies
  - Install LLVM 15 (32-bit RPi only)
  - Verify audio setup and test recording
  - Create configuration directories
  - Prompt for Picovoice Access Key
  - Set up configuration file
  - Test the complete installation
EOF
}

# Function to display success message
show_success_message() {
    local dev_mode="$1"
    
    cat << EOF

Installation completed successfully!

Configuration file created at: $CONFIG_DIR/.picovoice.env

EOF

    if [[ "$dev_mode" == true ]]; then
        cat << EOF
Development tools installed:
  - black (code formatter)
  - flake8 (linter)
  - pytest (testing framework)
  - pytest-cov (test coverage)
  - mypy (type checker)

Run development tools with:
  black .              # Format code
  flake8 .             # Check code style
  pytest               # Run tests
  pytest --cov=hexapod # Run tests with coverage
  mypy hexapod/        # Check types

EOF
    fi
    
    cat << EOF
You can now run the hexapod system with:
  hexapod
  hexapod --help
  hexapod --config $CONFIG_DIR/.picovoice.env
  hexapod --access-key YOUR_PICOVOICE_KEY --log-level INFO --clean

=== AUTOMATED SETUP COMPLETE ===
The following components have been automatically configured:
  ✓ Boot and hardware configuration (UART, UART2, I2C, SPI, 32-bit kernel)
  ✓ Hardware setup and kernel verification after first reboot
  ✓ ODAS installation (2nd reboot)
  ✓ Virtual environment and Python setup
  ✓ Pygame and audio compilation dependencies
  ✓ Hexapod package installation
  ✓ LLVM 15 installation (32-bit RPi only)
  ✓ Audio device verification

=== NEXT STEPS ===
1. Reboot if prompted for audio driver changes:
   sudo reboot

2. After reboot, verify audio setup:
   arecord -l

3. Test audio recording:
   arecord -D hw:CARD=seeed8micvoicec,DEV=0 -d 3 -r 48000 -c 8 -f s32_le test.wav

EOF
    show_controller_setup
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
                log_error "Unknown option: $arg"
                log_error "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Show help if requested
    if [[ "$show_help_flag" == true ]]; then
        show_help
        exit 0
    fi
    
    # Initialize logging
    init_logging
    
    # Determine installation phase based on phase markers
    local phase="unknown"
    
    if [ -f "$PHASE_1_MARKER" ] && [ -f "$PHASE_2_MARKER" ]; then
        phase="phase_3"
    elif [ -f "$PHASE_1_MARKER" ]; then
        phase="phase_2"
    else
        phase="phase_1"
    fi
    
    log_info "Installation phase: $phase"
    
    # PHASE 1: First run - configure boot and hardware
    if [[ "$phase" == "phase_1" ]]; then
        configure_boot_and_hardware
        # If we reach here, no reboot was needed, continue with ODAS installation
        install_odas
        install_seeed_driver
    fi
    
    # PHASE 2: After first reboot - install ODAS and seeed driver
    if [[ "$phase" == "phase_2" ]]; then
        verify_hardware_and_kernel
        install_odas
        install_seeed_driver
    fi
    
    # PHASE 3: After second reboot - final setup and Python installation
    if [[ "$phase" == "phase_3" ]]; then
        verify_kernel_and_audio_drivers
        
        # Block kernel updates after ODAS installation
        log_info "Blocking kernel updates for voicecard compatibility..."
        sudo apt-mark hold raspberrypi-kernel
        log_info "Kernel updates blocked. Current holds:"
        apt-mark showhold | while read line; do
            log_info "  $line"
        done
        
        # Update system
        log_step "UPDATING SYSTEM"
        fix_broken_packages
        update_system
        
        # Install system dependencies and Python
        log_step "INSTALLING SYSTEM DEPENDENCIES AND PYTHON"
        install_python_dependencies
        check_python_version
        
        # Upgrade pip system-wide
        log_info "Upgrading pip..."
        pip3 install --upgrade pip
        
        # Install LLVM before Python package (required for some Python packages)
        log_step "INSTALLING LLVM 15 (32-BIT RPI ONLY)"
        install_llvm
        
        # Install Python package
        if [[ "$dev_mode" == true ]]; then
            log_info "Installing Hexapod Voice Control System (Development Mode)..."
        else
            log_info "Installing Hexapod Voice Control System..."
        fi
        install_package "$dev_mode"
        
        log_step "VERIFYING AUDIO SETUP"
        verify_audio_setup
    fi
    
    log_step "CREATING CONFIGURATION DIRECTORIES AND SETUP"
    create_config_directories
    setup_picovoice_config
    
    if test_installation; then
        # Clean up reboot markers only after successful completion
        cleanup_phase_markers
        show_success_message "$dev_mode"
    else
        log_error "Installation test failed"
        exit 1
    fi
}

# Run main function
main "$@"