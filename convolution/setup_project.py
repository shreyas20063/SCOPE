#!/usr/bin/env python3
"""
Complete project setup script for Convolution Simulator.

This script:
1. Installs all dependencies
2. Builds the Windows executable
3. Prepares the project for GitHub deployment
4. Validates the final structure

Usage:
    python setup_project.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class ProjectSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.dist_dir = self.project_root / "dist"
        self.assets_dir = self.project_root / "assets"
        
    def create_directory_structure(self):
        """Create required directories."""
        print("Creating directory structure...")
        
        directories = [
            "core",
            "gui", 
            "simulation",
            "assets",
            "dist"
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✓ Created: {dir_name}/")
    
    def install_dependencies(self):
        """Install required Python packages."""
        print("Installing dependencies...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
    
    def build_executable(self):
        """Build the Windows executable."""
        print("Building Windows executable...")
        
        # Check if main.py exists
        if not (self.project_root / "main.py").exists():
            print("✗ main.py not found!")
            return False
        
        # Run the build script
        try:
            subprocess.check_call([sys.executable, "build_executable.py"])
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Build failed: {e}")
            return False
    
    def validate_structure(self):
        """Validate the final project structure."""
        print("Validating project structure...")
        
        required_files = [
            "main.py",
            "requirements.txt", 
            "README.md",
            ".gitignore",
            "core/__init__.py",
            "gui/__init__.py",
            "simulation/__init__.py"
        ]
        
        required_dirs = [
            "core",
            "gui",
            "simulation", 
            "assets",
            "dist"
        ]
        
        # Check files
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        # Check directories
        missing_dirs = []
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).is_dir():
                missing_dirs.append(dir_path)
        
        if missing_files:
            print(f"✗ Missing files: {', '.join(missing_files)}")
            return False
        
        if missing_dirs:
            print(f"✗ Missing directories: {', '.join(missing_dirs)}")
            return False
        
        # Check executable
        exe_path = self.dist_dir / "convolution_simulator.exe"
        if not exe_path.exists():
            print("✗ Executable not found in dist/")
            return False
        
        print("✓ Project structure validated")
        return True
    
    def create_assets_placeholder(self):
        """Create placeholder files in assets directory."""
        print("Setting up assets...")
        
        # Create a placeholder README in assets
        assets_readme = self.assets_dir / "README.md"
        if not assets_readme.exists():
            with open(assets_readme, 'w') as f:
                f.write("""# Assets Directory

This directory contains images and other resources for the Convolution Simulator.

## Contents
- `demo_screenshot.png` - Application screenshot for README
- Additional images as needed for documentation

## Usage
Place any project-related images, icons, or documentation assets here.
""")
            print("✓ Created assets/README.md")
        
        return True
    
    def display_summary(self):
        """Display project setup summary."""
        print("\n" + "="*60)
        print("PROJECT SETUP COMPLETE!")
        print("="*60)
        
        print("\nProject Structure:")
        print("convolution-simulator/")
        print("├── main.py")
        print("├── requirements.txt")
        print("├── README.md")
        print("├── .gitignore")
        print("├── build_executable.py")
        print("├── setup_project.py")
        print("├── DEPLOYMENT.md")
        print("├── core/")
        print("├── gui/")
        print("├── simulation/")
        print("├── assets/")
        print("└── dist/")
        print("    └── convolution_simulator.exe")
        
        print("\nNext Steps:")
        print("1. Test the executable: dist/convolution_simulator.exe")
        print("2. Initialize git: git init")
        print("3. Add files: git add .")
        print("4. Commit: git commit -m 'Initial commit'")
        print("5. Create GitHub repo and push")
        print("6. Create release with executable as asset")
        
        print("\nUsage Options:")
        print("• End users: Run dist/convolution_simulator.exe")
        print("• Developers: python main.py")
        
        print("\n" + "="*60)
    
    def run_setup(self):
        """Run the complete setup process."""
        print("Convolution Simulator - Project Setup")
        print("="*40)
        
        steps = [
            ("Creating directories", self.create_directory_structure),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up assets", self.create_assets_placeholder),
            ("Building executable", self.build_executable),
            ("Validating structure", self.validate_structure)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"✗ Setup failed at: {step_name}")
                return False
        
        self.display_summary()
        return True

def main():
    """Main setup function."""
    setup = ProjectSetup()
    success = setup.run_setup()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
