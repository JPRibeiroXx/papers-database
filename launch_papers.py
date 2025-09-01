#!/usr/bin/env python3
"""
Simple launcher for Papers Desktop Database
Double-click this file to start the app (if Python is associated with .py files)
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Set working directory
    os.chdir(script_dir)
    
    # Virtual environment path
    venv_path = script_dir / "venv"
    
    # Check if virtual environment exists
    if not venv_path.exists():
        print("Virtual environment not found. Please run setup first.")
        input("Press Enter to exit...")
        return
    
    # Python executable in virtual environment
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
    
    # Check if python exists in venv
    if not python_exe.exists():
        print(f"Python not found in virtual environment: {python_exe}")
        input("Press Enter to exit...")
        return
    
    # App directory
    app_dir = script_dir / "papers-desktop-app"
    if not app_dir.exists():
        print(f"App directory not found: {app_dir}")
        input("Press Enter to exit...")
        return
    
    # Change to app directory
    os.chdir(app_dir)
    
    try:
        print("Starting Papers Desktop Database...")
        # Run the application
        subprocess.run([str(python_exe), "-m", "app.main"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running application: {e}")
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
