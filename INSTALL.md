# Hexapod Voice Control System - Installation Guide

This guide will help you install the Hexapod Voice Control System as a Python package with a global command-line interface.

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Linux-based system (tested on Raspberry Pi OS)

## Quick Installation

### Option 1: Automated Installation (Recommended)

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
- Set up example configuration file
- Test the installation

### Option 2: Manual Installation

```bash
# Install the package
pip3 install -e .

# Create configuration directory
mkdir -p ~/.config/hexapod

# Copy the configuration file
cp .env.picovoice ~/.config/hexapod/.env

# Edit the configuration with your Picovoice key
nano ~/.config/hexapod/.env
```

## Configuration

### Setting up Picovoice Access Key

1. **Get your free access key:**
   - Visit [Picovoice Console](https://console.picovoice.ai/)
   - Sign up for a free account
   - Generate an access key

2. **Configure the key using one of these methods:**

   **Method A: Configuration file (Recommended)**
   ```bash
   # Edit the configuration file
   nano ~/.config/hexapod/.env
   
   # Set your access key
   PICOVOICE_ACCESS_KEY=your_actual_access_key_here
   ```

   **Method B: Environment variable**
   ```bash
   export PICOVOICE_ACCESS_KEY="your_actual_access_key_here"
   ```

   **Method C: Command line argument**
   ```bash
   hexapod --access-key "your_actual_access_key_here"
   ```

### Configuration Options

The system supports multiple configuration methods with the following priority (highest to lowest):

1. Command line arguments
2. Environment variables
3. `.env` configuration file
4. Default values

#### Available Configuration Options

**Picovoice Configuration (Required):**
| Option | Environment Variable | Command Line | Default | Description |
|--------|---------------------|--------------|---------|-------------|
| Picovoice Key | `PICOVOICE_ACCESS_KEY` | `--access-key` | Required | Your Picovoice access key |

**Application Options:**
| Option | Command Line | Default | Description |
|--------|--------------|---------|-------------|
| Log Level | `--log-level` | INFO | Logging level (DEBUG, INFO, USER_INFO, ODAS_USER_INFO, GAMEPAD_MODE_INFO, WARNING, ERROR, CRITICAL) |
| Log Directory | `--log-dir` | logs | Directory for log files |
| Log Config File | `--log-config-file` | hexapod/interface/logging/config/config.yaml | Path to log configuration file |
| Clean Logs | `--clean` | false | Clean all logs before running |
| Print Context | `--print-context` | false | Print Picovoice context information |

## Usage

### Basic Usage

```bash
# Run with configuration file
hexapod --config ~/.config/hexapod/.env

# Run with command line arguments
hexapod --access-key "YOUR_KEY" --log-level DEBUG

# Run with environment variable
PICOVOICE_ACCESS_KEY="YOUR_KEY" hexapod

# Show help
hexapod --help
```

### Advanced Usage

```bash
# Run with debug logging
hexapod --access-key "YOUR_KEY" --log-level DEBUG

# Run with custom log directory
hexapod --access-key "YOUR_KEY" --log-dir /tmp/hexapod_logs

# Run with user info logging level
hexapod --access-key "YOUR_KEY" --log-level USER_INFO

# Clean logs before running
hexapod --access-key "YOUR_KEY" --clean

# Print Picovoice context information
hexapod --access-key "YOUR_KEY" --print-context

# Run with custom log configuration
hexapod --access-key "YOUR_KEY" --log-config-file /path/to/custom/logging.yaml
```

## File Locations

After installation, the following files and directories are created:

- **Configuration:** `~/.config/hexapod/.env`
- **Logs:** `~/.local/share/hexapod/logs/`
- **Package data:** Installed in your Python environment
- **Global command:** `hexapod` (available system-wide)

## Troubleshooting

### Common Issues

1. **"PICOVOICE_ACCESS_KEY is not set" error:**
   - Make sure you've set your access key using one of the configuration methods above
   - Verify the key is correct by checking it at the Picovoice console

2. **"Global 'hexapod' command not found":**
   - Try restarting your terminal or running `source ~/.bashrc`
   - Check if the package was installed correctly: `pip3 show hexapod-voice-control`

3. **Audio device issues:**
   - The system automatically detects the ReSpeaker 6 microphone array
   - List available audio devices: `python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)['name']}') for i in range(p.get_device_count())]"`
   - The system will automatically find devices containing 'seeed-8mic-voicecard' in the name

4. **Permission errors:**
   - Make sure you have the necessary permissions for audio devices
   - On Raspberry Pi, you may need to add your user to the audio group: `sudo usermod -a -G audio $USER`

### Getting Help

```bash
# Show detailed help
hexapod --help

# Check package installation
pip3 show hexapod-voice-control

# Test configuration
hexapod --access-key "YOUR_KEY" --print-context
```

## Development

For development purposes, you can install the package in editable mode:

```bash
pip3 install -e .
```

This allows you to modify the source code without reinstalling the package.

## Uninstallation

To uninstall the package:

```bash
pip3 uninstall hexapod-voice-control
```

To remove configuration files:

```bash
rm -rf ~/.config/hexapod
rm -rf ~/.local/share/hexapod
```
