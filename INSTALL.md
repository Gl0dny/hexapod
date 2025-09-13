# Hexapod Voice Control System - Installation Guide

[← Back to Documentation](docs/README.md) | [Next: System Overview →](docs/core/system_overview.md)

This guide will help you install the Hexapod Voice Control System as a Python package with a global command-line interface.

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Raspberry Pi OS

## Installation

```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd hexapod

# Run the installation script
./install.sh
```

The installation script will:
- Check Python version compatibility
- Install the package in development mode
- Create configuration directories
- Prompt for your Picovoice access key
- Set up configuration file with your key
- Test the installation

## Configuration

### Picovoice Access Key

The installation script will prompt you for your Picovoice access key during installation. If you don't have one yet:

**Get your free access key:**
   - Visit [Picovoice Console](https://console.picovoice.ai/)
   - Sign up for a free account
   - Generate an access key

#### Available Configuration Options

**Picovoice Configuration (Required):**
| Option | Environment Variable | Command Line | Default | Description |
|--------|---------------------|--------------|---------|-------------|
| Picovoice Key | `PICOVOICE_ACCESS_KEY` | `--access-key` | Required | Your Picovoice access key |

**Application Options:**
| Option | Command Line | Default | Description |
|--------|--------------|---------|-------------|
| Config File | `--config` | ~/.config/hexapod/.picovoice.env | Path to picovoice access_key configuration file |
| Log Level | `--log-level` | INFO | Logging level (DEBUG, INFO, USER_INFO, ODAS_USER_INFO, GAMEPAD_MODE_INFO, WARNING, ERROR, CRITICAL) |
| Log Directory | `--log-dir` | logs | Directory for log files |
| Log Config File | `--log-config-file` | hexapod/interface/logging/config/config.yaml | Path to log configuration file |
| Clean Logs | `--clean` | false | Clean all logs before running |
| Print Context | `--print-context` | false | Print Picovoice context information |

## Usage

### Basic Usage

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

## Uninstallation

To uninstall the package:

```bash
pip3 uninstall hexapod-voice-control
```

To remove configuration files:

```bash
rm -rf ~/.config/hexapod
```

```bash
# Remove log files from current directory
rm -f *.log *.log.*
```

---

[← Back to Documentation](docs/README.md) | [Next: System Overview →](docs/core/system_overview.md)
