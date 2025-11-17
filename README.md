# Maya1 Speechify - Text-to-Speech Client/Server

A high-performance client/server application for converting text files to speech using the Maya1 3B parameter TTS model.

## Features

- **Server (Python/FastAPI)**
  - FastAPI with async support for high throughput
  - vLLM backend for efficient GPU utilization (~6-8GB VRAM)
  - Automatic text chunking for large files
  - Server-side audio merging
  - MP3 output format

- **Client (Go)**
  - Concurrent file processing with worker pools
  - Recursive directory scanning
  - Beautiful progress bars with your preferred green style
  - Verbose logging mode
  - Saves MP3 files alongside source .txt files

## Architecture

```
┌─────────────────┐          ┌──────────────────┐
│   Go Client     │   HTTP   │  Python Server   │
│                 │ ────────>│                  │
│  - File Scanner │  POST    │  - FastAPI       │
│  - Worker Pool  │  JSON    │  - vLLM Engine   │
│  - Progress Bar │          │  - Maya1 Model   │
│                 │<──────── │  - SNAC Decoder  │
│                 │   MP3    │                  │
└─────────────────┘          └──────────────────┘
```

## Requirements

### Server
- Ubuntu or Linux-based OS (RunPod)
- NVIDIA GPU with 16GB+ VRAM (RTX 4090, A100, H100)
- CUDA 11.8+
- Python 3.10+

### Client
- Go 1.21+
- Windows/Linux/macOS

## Installation

### Server Setup

1. **Clone and navigate to server directory:**
   ```bash
   cd Maya1_Speechify/server
   ```

2. **Create Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ffmpeg (required for MP3 encoding):**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ffmpeg

   # Or using conda
   conda install -c conda-forge ffmpeg
   ```

5. **Configure the server (optional):**

   The server uses `config.json` for all settings. A default configuration is included, but you can customize it:

   ```bash
   # View the example configuration with documentation
   cat config.example.json

   # Edit config.json to customize settings
   nano config.json
   ```

   **Key configuration options:**
   - `model_pool.num_instances`: Number of parallel model instances (default: 3)
   - `model_pool.gpu_memory_per_instance`: GPU memory per instance (default: 0.28 = 28%)
   - `server.port`: Server port (default: 8000)
   - `cors.enabled`: Enable CORS for web clients (default: true)

   See [Configuration](#configuration) section below for details.

6. **Start the server:**
   ```bash
   python main.py
   ```

   The server will start on `http://0.0.0.0:8000` by default.

   **Note:** First run will download the Maya1 model (~6GB) and SNAC decoder automatically.

### Client Setup

1. **Navigate to client directory:**
   ```bash
   cd Maya1_Speechify/client
   ```

2. **Download dependencies:**
   ```bash
   go mod download
   ```

3. **Build the client:**
   ```bash
   # Windows
   go build -o MayaSpeechify.exe .

   # Linux/macOS
   go build -o MayaSpeechify .
   ```

## Usage

### Server

**Start server with custom host/port:**
```bash
python main.py
# Or with environment variables
HOST=0.0.0.0 PORT=8000 python main.py
```

**Health check:**
```bash
curl http://localhost:8000/health
```

**API Endpoints:**

1. **POST /synthesize** - Synthesize from JSON
   ```bash
   curl -X POST http://localhost:8000/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello world", "voice_description": "warm, conversational"}' \
     --output output.mp3
   ```

2. **POST /synthesize_file** - Synthesize from file upload
   ```bash
   curl -X POST http://localhost:8000/synthesize_file \
     -F "file=@input.txt" \
     -F "voice_description=neutral, clear" \
     --output output.mp3
   ```

### Client

**Basic usage (single directory, non-recursive):**
```bash
MayaSpeechify.exe -scan "K:\Downloads\books"
```

**Recursive scanning with multiple workers:**
```bash
MayaSpeechify.exe -workers 2 -scan "K:\Downloads\books" -recursive
```

**Verbose mode for detailed logging:**
```bash
MayaSpeechify.exe -workers 2 -scan "K:\Downloads\books" -recursive -verbose
```

**Custom server URL:**
```bash
MayaSpeechify.exe -scan "K:\Downloads\books" -server "http://192.168.1.100:8000"
```

**Command-line flags:**
```
  -workers int
        Number of parallel workers (default: 1)
  -scan string
        Root directory to scan for .txt files (required)
  -recursive
        Search subdirectories recursively
  -verbose
        Enable detailed logging
  -server string
        Maya1 API server URL (default: "http://localhost:8000")
```

## Examples

### Example 1: Process single directory
```bash
MayaSpeechify.exe -scan "C:\Books"
```

Output:
```
Scanning for .txt files...
Found 5 text file(s)
│████████████████████████████████████████│ 100% (5/5)

=== Summary ===
Total files: 5
Successful: 5
Failed: 0
```

### Example 2: Recursive scan with verbose output
```bash
MayaSpeechify.exe -workers 2 -scan "C:\Books" -recursive -verbose
```

Output:
```
Configuration:
  Workers: 2
  Scan Path: C:\Books
  Recursive: true
  Server URL: http://localhost:8000

Scanning for .txt files...
Found 23 text file(s)

[Worker 1] Processing: chapter1.txt
[Worker 2] Processing: chapter2.txt
[Worker 1] Success: chapter1.txt -> chapter1.mp3 (12.34s)
[Worker 2] Success: chapter2.txt -> chapter2.mp3 (15.67s)
[Worker 1] Processing: chapter3.txt
...

=== Summary ===
Total files: 23
Successful: 23
Failed: 0
```

## Configuration

### Server Configuration File (`config.json`)

The server uses a JSON configuration file for all settings. The default `config.json` supports **3 parallel model instances** with round-robin load balancing.

**Configuration file location:** `server/config.json`

**Example configuration:** `server/config.example.json` (with detailed comments)

### Configuration Sections

#### 1. Server Settings
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 1,
    "log_level": "INFO"
  }
}
```

- `host`: Server bind address (default: 0.0.0.0 for all interfaces)
- `port`: Server port (default: 8000)
- `workers`: Uvicorn worker processes (default: 1)
- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)

#### 2. CORS Settings
```json
{
  "cors": {
    "enabled": true,
    "allowed_origins": ["*"],
    "allowed_methods": ["GET", "POST"],
    "allowed_headers": ["*"],
    "allow_credentials": false
  }
}
```

Enable CORS for web-based clients. Use `allowed_origins: ["*"]` for development, specific origins for production.

#### 3. Model Pool Settings ⚡ **NEW**
```json
{
  "model_pool": {
    "num_instances": 3,
    "gpu_memory_per_instance": 0.28,
    "tensor_parallel_size": 1
  }
}
```

- `num_instances`: Number of parallel model instances (1-8 recommended)
- `gpu_memory_per_instance`: GPU memory fraction per instance (0.1-0.9)
- `tensor_parallel_size`: GPUs per instance for tensor parallelism

**GPU Memory Guidelines:**
- **RTX 4090 (24GB)**: 3 instances × 0.28 = ~20GB (recommended)
- **A100 (40GB)**: 5 instances × 0.25 = ~50GB total across instances
- **Conservative**: 1 instance × 0.85 = ~20GB (safe fallback)

**Formula:** `Total VRAM = num_instances × gpu_memory_per_instance × GPU_SIZE`

Leave 10-15% headroom for CUDA overhead.

#### 4. Generation Parameters
```json
{
  "generation": {
    "temperature": 0.4,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "max_new_tokens": 2048
  }
}
```

Controls speech generation quality and characteristics.

#### 5. Audio Settings
```json
{
  "audio": {
    "sample_rate": 24000,
    "format": "mp3",
    "bitrate": "192k"
  }
}
```

- `sample_rate`: 24000 Hz (Maya1 native, don't change)
- `format`: Output format (mp3, wav)
- `bitrate`: MP3 quality (128k, 192k, 256k, 320k)

#### 6. Text Processing
```json
{
  "text_processing": {
    "chunk_size": 1500,
    "max_file_size_mb": 10
  }
}
```

- `chunk_size`: Max tokens per chunk (500-4000)
- `max_file_size_mb`: Maximum uploadable file size

### Environment Variable Overrides

Override config.json values with environment variables:

```bash
# Server settings
export HOST=0.0.0.0
export PORT=8000
export LOG_LEVEL=DEBUG

# Model pool settings
export NUM_INSTANCES=2
export GPU_MEMORY_PER_INSTANCE=0.35

# Start server
python main.py
```

### Viewing Current Configuration

Check active configuration via API:

```bash
curl http://localhost:8000/config
```

Returns current settings (non-sensitive fields only).

## Performance Tuning

### Server

**Model Pool Configuration:**
- Default: **3 instances** for RTX 4090 (optimal throughput)
- Conservative: **1 instance** (maximum memory for single request)
- Aggressive: **4+ instances** (only for GPUs >32GB VRAM)

Edit `config.json` to adjust `num_instances` and `gpu_memory_per_instance`.

**GPU Memory Optimization:**
- Adjust `GPU_MEMORY_UTILIZATION` in `config.py` (default: 0.85)
- For RTX 4090 (24GB VRAM), single instance uses ~6-8GB with vLLM
- Recommended to keep 1 worker on client side for single GPU setup

**Text Chunking:**
- Default chunk size: 1500 tokens (configurable in `config.py`)
- Automatically splits large texts at sentence boundaries
- Audio chunks merged seamlessly with 100ms silence padding

### Client

**Worker Count:**
- Default: 1 worker (safe for all setups)
- RTX 4090: Can handle 2-3 workers if server is scaled
- Adjust based on server capacity and network bandwidth

**Example VRAM Usage:**
```
RTX 4090 (24GB total):
├── System: ~2GB
├── Maya1 model (vLLM): ~6-8GB
├── SNAC decoder: ~1-2GB
└── Available: ~12-14GB
```

## Troubleshooting

### Server Issues

**Out of memory errors:**
- Reduce `GPU_MEMORY_UTILIZATION` in `config.py`
- Reduce `CHUNK_SIZE` for smaller batches
- Ensure no other processes are using GPU memory

**SNAC import errors:**
```bash
pip install git+https://github.com/hubertsiuzdak/snac.git
```

**MP3 encoding fails:**
- Install ffmpeg system-wide
- Verify with: `ffmpeg -version`

### Client Issues

**Connection refused:**
- Verify server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Use correct server URL with `-server` flag

**Build errors:**
```bash
# Clean and rebuild
rm -rf go.sum
go mod tidy
go build -o MayaSpeechify.exe .
```

## Project Structure

```
Maya1_Speechify/
├── server/
│   ├── main.py              # FastAPI application
│   ├── model.py             # vLLM model wrapper
│   ├── utils.py             # Text chunking & audio merging
│   ├── config.py            # Configuration
│   └── requirements.txt     # Python dependencies
├── client/
│   ├── main.go              # CLI entry point
│   ├── scanner.go           # File discovery
│   ├── worker.go            # Worker pool & HTTP client
│   ├── progress.go          # Progress bar implementation
│   └── go.mod               # Go dependencies
└── README.md
```

## API Reference

### Server Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model": "maya-research/maya1",
  "device": "cuda"
}
```

#### POST /synthesize
Synthesize speech from text.

**Request:**
```json
{
  "text": "Your text here",
  "voice_description": "warm, conversational, low pitch"
}
```

**Response:** MP3 audio file (audio/mpeg)

**Voice Description Options:**
- Pitch: `low pitch`, `high pitch`, `neutral pitch`
- Tone: `warm`, `cold`, `friendly`, `professional`
- Style: `conversational`, `formal`, `casual`
- Age: `young`, `middle-aged`, `elderly`

**Emotion Tags (inline in text):**
- `<laugh>` - Laughter
- `<cry>` - Crying
- `<whisper>` - Whispering
- `<angry>` - Angry tone
- `<gasp>` - Gasping
- Plus 15+ more emotions

## License

Apache 2.0 (same as Maya1 model)

## References

- [Maya1 Model - Hugging Face](https://huggingface.co/maya-research/maya1)
- [vLLM Documentation](https://docs.vllm.ai/)
- [SNAC Neural Codec](https://github.com/hubertsiuzdak/snac)

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review Maya1 model documentation
3. Open an issue on GitHub
