#!/usr/bin/env python3
"""
ODAS Studio GUI Launcher

This script manages the setup and execution of ODAS Studio, a graphical user interface
for the ODAS (Open embeddeD Audition System) library. It handles dependency checks,
environment setup, and proper execution of the ODAS Studio application.

Features:
- Verifies and installs required dependencies (Node.js 12, Python 2.7)
- Sets up the proper environment for ODAS Studio
- Handles SSH display configurations
- Provides clear error messages and installation instructions

Usage:
    python3 src/odas/odas_gui.py

Dependencies:
    - Node.js version 12
    - Python 2.7 (installed locally in the project)
    - npm packages (automatically installed)

The script will automatically:
1. Check for required dependencies
2. Install npm dependencies if needed
3. Configure the environment
4. Launch ODAS Studio
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def setup_local_python2():
    """
    Set up a local Python 2.7 environment for the project.
    
    Returns:
        bool: True if setup successful, False otherwise.
    """
    project_root = Path(__file__).parent.parent.parent
    python_dir = project_root / ".python2"
    python_bin = python_dir / "bin" / "python2.7"
    
    if python_bin.exists():
        print(f"Local Python 2.7 already installed at {python_bin}")
        return True
    
    print("\nSetting up local Python 2.7 environment...")
    
    try:
        # Create directory for Python 2.7
        python_dir.mkdir(parents=True, exist_ok=True)
        
        if platform.system() == "Linux":
            # Download and build Python 2.7 locally
            subprocess.run([
                "curl", "-O", "https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz"
            ], cwd=python_dir, check=True)
            
            subprocess.run([
                "tar", "xzf", "Python-2.7.18.tgz"
            ], cwd=python_dir, check=True)
            
            subprocess.run([
                "./configure", f"--prefix={python_dir}", "--enable-optimizations"
            ], cwd=python_dir / "Python-2.7.18", check=True)
            
            subprocess.run([
                "make", "-j", str(os.cpu_count() or 1)
            ], cwd=python_dir / "Python-2.7.18", check=True)
            
            subprocess.run([
                "make", "install"
            ], cwd=python_dir / "Python-2.7.18", check=True)
        else:
            # For macOS, use pyenv to install Python 2.7 locally
            if not subprocess.run(["which", "pyenv"], capture_output=True).returncode == 0:
                print("Installing pyenv...")
                subprocess.run([
                    "brew", "install", "pyenv"
                ], check=True)
            
            # Install Python 2.7 locally
            subprocess.run([
                "pyenv", "install", "2.7.18"
            ], check=True)
            
            # Create a local .python-version file
            with open(project_root / ".python-version", "w") as f:
                f.write("2.7.18\n")
            
            # Set up local Python environment
            subprocess.run([
                "pyenv", "local", "2.7.18"
            ], cwd=project_root, check=True)
            
            # Create symlink to the local Python installation
            pyenv_root = subprocess.run(
                ["pyenv", "root"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
            python_bin.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(
                f"{pyenv_root}/versions/2.7.18/bin/python2.7",
                python_bin
            )
        
        print(f"Local Python 2.7 installed at {python_bin}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up local Python 2.7: {e}")
        return False

def check_node_version():
    """
    Check if Node.js version 12 is installed.
    
    Returns:
        bool: True if Node.js 12 is installed, False otherwise.
    """
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        major_version = int(version.split('.')[0].lstrip('v'))
        if major_version != 12:
            print(f"Warning: Node.js version {version} detected. ODAS Studio requires Node.js 12.")
            return False
        return True
    except FileNotFoundError:
        print("Node.js is not installed.")
        return False

def check_python2():
    """
    Check if Python 2.7 is installed and properly configured.
    
    Returns:
        bool: True if Python 2.7 is installed and accessible, False otherwise.
    """
    project_root = Path(__file__).parent.parent.parent
    python_bin = project_root / ".python2" / "bin" / "python2.7"
    
    if python_bin.exists():
        try:
            result = subprocess.run([str(python_bin), '--version'], capture_output=True, text=True)
            version = result.stdout.strip()
            if '2.7' in version:
                print(f"Local Python 2.7 detected: {version}")
                return True
        except Exception as e:
            print(f"Error checking local Python 2.7: {e}")
    
    return setup_local_python2()

def install_dependencies():
    """
    Install npm dependencies for ODAS Studio.
    
    This function:
    1. Installs npm packages using local Python 2.7
    2. Rebuilds native modules
    
    Returns:
        bool: True if installation successful, False otherwise.
    """
    print("\nInstalling dependencies...")
    try:
        project_root = Path(__file__).parent.parent.parent
        python_bin = project_root / ".python2" / "bin" / "python2.7"
        
        if not python_bin.exists():
            print("Local Python 2.7 not found. Please run the script again.")
            return False
        
        # First try to install dependencies
        try:
            subprocess.run([
                'npm', 'install',
                f'--python={python_bin}'
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: npm install failed: {e}")
            print("Continuing anyway as dependencies might be partially installed...")
        
        # Try to rebuild native modules
        try:
            subprocess.run(['npm', 'rebuild'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: npm rebuild failed: {e}")
            print("Continuing anyway as the application might still work...")
        
        return True
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

def main():
    """
    Main function that orchestrates the setup and execution of ODAS Studio.
    
    The function:
    1. Locates the odas_web directory
    2. Checks and installs dependencies
    3. Configures the environment
    4. Launches ODAS Studio
    
    Exits with status code 1 if any critical step fails.
    """
    # Get the absolute path to the odas_web directory
    odas_web_dir = Path(__file__).parent.parent.parent / "lib" / "odas_web"
    
    if not odas_web_dir.exists():
        print(f"Error: odas_web directory not found at {odas_web_dir}")
        print("Please ensure the odas_web submodule is initialized and updated.")
        sys.exit(1)
    
    # Change to odas_web directory
    os.chdir(odas_web_dir)
    
    # Check dependencies
    if not check_node_version():
        print("\nPlease install Node.js version 12 using nvm:")
        print("1. Install nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash")
        print("2. Load nvm: export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\"")
        print("3. Install Node.js 12: nvm install 12 && nvm use 12")
        sys.exit(1)
    
    if not check_python2():
        print("\nFailed to set up local Python 2.7 environment.")
        sys.exit(1)
    
    # Install dependencies if needed
    if not (odas_web_dir / "node_modules").exists():
        if not install_dependencies():
            print("\nWarning: Dependency installation had some issues, but continuing anyway...")
            print("If the application doesn't work, try running the script again.")
    
    # Set DISPLAY for SSH if needed
    if "SSH_CONNECTION" in os.environ and "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
    
    # Run odas_web
    print("\nStarting ODAS Studio...")
    try:
        subprocess.run(['npm', 'start'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running ODAS Studio: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nODAS Studio stopped by user.")

if __name__ == "__main__":
    main() 