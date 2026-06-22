# Xfiltrator

Enterprise-grade Linux CLI for metadata extraction and lightweight forensic analysis. Routes files through format-specific engines, applies anomaly rules, and renders results in the terminal or as JSON.

## Requirements

- **Python 3.10+**
- **Linux** (primary target; uses `stat` inode/uid/gid fields)

### Python dependencies

Installed via `requirements.txt`:

| Package      |            Role                        |
|--------------|----------------------------------------|
| `rich`       | Terminal tables and panels             |
| `kreuzberg`  | Text/PDF/document parsing              |
| `requests`   |  Send API calls and HTTP requests      |

### Required System Tools

Engines degrade to stub mode when a binary is missing. For full coverage, install:

| Tool        | Shell Command                             | Used by              |
|-------------|-------------------------------------------|----------------------|
| `exiftool`  | `sudo apt install exiftool`               | Image EXIF/XMP       |
| `mediainfo` | `sudo apt install mediainfo`              | Audio/video profiling|
| `binwalk`   | `sudo apt install binwalk`                | Embedded signatures  |
| `strings`   | `sudo apt install strings`                | Printable strings    |

## Quick start (Linux)

```bash
git clone <repo-url> meta-toolkit
cd meta-toolkit

chmod +x install-deps.sh run.sh
./install-deps.sh

# Analyze a single file
./run.sh -f /path/to/file.pdf

# JSON output (no manual venv activation needed!)
./run.sh -f /path/to/file.jpg --json

# Analyze a directory recursively
./run.sh -d /path/to/directory --json -o output/
```

**Key difference**: The `./run.sh` wrapper automatically activates the virtual environment—no need for `source .venv/bin/activate`.

## Quick start (Windows)

> **Note:** meta-toolkit is **Linux-primary**. Windows support is available but secondary. For best results, use in a Linux VM (WSL2, VirtualBox, etc.) or native Linux.

## Install scripts

### Linux — `install-deps.sh`

Creates a local virtual environment (`.venv`), upgrades `pip`, and installs Python packages from `requirements.txt`. Pass `--system` to also install optional OS packages via `apt` (requires `sudo`).

```bash
./install-deps.sh              # Python deps only
./install-deps.sh --dev        # Include pytest (requirements-dev.txt)
./install-deps.sh --system     # Python + apt packages (Debian/Ubuntu)
```

## Usage

### Single File Analysis

```bash
usage: ./run.sh -f FILE [OPTIONS]

Extract and forensically analyze file metadata.

required arguments:
  -f, --file FILE       Path to the target file for analysis

output options:
  --json                Emit report as JSON (default: rich terminal layout)
  --txt                 Emit report as plain text
  -o, --output PATH     Write report to file instead of stdout

Advanced options:
  --ai                  Enable AI-powered string analysis (requires local LLM)
```

### Directory Batch Analysis

```bash
usage: ./run.sh -d DIRECTORY [OPTIONS]

Analyze all files in a directory recursively.

required arguments:
  -d, --directory DIR   Path to directory (will recurse into subdirs)

output options:
  --json                Write one JSON report per file
  --txt                 Write one TXT report per file
  -o, --output PATH     Output directory (preserves source structure)

performance options:
  --workers N           Number of concurrent threads (default: 8)
```

### Examples

#### Single file analysis (terminal output)
```bash
./run.sh -f evidence/sample.png
./run.sh -f document.pdf
./run.sh -f archive.zip --txt
```

#### Single file analysis (JSON output)
```bash
# Write JSON to stdout
./run.sh -f evidence/sample.png --json

# Pipe to file
./run.sh -f evidence/sample.png --json > report.json

# Write directly with -o flag
./run.sh -f evidence/sample.png -o report.json
```

#### AI-powered analysis
```bash
# Enable AI string analysis (requires local LLM via Ollama/LM Studio/vLLM)
./run.sh -f suspicious_binary --ai --json
```

#### Batch directory processing
```bash
# Analyze all files, preserve directory structure, write JSON reports
./run.sh -d /evidence/collection -o /reports --json

# Use 16 concurrent workers for faster processing
./run.sh -d /evidence/collection -o /reports --json --workers 16

# Mixed format: terminal summary + individual reports
./run.sh -d /evidence/collection -o /reports --txt
```


### Forensic flags

`forensic/anomaly_detector.py` applies baseline rules:

- **timestomping_suspect** — mtime newer than atime
- **future_mtime** — modification time in the future
- **identical_ctime_mtime** — ctime and mtime within one second
- **engine_failure** — upstream engine error
- **embedded_payloads** — multiple binwalk signatures
- **metadata_rewrite_tool** — EXIF software tag references editing tools

Reports include a summarized `risk_level`: `none`, `low`, `medium`, or `high`.

## Project layout

```
./
├── run.sh
├── meta_extract
├── install-deps.sh
├── install-deps.bat
├── install-deps.ps1
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── config/
│   └── ai.json
├── core/
│   ├── __init__.py
│   ├── orchestrator.py
│   └── batch_analyzer.py
├── engines/
│   ├── __init__.py
│   ├── exiftool_engine.py    
│   ├── kreuzberg_engine.py  
│   ├── mediainfo_engine.py   
│   ├── stego_binwalk_engine.py  
│   ├── ai_strings_engine.py  
│   └── ai_provider.py        
├── forensic/
│   ├── __init__.py
│   └── anomaly_detector.py
├── utils/
│   ├── __init__.py
│   ├── config.py            
│   ├── exporter.py   
│   ├── summary_exporter.py   
│   ├── progress_tracker.py    
│   └── ui_rich.py            
└── README.md
```

## AI Integration (Optional)

Meta-toolkit supports AI-powered string analysis through local LLM providers. This feature is **optional** and gracefully skipped if no provider is available.

### Supported Providers

| Provider | Port | Installation |
|----------|------|---------------|
| **Ollama** | 11434 | [ollama.ai](https://ollama.com) |
| **LM Studio** | 1234 | [lmstudio.ai](https://lmstudio.ai) |
| **vLLM** | 8000 | [vllm.readthedocs.io](https://docs.vllm.ai/) |

### Setup

1. **Install and start a local LLM provider** (example: Ollama)
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.1:8b
   ollama serve
   # Listens on localhost:11434
   ```

2. **Run meta-toolkit with `--ai` flag**
   ```bash
   ./run.sh -f suspicious_binary --ai --json
   ```

3. **Auto-discovery**
   - Toolkit checks localhost, VirtualBox NAT gateway, and Host-Only networks
   - If the LLM is running on the host machine, set `AI_HOST` to the VM's default gateway IP and keep it persistent in your shell profile
   - `./run.sh -f file --ai`
   - Falls back gracefully if no provider found

4. **Host machine LLM setup**
   - Get the VM default gateway IP:
    ```bash
    ip route | grep default
    ```
   - Export the gateway IP so `--ai` can reach the host LLM from the VM:
    ```bash
    export AI_HOST=<default-gateway-ip>
    ```
   - Make it persistent by adding that export to your shell startup file, for example `~/.bashrc` or `~/.zshrc`
   - Test reachability through the VM:
    ```bash
    curl https://<default-gateway-ip>:<port>/api/tags
    ```

### Configuration

Edit `config/ai.json` to customize:

```json
{
  "ai": {
    "enabled": true,
    "provider": "auto",
    "timeout": 480,
    "preferred_models": [
      "qwen3:8b",
      "llama3.1:8b",
      "llama3:8b",
      "mistral:7b"
    ],
    "ports": {
      "ollama": 11434,
      "lmstudio": 1234,
      "vllm": 8000
    }
  }
}
```

## Forensic Rules

The anomaly detector flags potential tampering:

| Rule | Severity | Description |
|------|----------|-------------|
| `timestomping_suspect` | Medium | mtime newer than atime (suspicious access pattern) |
| `future_mtime` | High | Modification time in the future |
| `identical_ctime_mtime` | Low | ctime and mtime within 1 second (suspicious precision) |
| `engine_failure` | Medium | Upstream extraction engine returned error |
| `embedded_payloads` | High | 3+ embedded signatures detected by binwalk |
| `metadata_rewrite_tool` | Low | EXIF software tag indicates editing tool use |

Each report includes: `risk_level` (`none`, `low`, `medium`, `high`)

## Development & Testing

### Quick sanity check

```bash
./run.sh -f meta_extract --json   # Analyze the script itself
```


## Troubleshooting

### "Virtual environment not found" error

```bash
# The .venv directory is missing. Reinstall:
./install-deps.sh
./run.sh -f your_file
```

### Engines show "stub" status

This is **normal** — it means an optional system tool is missing:

```bash
# Install all optional tools (Linux/Debian/Ubuntu)
./install-deps.sh --system

# Or manually
sudo apt-get install libimage-exiftool-perl mediainfo binwalk
```

### AI analysis not working

1. **Verify LLM provider is running**
   ```bash
   curl http://localhost:11434/api/tags  # Ollama
   curl http://localhost:1234/api/tags   # LM Studio
   ```

2. **Check AI configuration**
   - Verify `config/ai.json` ports match your provider
  - Set `AI_HOST` if running on non-localhost: `export AI_HOST=<default-gateway-ip>`
  - Confirm the host LLM is reachable from the VM with `curl https://<default-gateway-ip>:<port>/api/tags`

3. **Disable AI if not needed**
   - Simply omit `--ai` flag; analysis still works without it

### Tesseract / Kreuzberg warning noise

If you see `Error opening data file /io/.tesseract-cache/linux-x86_64/tessdata/eng.traineddata ... Tesseract couldn't load any languages!` messages from Tesseract after Kreuzberg runs, verify the tessdata location and export the parent directory as `TESSDATA_PREFIX`:

```bash
tesseract --version
find /usr -name eng.traineddata 2>/dev/null
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5
echo "$TESSDATA_PREFIX"
nano ~/.bashrc
```

Add this line to the end of `~/.bashrc`:

```bash
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5
```

If your `find` output points somewhere else, use that parent directory instead of `/usr/share/tesseract-ocr/5`.

### Timeout errors on slow systems

- Increase timeout in `config/ai.json` → `ai.timeout` (seconds)
- Reduce batch concurrency: `./run.sh -d /path --workers 4`

## License

Add your license here.
