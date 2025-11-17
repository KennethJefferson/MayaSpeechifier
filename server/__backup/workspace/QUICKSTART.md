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

# (Optional) Customize configuration
# The default config.json runs 3 model instances for parallel processing
# Edit config.json to adjust num_instances or gpu_memory_per_instance
nano config.json

# Start the server
python main.py
```

**First run will take ~5-10 minutes** to download the Maya1 model (~6GB) and SNAC decoder.

Server will be available at: `http://localhost:8000`

**Default Configuration:** 3 model instances with round-robin load balancing (optimal for RTX 4090)

### Step 2: Build the Client (Windows/Local Machine)

```bash
# Navigate to client directory
cd Maya1_Speechify/client

# Download Go dependencies
go mod download

# Build the executable
go build -o MayaSpeechify.exe .

# (Optional) Configure the client
# A default config.json is included, edit if needed
# Example: Set server URL for remote server
# Edit config.json:
# {
#   "server_url": "https://xxxxx-7777.proxy.runpod.net",
#   "timeout": 600,
#   "workers": 1
# }
```

**Note:** The client automatically loads `config.json` from the same directory as the executable. If missing, `config.example.json` is created on first run.

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

**Default Server Configuration (3 model instances):**
- RTX 4090: ~20GB VRAM total (3 instances × ~6.7GB each)
- Processes 3 chunks concurrently with round-robin load balancing
- Optimal throughput for parallel requests

**Client Workers:**
- Single worker (default): Sequential file processing
- Multiple workers (2-3): Parallel file processing (limited by server capacity)

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
- Edit `server/config.json`
- Reduce `num_instances` from 3 to 1 or 2
- OR reduce `gpu_memory_per_instance` from 0.28 to 0.25
- Restart server

Example fix:
```json
{
  "model_pool": {
    "num_instances": 1,
    "gpu_memory_per_instance": 0.85
  }
}
```

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
- Start with 1 client worker and increase gradually
- Monitor GPU usage: `nvidia-smi -l 1`
- Large text files are automatically chunked by the server

**Server Configuration (`server/config.json`):**
- Adjust `num_instances` for parallel processing (1-3 recommended for RTX 4090)
- Adjust `bitrate` for MP3 quality (128k, 192k, 256k, 320k)
- Enable/disable CORS for web clients
- Check server config: `curl http://localhost:8000/config`
- Check server health: `curl http://localhost:8000/health` (shows instance count)

**Client Configuration (`client/config.json`):**
- Set default `server_url` to avoid `-server` flag every time
- Adjust `timeout` for large files (default: 600s = 10 min)
- Set default `workers` count (can override with `-workers` flag)
- CLI flags always override config.json values
- First run creates `config.example.json` automatically if missing
