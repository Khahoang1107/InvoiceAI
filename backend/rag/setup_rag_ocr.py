#!/usr/bin/env python3
"""
Auto Setup Script - RAG + OCR
Tự động cài đặt dependencies cho RAG và OCR
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run command and show progress"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup process"""
    print("=" * 60)
    print("🚀 INVOICEAI - AUTO SETUP RAG + OCR")
    print("=" * 60)
    
    # Check if in backend directory
    if not os.path.exists("requirements.txt"):
        print("\n⚠️  Please run this script from the backend directory!")
        sys.exit(1)
    
    # Packages to install
    packages = [
        ("pinecone-client", "Pinecone Vector Database"),
        ("sentence-transformers", "Embedding Service"),
        ("pytesseract", "Tesseract Python Wrapper"),
        ("Pillow", "Image Processing"),
    ]
    
    print("\n📦 Installing Python packages...")
    
    for package, description in packages:
        run_command(
            f"pip install {package}",
            f"Installing {description}"
        )
    
    # Fix NumPy for EasyOCR
    print("\n🔧 Fixing NumPy compatibility...")
    run_command("pip uninstall numpy -y", "Uninstalling NumPy")
    run_command('pip install "numpy<2.0"', "Installing NumPy 1.x")
    
    # Install EasyOCR
    print("\n🎨 Installing EasyOCR...")
    run_command(
        "pip install easyocr",
        "Installing EasyOCR with dependencies"
    )
    
    # Check installations
    print("\n" + "=" * 60)
    print("✅ INSTALLATION COMPLETE!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("1. Setup Pinecone account: https://www.pinecone.io/")
    print("2. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
    print("3. Update .env file with API keys")
    print("4. Restart backend server")
    
    print("\n📚 See SETUP_RAG_OCR.md for detailed instructions")
    
    # Try to import to verify
    print("\n🧪 Verifying installations...")
    
    try:
        import pinecone
        print("✅ Pinecone: OK")
    except:
        print("❌ Pinecone: FAILED")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ Sentence Transformers: OK")
    except:
        print("❌ Sentence Transformers: FAILED")
    
    try:
        import pytesseract
        print("✅ PyTesseract: OK")
    except:
        print("❌ PyTesseract: FAILED")
    
    try:
        import easyocr
        print("✅ EasyOCR: OK")
    except:
        print("❌ EasyOCR: FAILED")
    
    print("\n🎉 Setup script completed!")

if __name__ == "__main__":
    main()
