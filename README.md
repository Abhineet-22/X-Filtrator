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

| Tool        | Shell Command           | Used by              |
|-------------|-------------------------|----------------------|
| `exiftool`  | `sudo apt install exiftool`| Image EXIF/XMP       |
| `mediainfo` | `sudo apt install mediainfo`             | Audio/video profiling|
| `binwalk`   | `sudo apt install binwalk`               | Embedded signatures  |
| `strings`   | `sudo apt install strings`              | Printable strings    |

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

**Command Prompt (cmd)**:

```bat
cd C:\Users\anima\Projects\meta-toolkit
install-deps.bat --dev
.venv\Scripts\activate.bat

REM After activation, use python directly (no wrapper on Windows)
python meta_extract -f tests\fixtures\sample.txt --json
pytest -v
```

**PowerShell**:

```powershell
cd C:\Users\anima\Projects\meta-toolkit
powershell -ExecutionPolicy Bypass -File .\install-deps.ps1 -Dev
.\.venv\Scripts\Activate.ps1

# After activation
python meta_extract -f tests\fixtures\sample.txt --json
pytest -v
```

If `python` prints *"Python was not found; run without arguments to install from the Microsoft Store"*, see [Windows Python setup](#windows-python-setup) below.

> **Note:** `.ps1` scripts do not run from Command Prompt by default. If `install-deps.ps1` prints nothing and `.venv` is missing, use `install-deps.bat` instead.

## Install scripts

### Linux — `install-deps.sh`

Creates a local virtual environment (`.venv`), upgrades `pip`, and installs Python packages from `requirements.txt`. Pass `--system` to also install optional OS packages via `apt` (requires `sudo`).

```bash
./install-deps.sh              # Python deps only
./install-deps.sh --dev        # Include pytest (requirements-dev.txt)
./install-deps.sh --system     # Python + apt packages (Debian/Ubuntu)
```

### Windows — `install-deps.bat` (cmd) or `install-deps.ps1` (PowerShell)

```bat
install-deps.bat               REM Python deps only
install-deps.bat --dev         REM Include pytest
```

```powershell
powershell -ExecutionPolicy Bypass -File .\install-deps.ps1
powershell -ExecutionPolicy Bypass -File .\install-deps.ps1 -Dev
```

## Windows Python setup

Windows often ships **App execution aliases** that hijack `python` and send you to the Microsoft Store even when Python is not installed.

1. **Install Python 3.10+** from [python.org/downloads](https://www.python.org/downloads/windows/)  
   On the installer first screen, enable **"Add python.exe to PATH"**.

2. **Disable Store aliases** (recommended):  
   **Settings → Apps → Advanced app settings → App execution aliases**  
   Turn **OFF** both `python.exe` and `python3.exe`.

3. **Close and reopen** PowerShell or Cursor's terminal.

4. Verify:

```powershell
py -3 --version          # preferred on Windows
# or, after PATH is set:
python --version
```

5. Bootstrap the project (pick cmd **or** PowerShell):

```bat
cd C:\Users\anima\Projects\meta-toolkit
install-deps.bat --dev
.venv\Scripts\activate.bat
pytest -v
```

After activation, `python` inside `.venv` always works — you do not need the global `python` command again for this project.

### Python 3.14 note

You have Python 3.14, which is very new. If `pip install` fails building `kreuzberg`, install **Python 3.12 or 3.13** alongside it and create the venv explicitly:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
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

advanced options:
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

## Architecture

```
meta_extract
└── core/orchestrator.py
        ├── filesystem stat (size, times, mode, uid/gid)
        ├── MIME detection (magic bytes → mimetypes)
        ├── engine dispatch
        │     ├── engines/kreuzberg_engine.py    (text, PDF, documents)
        │     ├── engines/exiftool_engine.py     (images)
        │     ├── engines/mediainfo_engine.py    (audio/video)
        │     └── engines/stego_binwalk_engine.py (binary carving)
        └── forensic/anomaly_detector.py         (tampering / timestomping flags)
                └── utils/ui_rich.py  or  utils/exporter.py
```

### Engine routing

| File type signal              | Engine          |
|-------------------------------|-----------------|
| Images (PNG, JPEG, GIF, …)    | `exiftool`      |
| Text, PDF, JSON, XML          | `kreuzberg`     |
| Audio / video containers      | `mediainfo`     |
| Unknown or binary             | `stego_binwalk` |

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
meta-toolkit/
├── run.sh                    # Wrapper script (auto-activates venv)
├── meta_extract              # CLI entry point (executable Python)
├── install-deps.sh           # Linux dependency bootstrap
├── install-deps.bat          # Windows installer (Command Prompt)
├── install-deps.ps1          # Windows installer (PowerShell)
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Development deps (pytest + runtime)
├── pytest.ini
├── config/
│   └── ai.json               # AI provider configuration
├── core/
│   ├── __init__.py
│   ├── orchestrator.py       # File analysis routing & dispatch
│   └── batch_analyzer.py     # Concurrent directory processing
├── engines/
│   ├── __init__.py
│   ├── exiftool_engine.py    # Image EXIF/XMP extraction
│   ├── kreuzberg_engine.py   # Text/PDF/document parsing
│   ├── mediainfo_engine.py   # Audio/video metadata
│   ├── stego_binwalk_engine.py  # Binary carving & strings
│   ├── ai_strings_engine.py  # AI-powered string analysis
│   └── ai_provider.py        # LLM auto-discovery (Ollama/LM Studio)
├── forensic/
│   ├── __init__.py
│   └── anomaly_detector.py   # Tampering & timestomping rules
├── utils/
│   ├── __init__.py
│   ├── config.py             # Configuration loader
│   ├── exporter.py           # JSON/TXT report serialization
│   ├── summary_exporter.py   # Batch summary generation
│   ├── progress_tracker.py   # Progress reporting
│   └── ui_rich.py            # Terminal rendering (Rich library)
├── tests/
│   ├── conftest.py           # pytest fixtures
│   ├── test_ai_engines.py    # AI integration tests
│   ├── test_kreuzberg_engine.py
│   ├── test_kreuzberg_orchestrator.py
│   └── fixtures/
│       ├── sample.txt
│       └── sample.md
└── README.md
```

## AI Integration (Optional)

Meta-toolkit supports AI-powered string analysis through local LLM providers. This feature is **optional** and gracefully skipped if no provider is available.

### Supported Providers

| Provider | Port | Installation |
|----------|------|---------------|
| **Ollama** | 11434 | [ollama.ai](https://ollama.ai) |
| **LM Studio** | 1234 | [lmstudio.ai](https://lmstudio.ai) |
| **vLLM** | 8000 | [vllm.readthedocs.io](https://vllm.readthedocs.io) |

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
   - Respects `AI_HOST` environment variable: `AI_HOST=192.168.1.100 ./run.sh -f file --ai`
   - Falls back gracefully if no provider found

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

### Running tests

```bash
./install-deps.sh --dev
./run.sh -f tests/fixtures/sample.txt

# Run pytest
source .venv/bin/activate
pytest -v

# Run specific test module
pytest tests/test_kreuzberg_engine.py -v
```

### Test coverage

| Module | Purpose |
|--------|----------|
| `test_ai_engines.py` | AI string analysis integration |
| `test_kreuzberg_engine.py` | Direct text/PDF extraction; error handling |
| `test_kreuzberg_orchestrator.py` | End-to-end routing through `analyze_file()` |

Tests are skipped automatically when dependencies are not installed.

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
   - Set `AI_HOST` if running on non-localhost: `AI_HOST=192.168.1.100 ./run.sh -f file --ai`

3. **Disable AI if not needed**
   - Simply omit `--ai` flag; analysis still works without it

### Timeout errors on slow systems

- Increase timeout in `config/ai.json` → `ai.timeout` (seconds)
- Reduce batch concurrency: `./run.sh -d /path --workers 4`

## License

Add your license here.
