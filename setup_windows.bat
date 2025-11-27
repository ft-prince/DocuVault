@echo off
REM Quick Setup Script for Windows CMD
REM Run this after activating your virtual environment

echo ========================================
echo DocuVault RAG Setup - Windows CMD
echo ========================================
echo.

echo Step 1: Creating directories...
mkdir media\documents 2>nul
mkdir media\rag 2>nul
mkdir media\avatars 2>nul
mkdir staticfiles 2>nul
mkdir static 2>nul
echo   [OK] Directories created
echo.

echo Step 2: Verifying CUDA...
python -c "import torch; print('  CUDA available:', torch.cuda.is_available()); print('  CUDA device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
echo.

echo Step 3: Installing dependencies...
echo   This will take 5-10 minutes. Please be patient...
echo.

echo   Installing LangChain...
pip install -q langchain==0.1.20 langchain-community==0.0.38
if %errorlevel% neq 0 (
    echo   [ERROR] LangChain installation failed
    pause
    exit /b 1
)
echo   [OK] LangChain installed
echo.

echo   Installing RAG dependencies...
pip install -q sentence-transformers transformers accelerate bitsandbytes pymupdf pypdf chromadb tqdm
if %errorlevel% neq 0 (
    echo   [WARNING] Some packages may have failed
)
echo   [OK] RAG dependencies installed
echo.

echo Step 4: Verifying installations...
python -c "from langchain.memory import ConversationBufferMemory; print('  [OK] LangChain')"
python -c "from sentence_transformers import SentenceTransformer; print('  [OK] Sentence Transformers')"
python -c "import chromadb; print('  [OK] ChromaDB')"
python -c "import fitz; print('  [OK] PyMuPDF')"
echo.

echo Step 5: Running Django migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo   [ERROR] Migrations failed. Check the error above.
    pause
    exit /b 1
)
echo   [OK] Migrations completed
echo.

echo Step 6: Collecting static files...
python manage.py collectstatic --noinput
echo   [OK] Static files collected
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create superuser: python manage.py createsuperuser
echo 2. Start server: python manage.py runserver
echo 3. Open browser: http://localhost:8000
echo.
echo NOTE: AI models (~15GB) will download on first chatbot use.
echo       This may take 10-30 minutes depending on internet speed.
echo.
pause
