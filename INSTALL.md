# Hexapod Voice Control System - Installation Guide

[← Back to Documentation](docs/README.md) | [Next: System Overview →](docs/core/system_overview.md)

This guide will help you install the Hexapod Voice Control 
System as a Python package with a global command-line 
interface.

## Quick Start

### Prerequisites
- Raspberry Pi 4 with [Raspberry Pi OS Lite (32-bit) - 2023-05-03](https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-05-03/)
- SSH access from development machine
- GitHub account with SSH key access

### Setup Steps
1. **MAC SSH Setup**: 
   ```bash
   ssh-keygen -R <hexapod-ip>
   ssh hexapod@<hexapod-ip>
   ```

2. **RPI SSH Setup**: 
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"

   mkdir -p ~/.ssh

   ssh-keyscan -H github.com >> ~/.ssh/known_hosts
   
   cat ~/.ssh/id_ed25519.pub
   # Add this key to GitHub at: https://github.com/settings/keys
   ```

3. **Repository Setup**: 
   ```bash
   git clone git@github.com:Gl0dny/hexapod.git
   cd hexapod/
   git submodule update --init --recursive
   ```

4. **Run Install Script**: 
   ```bash
   ./install.sh
   # or for development mode:
   ./install.sh --dev
   ```
   
> [!warning]
> **Important**: You must rerun the script after each reboot until installation completes

### Recovery
- Script is idempotent - safe to run multiple times
- Reboot markers persist until successful completion

## What the Install Script Does

### System Configuration
- Configures boot settings (UART, UART2, 32-bit kernel)
- Enables hardware interfaces (UART, I2C, SPI)
- Verifies system configuration and kernel version
- Fixes broken packages and updates system

### Development Environment
- Installs Zsh, Oh My Zsh, and development tools
- Sets up custom dotfiles and plugins
- Installs Python 3.12 (via pyenv if needed)
- Creates virtual environment

### Audio System
- Installs ODAS and seeed voicecard drivers
- Blocks kernel updates for voicecard compatibility
- Verifies audio setup and tests recording

### Python Environment
- Installs Python compilation dependencies
- Installs LLVM 15 (32-bit RPi only)
- Installs hexapod package and requirements
- Sets up Picovoice configuration

### Reboot Management
- Handles two required reboots automatically
- Continues installation after each reboot
- Cleans up reboot markers on successful completion

## Usage

```bash
# Show detailed help
hexapod --help

# Check package installation
pip3 show hexapod-voice-control

# Test configuration
hexapod --access-key "YOUR_KEY" --print-context

# Run with configuration file
hexapod --config ~/.config/hexapod/.picovoice.env

# Run with command line arguments
hexapod --access-key "YOUR_KEY" --log-level DEBUG

# Run with environment variable
PICOVOICE_ACCESS_KEY="YOUR_KEY" hexapod
```

## Configuration

### Picovoice Access Key
- Get free key from [Picovoice Console](https://console.picovoice.ai/)
- Script prompts for key during installation

### Available Options
| Option | Command Line | Default | Description |
|--------|--------------|---------|-------------|
| Picovoice Key | `--access-key` | Required | Your Picovoice access key |
| Config File | `--config` | ~/.config/hexapod/.picovoice.env | Configuration file path |
| Log Level | `--log-level` | INFO | Logging level |
| Clean Logs | `--clean` | false | Clean logs before running |

## Troubleshooting

### Voicecard Driver Issues

**Problem**: Installation gets stuck during voicecard driver verification, with infinite checking for `arecord` command.

**Symptoms**:
- Script hangs at "Testing audio recording..." step
- `arecord -l` command doesn't return or takes extremely long
- Audio device verification fails repeatedly

**Solution**: Hard reset required
1. **Power cycle the Raspberry Pi**:
   ```bash
   sudo reboot
   # If that doesn't work, physically unplug and replug power
   ```

2. **After reboot, continue installation**:
   ```bash
   ./install.sh
   # Script will resume from the appropriate phase
   ```

**Root Cause**: This issue occurs due to kernel compatibility limitations with the seeed voicecard driver:

- **Newer kernels**: Don't work at all with the voicecard driver
- **Older kernels**: Would work fine with the voicecard driver but aren't compatible with other parts of the system
- **Current kernel (5.4.51-v7l+)**: The compromise solution - works with both the voicecard driver and other system components, but may occasionally hang during initial verification due to:
  - Kernel compatibility edge cases in the driver code
  - Hardware timing issues during driver initialization
  - System resource constraints during audio device enumeration

**Note**: This hanging issue is hardware-dependent and currently has no known solution. The system is designed to comply with this limitation. If the hardware boots without this issue, everything works properly. The driver is production-stable and will work correctly once the system is fully booted and the driver is properly loaded. However, there have been individual cases where the driver can also get stuck during system initialization, requiring a hard reset to resolve.

### Controller Pairing

To pair a PlayStation controller with the system:

```bash
# Start Bluetooth control
bluetoothctl

# In bluetoothctl, run these commands:
scan on
# Wait for "Wireless Controller" or "DualSense" to appear
# Note the MAC address (e.g., 00:11:22:33:44:55)
  
# Stop scanning
scan off

# Pair with your controller (replace XX:XX:XX:XX:XX:XX with actual MAC)
pair XX:XX:XX:XX:XX:XX

# Trust the device
trust XX:XX:XX:XX:XX:XX

# Connect
connect XX:XX:XX:XX:XX:XX

# paired check
paired-devices
# info about specific device
info XX:XX:XX:XX:XX:XX
# connected check
devices

# test with linux
ls /dev/input/js*
sudo apt install joystick
jstest /dev/input/js0

# disconnecting
disconnect 88:03:4C:14:82:C8
# forgetting
remove 88:03:4C:14:82:C8

# Exit
quit
```

## Uninstallation

To uninstall the Python package:
```bash
pip3 uninstall hexapod-voice-control
```

To remove configuration files:
```bash
rm -rf ~/.config/hexapod
rm -f *.log *.log.*
```

---

[← Back to Documentation](docs/README.md) | [Next: System Overview →](docs/core/system_overview.md)