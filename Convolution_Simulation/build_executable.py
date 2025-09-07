#!/usr/bin/env python3
"""
Build script for creating Windows executable of Convolution Simulator.

This script uses PyInstaller to create a standalone executable that includes
all dependencies and can run without requiring Python installation.

Usage:
    python build_executable.py
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print("✓ PyInstaller found")
        return True
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
        return True

def create_executable():
    """Create the Windows executable."""
    print("Building Convolution Simulator executable...")
    
    # PyInstaller command with optimized settings
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single file executable
        "--noconsole",                  # No console window (GUI only)
        "--name", "convolution_simulator",  # Output name
        "--distpath", "dist",           # Output directory
        "--workpath", "build",          # Temporary build directory
        "--specpath", ".",              # Spec file location
        "--add-data", "core;core",      # Include core module
        "--add-data", "gui;gui",        # Include gui module
        "--add-data", "simulation;simulation",  # Include simulation module
        "--hidden-import", "tkinter",
        "--hidden-import", "numpy",
        "--hidden-import", "matplotlib",
        "--hidden-import", "sympy",
        "--hidden-import", "imageio",
        "--hidden-import", "matplotlib.backends.backend_tkagg",
        "--hidden-import", "PIL",
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✓ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False

def cleanup_build_files():
    """Clean up temporary build files."""
    print("Cleaning up build files...")
    
    # Remove build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("✓ Removed build directory")
    
    # Remove spec file
    spec_file = "convolution_simulator.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print("✓ Removed spec file")

def verify_executable():
    """Verify that the executable was created and has reasonable size."""
    exe_path = os.path.join("dist", "convolution_simulator.exe")
    
    if not os.path.exists(exe_path):
        print("✗ Executable not found!")
        return False
    
    file_size = os.path.getsize(exe_path)
    size_mb = file_size / (1024 * 1024)
    
    print(f"✓ Executable created: {exe_path}")
    print(f"✓ File size: {size_mb:.1f} MB")
    
    if size_mb < 10:
        print("⚠ Warning: Executable seems unusually small. Dependencies might be missing.")
        return False
    elif size_mb > 200:
        print("⚠ Warning: Executable is quite large. Consider optimizing dependencies.")
    
    return True

def main():
    """Main build process."""
    print("=" * 60)
    print("Convolution Simulator - Executable Builder")
    print("=" * 60)
    
    # Check prerequisites
    if not check_pyinstaller():
        print("✗ Failed to install PyInstaller")
        return False
    
    # Create dist directory if it doesn't exist
    os.makedirs("dist", exist_ok=True)
    
    # Build executable
    if not create_executable():
        print("✗ Build process failed")
        return False
    
    # Verify result
    if not verify_executable():
        print("✗ Executable verification failed")
        return False
    
    # Clean up
    cleanup_build_files()
    
    print("\n" + "=" * 60)
    print("✓ BUILD COMPLETE!")
    print("✓ Executable: dist/convolution_simulator.exe")
    print("✓ Ready for distribution")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
