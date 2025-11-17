# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Start the Server (Ubuntu/RunPod)

```bash
# Navigate to server directory
cd Maya1_Speechify/server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Install ffmpeg (if not already installed)
sudo apt-get update && sudo apt-get install -y ffmpeg

# Start the server
python main.py
```

**First run will take ~5-10 minutes** to download the Maya1 model (~6GB) and SNAC decoder.

Server will be available at: `http://localhost:8000`

### Step 2: Build the Client (Windows/Local Machine)

```bash
# Navigate to client directory
cd Maya1_Speechify/client

# Download Go dependencies
go mod download

# Build the executable
go build -o MayaSpeechify.exe .
```

### Step 3: Test the Setup

**Option A: Test server only**
```bash
# In server directory
python test_server.py
```

**Option B: Test with client**
```bash
# In client directory (use the test.txt file)
MayaSpeechify.exe -scan . -verbose
```

This will convert `test.txt` to `test.mp3` in the same directory.

### Step 4: Process Your Files

```bash
# Single directory
MayaSpeechify.exe -scan "K:\Downloads\books"

# Recursive with multiple workers
MayaSpeechify.exe -workers 2 -scan "K:\Downloads\books" -recursive -verbose
```

## 📊 Expected Performance

- **Small files (< 1KB):** ~5-10 seconds
- **Medium files (1-10KB):** ~10-30 seconds
- **Large files (> 10KB):** ~30-120 seconds

With RTX 4090:
- Single worker (safe): ~6-8GB VRAM
- Two workers (possible): ~12-16GB VRAM

## 🔧 Common Issues

**Server won't start:**
```bash
# Check CUDA is available
python -c "import torch; print(torch.cuda.is_available())"

# Should print: True
```

**Client can't connect:**
```bash
# Test server health
curl http://localhost:8000/health

# If using remote server, update client command:
MayaSpeechify.exe -scan "C:\Books" -server "http://YOUR_SERVER_IP:8000"
```

**Out of memory:**
- Edit `server/config.py`
- Reduce `GPU_MEMORY_UTILIZATION` from 0.85 to 0.75
- Restart server

## 📁 What Gets Created

For each `.txt` file, an `.mp3` file is created in the same directory:

```
books/
├── chapter1.txt
├── chapter1.mp3  ← Created
├── chapter2.txt
└── chapter2.mp3  ← Created
```

## 🎯 Next Steps

1. Read the full [README.md](README.md) for advanced features
2. Customize voice descriptions in requests
3. Adjust worker count based on your GPU capacity
4. Set up as a systemd service for production use

## 💡 Pro Tips

- Use `-verbose` flag while testing to see detailed progress
- Start with 1 worker and increase gradually
- Monitor GPU usage: `nvidia-smi -l 1`
- Large text files are automatically chunked by the server
- MP3 bitrate can be adjusted in `server/config.py`
