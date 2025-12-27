# Deployment Guide - Convolution Simulator

This guide provides step-by-step instructions for building the Windows executable and preparing the project for GitHub deployment.

## Prerequisites

- Python 3.7+ installed
- Git installed
- Windows environment (for .exe building)

## Step 1: Environment Setup

```bash
# Clone or navigate to project directory
cd convolution-simulator

# Install all dependencies including build tools
pip install -r requirements.txt
```

## Step 2: Build Windows Executable

### Automatic Build (Recommended)
```bash
python build_executable.py
```

### Manual Build
```bash
# Install PyInstaller if not already installed
pip install pyinstaller

# Create executable
pyinstaller --onefile --noconsole --name convolution_simulator \
    --add-data "core;core" --add-data "gui;gui" --add-data "simulation;simulation" \
    --hidden-import tkinter --hidden-import numpy --hidden-import matplotlib \
    --hidden-import sympy --hidden-import imageio main.py

# Move executable to proper location
mkdir -p dist
move dist/convolution_simulator.exe dist/convolution_simulator.exe
```

## Step 3: Verify Build

The executable should be created at `dist/convolution_simulator.exe` with:
- File size: 50-150 MB (typical range)
- Runs without Python installation
- All GUI features functional

Test the executable:
```bash
# Navigate to dist directory
cd dist

# Run executable
./convolution_simulator.exe
```

## Step 4: Clean Project Structure

Ensure your project has this structure:
```
convolution-simulator/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── DEPLOYMENT.md               # This guide
├── .gitignore                  # Git ignore rules
├── build_executable.py         # Build script
│
├── core/                       # Core logic
│   ├── __init__.py
│   ├── convolution.py
│   ├── signals.py
│   └── utils.py
│
├── gui/                        # GUI components
│   ├── __init__.py
│   ├── main_window.py
│   ├── controls.py
│   ├── plotting.py
│   └── themes.py
│
├── simulation/                 # Simulation control
│   ├── __init__.py
│   ├── continuous.py
│   ├── discrete.py
│   └── playback.py
│
├── assets/                     # Images and resources
│   └── demo_screenshot.png
│
└── dist/                       # Distribution files
    └── convolution_simulator.exe
```

## Step 5: GitHub Preparation

### 5.1 Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: Convolution Simulator v1.0"
```

### 5.2 Create GitHub Repository
1. Go to GitHub and create a new repository named `convolution-simulator`
2. Don't initialize with README (we already have one)

### 5.3 Connect and Push
```bash
git remote add origin https://github.com/YOUR_USERNAME/convolution-simulator.git
git branch -M main
git push -u origin main
```

### 5.4 Create Release
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `Convolution Simulator v1.0.0`
5. Upload the `convolution_simulator.exe` file as a release asset
6. Write release notes describing features

## Step 6: Documentation Updates

Ensure these files are properly configured:

### README.md
- [x] Installation instructions for both executable and source
- [x] Usage instructions
- [x] Feature descriptions
- [x] Signal syntax guide
- [x] Build instructions

### .gitignore
- [x] Excludes `__pycache__/`
- [x] Excludes build artifacts (`build/`, `dist/`, `*.spec`)
- [x] Excludes OS files (`.DS_Store`, `Thumbs.db`)
- [x] Excludes IDE files

## Distribution Checklist

Before releasing, verify:

- [ ] Executable runs on clean Windows machine (no Python)
- [ ] All demo modes function correctly
- [ ] Custom signal input works
- [ ] Animation controls respond properly
- [ ] Export functions (PNG, CSV, GIF) work
- [ ] Dark/light themes switch correctly
- [ ] Mathematical expressions parse correctly
- [ ] No console errors during normal operation

## Troubleshooting

### Build Issues
- **Import errors**: Add missing modules to `--hidden-import` flags
- **File not found**: Ensure all modules are included with `--add-data`
- **Large executable**: Consider using `--exclude-module` for unused packages

### Runtime Issues
- **Slow startup**: Normal for first run, PyInstaller extraction
- **Missing plots**: Check matplotlib backend compatibility
- **Expression errors**: Verify sympy integration in executable

### Git Issues
- **Large files**: Ensure `.gitignore` excludes executables
- **Missing files**: Check that all source files are tracked
- **LFS needed**: For files >100MB, consider Git LFS

## Maintenance

### Version Updates
1. Update version numbers in relevant files
2. Rebuild executable: `python build_executable.py`
3. Test thoroughly
4. Create new GitHub release
5. Update documentation as needed

### Dependency Updates
1. Update `requirements.txt`
2. Test compatibility
3. Rebuild and test executable
4. Document any breaking changes
