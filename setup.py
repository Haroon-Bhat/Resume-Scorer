"""
Setup script for Resume Parser Project
Run this script to set up the project for first-time use
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"📦 {description}...")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False


def create_directories():
    """Create necessary directories"""
    directories = ['input', 'output', 'resumes_pdf']
    
    print("\n📁 Creating directories...")
    for dir_name in directories:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        print(f"   ✓ {dir_name}/")


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"\n🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    
    print("   ✓ Python version OK")
    return True


def install_dependencies():
    """Install required packages"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies"
    )


def verify_installation():
    """Verify all modules can be imported"""
    print("\n🔍 Verifying installation...")
    
    modules = [
        ('PyPDF2', 'PDF parsing'),
        ('docx', 'DOCX parsing'),
        ('reportlab', 'PDF generation')
    ]
    
    all_ok = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"   ✓ {module} ({description})")
        except ImportError:
            print(f"   ❌ {module} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def print_usage():
    """Print usage instructions"""
    print(f"""
{'='*60}
✅ SETUP COMPLETE!
{'='*60}

📋 HOW TO USE:

1. Put your resumes in the 'input/' folder
   (Supported: PDF, DOCX, DOC, TXT)

2. Put your Job Description in the 'input/' folder
   (Filename must contain: job, jd, description, or position)

3. Run the screening:
   python screen.py --folder input --top 10

4. Find results in the 'output/' folder (CSV file)

{'='*60}
📖 For more options, see README.md
{'='*60}
""")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         RESUME PARSER PROJECT - SETUP SCRIPT              ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies. Please run manually:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Step 4: Verify installation
    if not verify_installation():
        print("\n⚠️ Some modules failed to install. Please check errors above.")
        sys.exit(1)
    
    # Step 5: Print usage
    print_usage()


if __name__ == "__main__":
    main()
