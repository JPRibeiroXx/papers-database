# Papers Desktop Database - Launch Instructions

This document explains how to easily start the Papers Desktop Database application.

## 🚀 Quick Launch Options

You have several ways to start the app:

### 📱 **Option 1: macOS App Bundle (Recommended for Mac)**

Double-click: **`Papers Database.app`**

- Looks and behaves like a native macOS app
- Opens in Terminal automatically
- Most user-friendly option for Mac users

### 🖥️ **Option 2: Shell Script (Mac/Linux)**

Double-click: **`run_papers_app.command`**

- Works on macOS and Linux
- Opens in Terminal
- Automatically installs dependencies if needed

### 🐍 **Option 3: Python Launcher (Cross-platform)**

Double-click: **`launch_papers.py`**

- Works on any platform with Python
- May require Python to be associated with .py files
- Runs directly without showing Terminal

### 🪟 **Option 4: Windows Batch File**

Double-click: **`run_papers_app.bat`** (Windows only)

- Specifically for Windows users
- Opens in Command Prompt
- Automatically installs dependencies

## 🔧 Manual Launch (Advanced Users)

If you prefer to run manually:

```bash
# Navigate to the project directory
cd /Users/joaoribeiro/Documents/PaperDB

# Activate virtual environment
source venv/bin/activate

# Go to app directory
cd papers-desktop-app

# Run the app
python -m app.main
```

## 🐛 Troubleshooting

### App won't start

1. **Make sure Python 3.8+ is installed**
2. **Check that the virtual environment exists** (`venv` folder should be present)
3. **Try the shell script first** (`run_papers_app.command`) as it shows error messages

### Permission errors on Mac

If you get "permission denied" errors:

1. Right-click the file → Open With → Terminal
2. Or run in Terminal: `chmod +x run_papers_app.command`

### macOS Security Warning

If macOS blocks the app:

1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway" for the Papers Database app
3. Or right-click the app → Open → Open

### Dependencies missing

The launcher scripts automatically install dependencies, but if you have issues:

```bash
cd papers-desktop-app
pip install -r requirements.txt
```

## 📁 File Structure

Your PaperDB folder should contain:

```
PaperDB/
├── Papers Database.app          # ← macOS app (double-click this!)
├── run_papers_app.command      # ← Shell script launcher
├── launch_papers.py            # ← Python launcher
├── run_papers_app.bat          # ← Windows launcher
├── venv/                       # Virtual environment
├── papers-desktop-app/         # Main application
├── PDFs/                       # PDF files
├── PapersDB.xlsx              # Original Excel file
└── test_papers.db             # SQLite database
```

## 🎯 Recommended Launch Method

**For the best experience:**

- **macOS users**: Use `Papers Database.app`
- **Windows users**: Use `run_papers_app.bat`
- **Linux users**: Use `run_papers_app.command`
- **All platforms**: `launch_papers.py` works everywhere

Simply double-click your preferred launcher and the app will start! 🚀
