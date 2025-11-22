"""
Quick Fix Script for Missing Dependencies
Run this if you're getting import errors
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print(f"✓ {package} installed\n")

def create_directories():
    """Create necessary directories"""
    print("\nStep 4: Creating directories...")
    print("-" * 50)
    
    directories = [
        "media/documents",
        "media/rag",
        "media/avatars",
        "staticfiles",
        "static"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created/verified: {directory}")
        except Exception as e:
            print(f"✗ Failed to create {directory}: {e}")

def main():
    print("=" * 50)
    print("DocuVault RAG - Dependency Fix")
    print("=" * 50)
    print()
    
    # Critical packages with specific versions
    critical_packages = [
        "langchain==0.1.20",
        "langchain-community==0.0.38",
    ]
    
    # Other required packages
    other_packages = [
        "sentence-transformers",
        "transformers",
        "accelerate",
        "bitsandbytes",
        "pymupdf",
        "pypdf",
        "chromadb",
        "tqdm",
    ]
    
    print("Step 1: Installing critical packages...")
    print("-" * 50)
    for package in critical_packages:
        try:
            install_package(package)
        except Exception as e:
            print(f"✗ Failed to install {package}: {e}")
            print("Trying without version constraint...")
            package_name = package.split("==")[0]
            try:
                install_package(package_name)
            except:
                print(f"✗ Still failed. Please install manually: pip install {package_name}")
    
    print("\nStep 2: Installing other packages...")
    print("-" * 50)
    for package in other_packages:
        try:
            install_package(package)
        except Exception as e:
            print(f"✗ Failed to install {package}: {e}")
    
    print("\nStep 3: Verifying installations...")
    print("-" * 50)
    
    # Test imports
    tests = [
        ("Django", "import django"),
        ("PyTorch", "import torch"),
        ("LangChain", "from langchain.memory import ConversationBufferMemory"),
        ("LangChain Community", "from langchain_community.document_loaders import PyPDFLoader"),
        ("Sentence Transformers", "from sentence_transformers import SentenceTransformer"),
        ("Transformers", "import transformers"),
        ("ChromaDB", "import chromadb"),
        ("PyMuPDF", "import fitz"),
    ]
    
    all_passed = True
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name} - {e}")
            all_passed = False
    
    # Create directories
    create_directories()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All dependencies installed successfully!")
        print("✓ All directories created!")
        print("\nNext steps:")
        print("  1. python manage.py migrate")
        print("  2. python manage.py createsuperuser")
        print("  3. python manage.py runserver")
    else:
        print("⚠ Some dependencies failed to install.")
        print("\nPlease check the errors above and install manually:")
        print("  pip install <package-name>")
    print("=" * 50)

if __name__ == "__main__":
    main()
