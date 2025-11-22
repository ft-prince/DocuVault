# DocuVault RAG Chatbot - Deployment Guide for Remote GPU Server

## 🖥️ System Requirements

### Hardware
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3070, RTX 4090, A6000, etc.)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB free space (for models and documents)
- **CPU**: 8+ cores recommended

### Software
- **OS**: Ubuntu 20.04/22.04 or Windows Server 2019+
- **Python**: 3.10 or 3.11
- **CUDA**: 11.8 or 12.1
- **Git**: For cloning repository

---

## 📋 Step-by-Step Installation

### Step 1: Prepare the Server

#### For Ubuntu/Linux:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10 and dependencies
sudo apt install python3.10 python3.10-venv python3.10-dev -y

# Install build essentials
sudo apt install build-essential libssl-dev libffi-dev -y

# Install CUDA (if not already installed)
# Follow: https://developer.nvidia.com/cuda-downloads

# Verify GPU
nvidia-smi
```

#### For Windows Server:
```powershell
# Install Python 3.10 from python.org
# Install CUDA Toolkit from NVIDIA website
# Install Visual Studio Build Tools

# Verify GPU
nvidia-smi
```

---

### Step 2: Clone the Repository

```bash
# Navigate to desired directory
cd /home/your-username/  # Linux
# or
cd C:\Users\YourUser\    # Windows

# Clone repository
git clone https://github.com/ft-prince/DocuVault.git
cd DocuVault

# Switch to ragchatbot branch
git checkout ragchatbot
```

---

### Step 3: Create Virtual Environment

#### Linux:
```bash
# Create virtual environment
python3.10 -m venv venv

# Activate
source venv/bin/activate
```

#### Windows:
```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate
```

---

### Step 4: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install base Django dependencies
pip install -r requirements.txt

# Install RAG-specific dependencies
pip install -r requirements_rag.txt

# Install PyTorch with CUDA support
# For CUDA 11.8:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify PyTorch GPU support
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"}')"
```

**Expected Output:**
```
CUDA available: True
CUDA device: NVIDIA GeForce RTX 4090 (or your GPU model)
```

---

### Step 5: Configure Django Settings

```bash
# Create necessary directories
mkdir -p media/documents media/rag media/avatars staticfiles static

# Set proper permissions (Linux only)
chmod -R 755 media static
```

Edit `config/settings.py` if needed:
```python
# For production, update these:
DEBUG = False  # Set to False in production
ALLOWED_HOSTS = ['your-server-ip', 'your-domain.com']

# Optionally configure database (default is SQLite)
```

---

### Step 6: Initialize Database

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

---

### Step 7: Download AI Models (Important!)

The models will be downloaded automatically on first use, but you can pre-download them:

```bash
# Pre-download models (optional but recommended)
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer

print('Downloading embedding model...')
SentenceTransformer('Qwen/Qwen3-Embedding-0.6B', device='cuda')

print('Downloading LLM model...')
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B')
# Note: Full LLM download happens on first chatbot query
print('Models ready!')
"
```

**Model Storage Locations:**
- Linux: `~/.cache/huggingface/`
- Windows: `C:\Users\YourUser\.cache\huggingface\`

**Total Download Size:** ~15GB (be patient, takes 10-30 minutes depending on internet)

---

### Step 8: Collect Static Files (Production)

```bash
python manage.py collectstatic --noinput
```

---

### Step 9: Test the Application

```bash
# Run development server
python manage.py runserver 0.0.0.0:8000

# Access from browser:
# http://your-server-ip:8000
```

---

### Step 10: Index Sample Documents

1. **Login** to the application
2. **Upload a PDF document** via the Documents section
3. **Go to the document detail page**
4. **Click "Index Document"** to add it to the RAG system
5. **Navigate to AI Assistant** from the top menu
6. **Start asking questions!**

---

## 🚀 Production Deployment

### Option A: Using Gunicorn (Linux)

```bash
# Install gunicorn
pip install gunicorn

# Create systemd service file
sudo nano /etc/systemd/system/docuvault.service
```

**Service File Content:**
```ini
[Unit]
Description=DocuVault DMS with RAG
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/path/to/DocuVault
Environment="PATH=/path/to/DocuVault/venv/bin"
ExecStart=/path/to/DocuVault/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable docuvault
sudo systemctl start docuvault
sudo systemctl status docuvault
```

### Option B: Using Nginx as Reverse Proxy

```bash
# Install nginx
sudo apt install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/docuvault
```

**Nginx Config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location /static/ {
        alias /path/to/DocuVault/staticfiles/;
    }

    location /media/ {
        alias /path/to/DocuVault/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/docuvault /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 Configuration & Optimization

### GPU Memory Optimization

If you encounter CUDA out of memory errors, edit `documents/rag/config.py`:

```python
# Reduce batch size
EMBEDDING_BATCH_SIZE = 8  # Default is 16

# Or use smaller models
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Smaller alternative
LLM_MODEL = "Qwen/Qwen2.5-1.5B"  # Smaller LLM
```

### Performance Tuning

```python
# In config.py
CHUNK_SIZE = 512  # Larger = fewer chunks, faster but less granular
N_RESULTS = 3     # Fewer results = faster retrieval
MAX_NEW_TOKENS = 256  # Shorter responses = faster generation
```

---

## 📊 Monitoring & Maintenance

### Check System Status

```bash
# View logs
tail -f /var/log/syslog  # Linux
# or check systemd logs
sudo journalctl -u docuvault -f

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check Django errors
python manage.py check --deploy
```

### Database Backup

```bash
# Backup SQLite database
cp db.sqlite3 db.sqlite3.backup

# Backup media files
tar -czf media_backup.tar.gz media/
```

### Update Application

```bash
cd /path/to/DocuVault
git pull origin ragchatbot
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements_rag.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart docuvault  # if using systemd
```

---

## 🐛 Troubleshooting

### Issue: CUDA Out of Memory
**Solution:**
- Reduce `EMBEDDING_BATCH_SIZE` in `documents/rag/config.py`
- Use smaller models
- Close other GPU applications

### Issue: Models not downloading
**Solution:**
```bash
# Check internet connection
ping huggingface.co

# Manually download models
huggingface-cli download Qwen/Qwen3-Embedding-0.6B
huggingface-cli download Qwen/Qwen2.5-7B
```

### Issue: Import errors
**Solution:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements_rag.txt
```

### Issue: ChromaDB errors
**Solution:**
```bash
# Delete and recreate vector database
rm -rf media/rag/chroma_db
# Then re-index documents from the UI
```

### Issue: Slow responses
**Solution:**
- Ensure GPU is being used: Check with `nvidia-smi` during query
- Reduce `MAX_NEW_TOKENS` in config
- Use smaller models
- Enable model caching (done automatically)

### Issue: Permission denied errors (Linux)
**Solution:**
```bash
sudo chown -R your-username:www-data /path/to/DocuVault
chmod -R 755 /path/to/DocuVault/media
chmod -R 755 /path/to/DocuVault/static
```

---

## 📱 Accessing the Application

### Local Development
```
http://localhost:8000
```

### Remote Server
```
http://your-server-ip:8000
# or with nginx
http://your-domain.com
```

### Admin Panel
```
http://your-server-ip:8000/admin/
```

---

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in `config/settings.py`
- [ ] Set `DEBUG = False` in production
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use HTTPS (Let's Encrypt with Certbot)
- [ ] Set up firewall (UFW on Linux)
- [ ] Use strong passwords for superuser
- [ ] Regular backups
- [ ] Keep dependencies updated

---

## 📈 Usage Workflow

1. **Admin creates user accounts** via Django admin
2. **Users upload PDF documents** via Documents page
3. **Documents are indexed** (manually or automatically)
4. **Users query the AI Assistant** about their documents
5. **System retrieves relevant info** and generates answers
6. **Chat history is saved** per session

---

## 🎯 Quick Commands Reference

```bash
# Start server
python manage.py runserver 0.0.0.0:8000

# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Check for errors
python manage.py check

# Test RAG system standalone
python test_rag.py

# Shell access
python manage.py shell
```

---

## 📞 Support & Resources

- **GitHub Issues**: [https://github.com/ft-prince/DocuVault/issues](https://github.com/ft-prince/DocuVault/issues)
- **Django Docs**: [https://docs.djangoproject.com/](https://docs.djangoproject.com/)
- **PyTorch CUDA**: [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)
- **HuggingFace Models**: [https://huggingface.co/Qwen](https://huggingface.co/Qwen)

---

## ✅ Verification Steps

After deployment, verify:

1. **GPU Detection**: `python -c "import torch; print(torch.cuda.is_available())"`
2. **Django Check**: `python manage.py check --deploy`
3. **Access Web UI**: Can you login and see dashboard?
4. **Upload Document**: Can you upload a PDF?
5. **Index Document**: Does indexing complete successfully?
6. **Query Chatbot**: Does the AI respond with relevant answers?
7. **Check Sources**: Are document sources displayed correctly?

---

## 🎉 Success!

If all steps completed successfully, your DocuVault RAG Chatbot is now running on your GPU server!

**Test Query**: "What is this document about?" after indexing a PDF.

**Expected**: AI provides summary with source citations and relevance scores.

---

**Last Updated**: November 22, 2025  
**Version**: Phase 2 - Django Integration Complete
