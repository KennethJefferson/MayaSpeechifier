# Maya1 Speechify Client User Guide

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Usage](#advanced-usage)
6. [Command-Line Options](#command-line-options)
7. [Examples](#examples)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)
11. [API Reference](#api-reference)

## Overview

Maya1 Speechify is a high-performance client application for converting text files to natural-sounding speech using the Maya1 3B parameter TTS model. The client is written in Go for maximum performance and cross-platform compatibility.

### Key Features
- **High-Quality TTS**: Leverages Maya1's 3B parameters for natural, emotionally expressive speech
- **Batch Processing**: Convert multiple files or entire directories
- **Parallel Processing**: Multi-worker support for faster batch conversions
- **Recursive Scanning**: Process entire directory trees automatically
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Progress Tracking**: Visual progress bars with detailed status
- **Flexible Configuration**: JSON config files with CLI overrides
- **Resume Capability**: Skip already processed files on reruns

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Memory**: 512MB RAM minimum
- **Network**: Stable internet connection (for cloud server) or local network (for local server)
- **Disk Space**: ~10MB for client, plus space for MP3 outputs
- **Go Runtime**: Not required (standalone executable)

## Installation

### Pre-built Binaries

#### Windows
```powershell
# Download the latest release (example)
curl -LO https://github.com/yourusername/maya1-speechify/releases/latest/download/MayaSpeechify.exe

# Or build from source
cd client
go build -o MayaSpeechify.exe .
```

#### macOS/Linux
```bash
# Download the latest release (example)
curl -LO https://github.com/yourusername/maya1-speechify/releases/latest/download/MayaSpeechify
chmod +x MayaSpeechify

# Or build from source
cd client
go build -o MayaSpeechify .
```

### Building from Source

#### Prerequisites
- Go 1.21 or higher
- Git

#### Build Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/maya1-speechify.git
cd maya1-speechify/client

# Install dependencies
go mod download
go mod tidy

# Build the executable
go build -o MayaSpeechify .    # Unix/macOS
go build -o MayaSpeechify.exe . # Windows

# Verify the build
./MayaSpeechify -version
```

## Configuration

### Configuration File (`config.json`)

The client uses a JSON configuration file for default settings. Create `config.json` in the same directory as the executable:

```json
{
  "server_url": "https://yakgzeajldnlek-7777.proxy.runpod.net",
  "timeout": 600,
  "workers": 1,
  "voice_description": null,
  "output_format": "mp3",
  "bitrate": 192
}
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `server_url` | string | (required) | Maya1 server endpoint URL |
| `timeout` | integer | 600 | Request timeout in seconds |
| `workers` | integer | 1 | Number of parallel workers |
| `voice_description` | string/null | null | Optional voice style description |
| `output_format` | string | "mp3" | Audio format (mp3, wav) |
| `bitrate` | integer | 192 | MP3 bitrate in kbps |

### Environment Variables

Override configuration with environment variables:

```bash
export MAYA_SERVER_URL="http://localhost:7777"
export MAYA_WORKERS=4
export MAYA_TIMEOUT=1200
```

### Configuration Priority

Settings are applied in this order (highest priority first):
1. Command-line flags
2. Environment variables
3. Configuration file (`config.json`)
4. Built-in defaults

## Basic Usage

### Convert a Single File
```bash
./MayaSpeechify -scan path/to/file.txt
```

### Convert All Files in a Directory
```bash
./MayaSpeechify -scan path/to/books
```

### Recursive Directory Processing
```bash
./MayaSpeechify -scan path/to/library -recursive
```

### Show Progress and Details
```bash
./MayaSpeechify -scan . -recursive -verbose
```

## Advanced Usage

### Parallel Processing

Process multiple files simultaneously for faster conversion:

```bash
# Use 4 parallel workers
./MayaSpeechify -scan library/ -recursive -workers 4

# Optimal workers = number of CPU cores
./MayaSpeechify -scan . -recursive -workers $(nproc)  # Linux/macOS
./MayaSpeechify -scan . -recursive -workers %NUMBER_OF_PROCESSORS%  # Windows
```

### Custom Server Endpoints

```bash
# Use local server
./MayaSpeechify -scan books/ -server "http://localhost:7777"

# Use RunPod deployment
./MayaSpeechify -scan docs/ -server "https://your-pod-id.proxy.runpod.net"

# Use custom deployment
./MayaSpeechify -scan texts/ -server "https://api.yourservice.com/tts"
```

### Voice Customization

```bash
# Specify voice characteristics
./MayaSpeechify -scan story.txt -voice "warm, friendly, female voice with slight British accent"

# Different voices for different content
./MayaSpeechify -scan technical.txt -voice "clear, professional, male voice"
./MayaSpeechify -scan children.txt -voice "cheerful, animated, storyteller voice"
```

### Batch Processing with Filters

```bash
# Process only specific files (using shell globbing)
./MayaSpeechify -scan "books/*.txt"

# Process with exclusion (Unix/macOS)
find books/ -name "*.txt" ! -name "*draft*" | xargs -I {} ./MayaSpeechify -scan {}

# Process with inclusion list
for file in $(cat filelist.txt); do
  ./MayaSpeechify -scan "$file"
done
```

### Output Management

```bash
# Custom output directory (requires code modification)
./MayaSpeechify -scan input/ -output output/

# Preserve directory structure
./MayaSpeechify -scan library/ -recursive -preserve-structure

# Skip existing MP3s
./MayaSpeechify -scan books/ -recursive -skip-existing
```

## Command-Line Options

### Required Options

| Flag | Description | Example |
|------|-------------|---------|
| `-scan` | Path to file or directory to process | `-scan books/` |

### Optional Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `-recursive` | `-r` | false | Scan directories recursively |
| `-workers` | `-w` | 1 | Number of parallel workers |
| `-server` | `-s` | (from config) | Server endpoint URL |
| `-timeout` | `-t` | 600 | Request timeout in seconds |
| `-voice` | `-v` | (none) | Voice description |
| `-verbose` | | false | Enable detailed logging |
| `-config` | `-c` | `config.json` | Path to config file |
| `-skip-existing` | | false | Skip files with existing MP3s |
| `-version` | | | Show version information |
| `-help` | `-h` | | Show help message |

### Flag Combinations

```bash
# Maximum performance mode
./MayaSpeechify -scan library/ -r -w 8 -t 1200

# Debug mode
./MayaSpeechify -scan test.txt -verbose -w 1

# Production batch processing
./MayaSpeechify -scan /data/books -r -w 4 -skip-existing

# Quick test
./MayaSpeechify -scan sample.txt -t 30 -verbose
```

## Examples

### Example 1: Convert an Audiobook Collection

```bash
# Directory structure:
# audiobooks/
#   fiction/
#     scifi/
#       book1.txt
#       book2.txt
#     fantasy/
#       book3.txt
#   nonfiction/
#     history/
#       book4.txt

# Convert everything with 4 workers
./MayaSpeechify -scan audiobooks/ -recursive -workers 4

# Result: MP3 files created alongside each .txt file
```

### Example 2: Process Daily News Articles

```bash
#!/bin/bash
# daily_news_tts.sh

DATE=$(date +%Y%m%d)
NEWS_DIR="/data/news/$DATE"
WORKERS=2

# Download news articles (example)
python fetch_news.py --output "$NEWS_DIR"

# Convert to speech
./MayaSpeechify \
  -scan "$NEWS_DIR" \
  -recursive \
  -workers $WORKERS \
  -voice "clear, neutral news anchor voice" \
  -verbose

# Move MP3s to podcast directory
mv "$NEWS_DIR"/*.mp3 /var/www/podcasts/daily/
```

### Example 3: Bulk Educational Content

```bash
# Process course materials with appropriate voices
COURSE_DIR="online_course"

# Lectures - professional voice
./MayaSpeechify -scan "$COURSE_DIR/lectures" -r \
  -voice "clear, professional, academic tone"

# Examples - friendly voice
./MayaSpeechify -scan "$COURSE_DIR/examples" -r \
  -voice "friendly, encouraging, conversational"

# Summaries - concise voice
./MayaSpeechify -scan "$COURSE_DIR/summaries" -r \
  -voice "concise, clear, slightly faster pace"
```

### Example 4: Resume After Interruption

```bash
# First run (interrupted)
./MayaSpeechify -scan huge_library/ -recursive -workers 4
# ^C (interrupted after processing 100/500 files)

# Resume (skips already converted files)
./MayaSpeechify -scan huge_library/ -recursive -workers 4 -skip-existing
# Continues from file 101
```

### Example 5: Integration with Other Tools

```bash
# Convert markdown to text, then to speech
for file in docs/*.md; do
  pandoc "$file" -t plain -o "${file%.md}.txt"
done
./MayaSpeechify -scan docs/ -recursive

# Convert EPUBs to speech
for epub in ebooks/*.epub; do
  ebook-convert "$epub" "${epub%.epub}.txt"
done
./MayaSpeechify -scan ebooks/ -workers 2

# Process with specific encoding
iconv -f WINDOWS-1252 -t UTF-8 old_doc.txt > converted.txt
./MayaSpeechify -scan converted.txt
```

## Performance Optimization

### Worker Count Guidelines

| System Type | CPU Cores | Recommended Workers | Notes |
|-------------|-----------|-------------------|--------|
| Low-end laptop | 2-4 | 1-2 | Avoid system slowdown |
| Standard desktop | 4-8 | 2-4 | Good balance |
| Workstation | 8-16 | 4-8 | Maximum throughput |
| Server | 16+ | 8-16 | Consider server limits |

### Network Optimization

```bash
# For local server (low latency)
./MayaSpeechify -scan books/ -workers 8 -timeout 60

# For remote server (high latency)
./MayaSpeechify -scan books/ -workers 2 -timeout 600

# For unstable connection
./MayaSpeechify -scan books/ -workers 1 -timeout 1200 -verbose
```

### Memory Management

- Each worker uses ~50-100MB RAM
- Large text files are automatically chunked
- MP3 encoding is streamed (low memory usage)

### Disk I/O Optimization

```bash
# Process files from SSD for best performance
./MayaSpeechify -scan /ssd/texts/ -workers 4

# For slow storage, reduce workers
./MayaSpeechify -scan /nas/books/ -workers 2

# Monitor disk usage
watch -n 1 'df -h | grep -E "Filesystem|maya"'
```

### Server Load Balancing

```json
{
  "server_url": "https://lb.maya-tts.com",
  "timeout": 300,
  "workers": 6
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Refused
```
Error: failed to send request: connection refused
```
**Solution:**
- Check server is running: `curl http://server:7777/health`
- Verify server URL in config.json
- Check firewall settings
- Ensure VPN is connected (if required)

#### 2. Timeout Errors
```
Error: request timeout after 600s
```
**Solution:**
- Increase timeout: `-timeout 1200`
- Reduce file size (split large files)
- Check network stability
- Reduce number of workers

#### 3. 502 Bad Gateway
```
Error: server returned status 502
```
**Solution:**
- Server may be restarting, wait 30 seconds
- Check RunPod pod status
- Verify proxy URL is correct
- Contact server administrator

#### 4. File Not Found
```
Error: failed to read file: no such file or directory
```
**Solution:**
- Check file path is correct
- Use absolute paths for clarity
- Verify file permissions
- Check for special characters in filenames

#### 5. Invalid UTF-8
```
Error: invalid UTF-8 encoding in text file
```
**Solution:**
```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt
# Or
file -bi input.txt  # Check encoding
```

#### 6. Out of Memory
```
Error: cannot allocate memory
```
**Solution:**
- Reduce number of workers
- Process smaller batches
- Close other applications
- Split large files

### Debug Mode

Enable verbose logging for detailed diagnostics:

```bash
# Maximum debugging
./MayaSpeechify -scan test.txt -verbose 2>&1 | tee debug.log

# Network debugging
MAYA_DEBUG=network ./MayaSpeechify -scan test.txt -verbose

# Performance profiling
./MayaSpeechify -scan books/ -verbose | grep "Duration:"
```

### Log Analysis

```bash
# Check for patterns in errors
grep -i "error\|fail" maya.log | sort | uniq -c

# Monitor progress
tail -f maya.log | grep "Success"

# Performance statistics
grep "Duration:" maya.log | awk '{sum+=$2; count++} END {print "Avg:", sum/count}'
```

## FAQ

### Q1: Can I use a custom TTS model instead of Maya1?
**A:** The client is designed for Maya1, but you can modify the server to use different models. The client just expects a `/synthesize` endpoint that returns MP3 data.

### Q2: How large can input files be?
**A:** The server automatically chunks files larger than ~1500 tokens. Files up to 1MB+ have been tested successfully. Very large files (>10MB) may require timeout adjustment.

### Q3: Can I convert other formats besides .txt?
**A:** Currently only .txt files are supported. Use external tools to convert:
```bash
# PDF to text
pdftotext input.pdf output.txt

# DOCX to text
pandoc input.docx -t plain -o output.txt

# HTML to text
html2text input.html > output.txt
```

### Q4: How can I improve speech quality?
**A:**
- Use well-formatted input text (proper punctuation, paragraphs)
- Add voice descriptions for specific styles
- Ensure text is clean (no encoding issues)
- Use higher bitrate (modify server config)

### Q5: Can I queue jobs for later processing?
**A:** Create a simple queue system:
```bash
# Create job queue
ls books/*.txt > queue.txt

# Process queue
while read -r file; do
  ./MayaSpeechify -scan "$file"
  sed -i '1d' queue.txt  # Remove processed file
done < queue.txt
```

### Q6: Is there a GUI version?
**A:** No GUI currently, but you can create simple wrappers:
```powershell
# Windows PowerShell GUI
Add-Type -AssemblyName System.Windows.Forms
$FileBrowser = New-Object System.Windows.Forms.OpenFileDialog
$FileBrowser.filter = "Text files (*.txt)|*.txt"
[void]$FileBrowser.ShowDialog()
./MayaSpeechify.exe -scan $FileBrowser.FileName
```

### Q7: Can I process multiple languages?
**A:** Maya1 supports multiple languages. The model will auto-detect the language in most cases. For best results, don't mix languages in a single file.

### Q8: How do I monitor server health?
**A:**
```bash
# Health check
curl http://server:7777/health

# Continuous monitoring
watch -n 5 'curl -s http://server:7777/health | python -m json.tool'

# Check GPU usage (on server)
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 1
```

### Q9: Can I run multiple client instances?
**A:** Yes, but coordinate to avoid overloading the server:
```bash
# Instance 1: Process fiction
./MayaSpeechify -scan books/fiction -recursive -workers 2 &

# Instance 2: Process non-fiction
./MayaSpeechify -scan books/nonfiction -recursive -workers 2 &

wait  # Wait for both to complete
```

### Q10: How do I update the client?
**A:**
```bash
# Backup current version
cp MayaSpeechify MayaSpeechify.backup

# Download or build new version
go get -u ./...
go build -o MayaSpeechify .

# Test new version
./MayaSpeechify -version
```

## API Reference

### Server Endpoints

#### POST /synthesize
Converts text to speech.

**Request:**
```json
{
  "text": "Text to convert",
  "voice_description": "Optional voice style"
}
```

**Response:**
- Success (200): MP3 audio data (binary)
- Error (400): Invalid request
- Error (500): Server error

**Example:**
```bash
curl -X POST http://server:7777/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  -o output.mp3
```

#### GET /health
Check server status.

**Response:**
```json
{
  "status": "healthy",
  "model": "maya-research/maya1",
  "device": "cuda",
  "num_instances": 2,
  "healthy_instances": 2,
  "gpu_memory_per_instance": "40.0%"
}
```

#### GET /config
Get server configuration.

**Response:**
```json
{
  "model_pool": {
    "num_instances": 2,
    "gpu_memory_per_instance": 0.4
  },
  "server": {
    "port": 7777
  }
}
```

### Client Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | All files processed successfully |
| 1 | Partial failure | Some files failed |
| 2 | Complete failure | All files failed |
| 3 | Configuration error | Invalid config or flags |
| 4 | Network error | Cannot reach server |
| 5 | File system error | Cannot read/write files |

### File Naming Convention

Output files follow this pattern:
- Input: `path/to/document.txt`
- Output: `path/to/document.mp3`

Special cases:
- Input: `book.chapter1.txt` → Output: `book.chapter1.mp3`
- Input: `file.txt.backup` → Output: `file.txt.mp3` (extension replaced)

## Support and Contributing

### Getting Help
- Check this guide first
- Review [GitHub Issues](https://github.com/yourusername/maya1-speechify/issues)
- Enable verbose mode for diagnostics
- Collect logs before reporting issues

### Reporting Issues
Include:
1. Client version (`./MayaSpeechify -version`)
2. Operating system and version
3. Exact command used
4. Error messages (verbose mode)
5. Sample text file (if applicable)

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### License
[Specify your license here]

---

*Last updated: November 2024*
*Version: 1.0.0*