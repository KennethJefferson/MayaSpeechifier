# Maya1 Speechify - Quick Reference Card

## Installation
```bash
# Windows
go build -o MayaSpeechify.exe .

# Linux/macOS
go build -o MayaSpeechify .
```

## Essential Commands

### Basic Usage
```bash
# Single file
./MayaSpeechify -scan document.txt

# Directory (non-recursive)
./MayaSpeechify -scan books/

# Recursive directory scan
./MayaSpeechify -scan library/ -recursive

# With progress details
./MayaSpeechify -scan books/ -recursive -verbose
```

### Performance Options
```bash
# Parallel processing (2 workers)
./MayaSpeechify -scan books/ -recursive -workers 2

# Custom timeout (20 minutes)
./MayaSpeechify -scan large_book.txt -timeout 1200

# Maximum performance
./MayaSpeechify -scan library/ -recursive -workers 4 -timeout 600
```

### Server Options
```bash
# Local server
./MayaSpeechify -scan text.txt -server "http://localhost:7777"

# RunPod server
./MayaSpeechify -scan text.txt -server "https://pod-id.proxy.runpod.net"

# With custom voice
./MayaSpeechify -scan story.txt -voice "warm, friendly narrator voice"
```

## Configuration File

Create `config.json` in the same directory as the executable:

```json
{
  "server_url": "https://yakgzeajldnlek-7777.proxy.runpod.net",
  "timeout": 600,
  "workers": 1
}
```

## Command-Line Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-scan` | Path to process | (required) |
| `-recursive` | Scan subdirectories | false |
| `-workers` | Parallel workers | 1 |
| `-server` | Server URL | (from config) |
| `-timeout` | Timeout in seconds | 600 |
| `-voice` | Voice description | (none) |
| `-verbose` | Detailed output | false |

## Exit Codes

- `0` = Success
- `1` = Partial failure
- `2` = Complete failure
- `3` = Config error
- `4` = Network error
- `5` = File system error

## Common Examples

```bash
# Process audiobook collection
./MayaSpeechify -scan /audiobooks -recursive -workers 4

# Daily news with custom voice
./MayaSpeechify -scan /news/today -voice "news anchor voice"

# Debug problematic file
./MayaSpeechify -scan problem.txt -verbose -timeout 1200

# Batch process with skip existing
./MayaSpeechify -scan library/ -recursive -skip-existing
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check server URL and status |
| Timeout errors | Increase `-timeout` value |
| 502 Bad Gateway | Server restarting, wait 30s |
| High memory use | Reduce `-workers` count |
| Slow processing | Increase `-workers` count |

## Server Health Check
```bash
curl https://your-server:7777/health
```

## Performance Tips

- **Optimal workers** = CPU cores / 2
- **Local server**: Use more workers (4-8)
- **Remote server**: Use fewer workers (1-3)
- **Large files**: Increase timeout
- **Many small files**: Increase workers

---
*Quick Reference v1.0 - Full guide: USER_GUIDE.md*