# Quick Setup Script for Windows
# Run this after activating your virtual environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DocuVault RAG Setup - Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create directories
Write-Host "Step 1: Creating directories..." -ForegroundColor Yellow
$directories = @("media\documents", "media\rag", "media\avatars", "staticfiles", "static")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ $dir already exists" -ForegroundColor Gray
    }
}

# Step 2: Verify CUDA
Write-Host "`nStep 2: Verifying CUDA..." -ForegroundColor Yellow
python -c "import torch; print(f'  ✓ CUDA available: {torch.cuda.is_available()}'); print(f'  ✓ CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Step 3: Install dependencies
Write-Host "`nStep 3: Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This will take 5-10 minutes. Please be patient..." -ForegroundColor Gray

# Install LangChain with specific versions
Write-Host "`n  Installing LangChain..." -ForegroundColor Cyan
pip install -q langchain==0.1.20 langchain-community==0.0.38
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ LangChain installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ LangChain installation failed" -ForegroundColor Red
    exit 1
}

# Install other RAG dependencies
Write-Host "`n  Installing RAG dependencies..." -ForegroundColor Cyan
$packages = @(
    "sentence-transformers",
    "transformers",
    "accelerate",
    "bitsandbytes",
    "pymupdf",
    "pypdf",
    "chromadb",
    "tqdm"
)

foreach ($package in $packages) {
    Write-Host "    Installing $package..." -ForegroundColor Gray
    pip install -q $package
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ $package installed" -ForegroundColor Green
    } else {
        Write-Host "    ✗ $package failed" -ForegroundColor Red
    }
}

# Step 4: Verify installations
Write-Host "`nStep 4: Verifying installations..." -ForegroundColor Yellow

$verifications = @(
    @("Django", "import django; print(f'Django {django.get_version()}')"),
    @("PyTorch", "import torch; print(f'PyTorch {torch.__version__}')"),
    @("LangChain", "from langchain.memory import ConversationBufferMemory; print('LangChain OK')"),
    @("Transformers", "import transformers; print(f'Transformers {transformers.__version__}')"),
    @("ChromaDB", "import chromadb; print('ChromaDB OK')")
)

foreach ($verify in $verifications) {
    $name = $verify[0]
    $code = $verify[1]
    try {
        $result = python -c $code 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $name - $result" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $name - Error" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ✗ $name - Error" -ForegroundColor Red
    }
}

# Step 5: Run migrations
Write-Host "`nStep 5: Running Django migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Migrations completed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Migrations failed" -ForegroundColor Red
    Write-Host "`nPlease check the error above and fix it before continuing." -ForegroundColor Red
    exit 1
}

# Step 6: Collect static files
Write-Host "`nStep 6: Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Static files collected" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Static files collection had warnings (this is usually OK)" -ForegroundColor Yellow
}

# Done
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Create superuser: python manage.py createsuperuser" -ForegroundColor White
Write-Host "2. Start server: python manage.py runserver" -ForegroundColor White
Write-Host "3. Open browser: http://localhost:8000" -ForegroundColor White
Write-Host "`n⚠ Note: AI models (~15GB) will download on first chatbot use." -ForegroundColor Yellow
Write-Host "   This may take 10-30 minutes depending on your internet speed." -ForegroundColor Yellow
Write-Host ""
