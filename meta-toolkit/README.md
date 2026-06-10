# meta-toolkit

Enterprise-grade Linux CLI for metadata extraction and lightweight forensic analysis. Routes files through format-specific engines, applies anomaly rules, and renders results in the terminal or as JSON.

## Requirements

- **Python 3.10+**
- **Linux** (primary target; uses `stat` inode/uid/gid fields)

### Python dependencies

Installed via `requirements.txt`:

| Package   | Role                          |
|-----------|-------------------------------|
| `rich`    | Terminal tables and panels      |
| `kreuzberg` | Text/PDF/document parsing   |

### Optional system tools

Engines degrade to stub mode when a binary is missing. For full coverage, install:

| Tool        | Package (Debian/Ubuntu) | Used by              |
|-------------|-------------------------|----------------------|
| `exiftool`  | `libimage-exiftool-perl`| Image EXIF/XMP       |
| `mediainfo` | `mediainfo`             | Audio/video profiling|
| `binwalk`   | `binwalk`               | Embedded signatures  |
| `strings`   | `binutils`              | Printable strings    |

## Quick start (Linux)

```bash
git clone <repo-url> meta-toolkit
cd meta-toolkit

chmod +x install-deps.sh meta_extract
./install-deps.sh
source .venv/bin/activate

./meta_extract -f /path/to/file.pdf
./meta_extract -f /path/to/file.jpg --json
```

## Quick start (Windows)

**Command Prompt (cmd)** — use the `.bat` installer:

```bat
cd C:\Users\anima\Projects\meta-toolkit
install-deps.bat --dev
.venv\Scripts\activate.bat

python meta_extract -f tests\fixtures\sample.txt --json
pytest -v
```

**PowerShell** — use the `.ps1` installer:

```powershell
cd C:\Users\anima\Projects\meta-toolkit
powershell -ExecutionPolicy Bypass -File .\install-deps.ps1 -Dev
.\.venv\Scripts\Activate.ps1

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

```
usage: meta_extract [-h] -f FILE [--json]

Extract and forensically analyze file metadata.

options:
  -f, --file FILE   Path to the target file for analysis. (required)
  --json            Emit the full report as JSON instead of a rich terminal layout.
```

### Examples

```bash
# Rich terminal report (default)
./meta_extract -f evidence/sample.png

# Machine-readable JSON on stdout
./meta_extract -f evidence/archive.zip --json > report.json

# Redirect JSON to a file
./meta_extract -f document.pdf --json | tee out/report.json
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
├── meta_extract              # CLI entry point
├── install-deps.sh           # Linux dependency bootstrap
├── install-deps.bat          # Windows installer (Command Prompt)
├── install-deps.ps1          # Windows installer (PowerShell)
├── requirements.txt
├── requirements-dev.txt      # pytest + runtime deps
├── pytest.ini
├── core/
│   └── orchestrator.py
├── engines/
├── forensic/
│   └── anomaly_detector.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/             # sample.txt, sample.md
│   ├── test_kreuzberg_engine.py
│   └── test_kreuzberg_orchestrator.py
└── utils/
    ├── ui_rich.py
    └── exporter.py
```

## Development

```bash
source .venv/bin/activate
python meta_extract -f meta_extract --json   # smoke test
```

### Testing

Integration tests exercise the real `kreuzberg` library (sync API) against checked-in fixtures.

```bash
./install-deps.sh --dev
source .venv/bin/activate
pytest
```

| Test module | Coverage |
|-------------|----------|
| `test_kreuzberg_engine.py` | Direct engine extraction, API parity with `extract_file_sync`, error on missing file |
| `test_kreuzberg_orchestrator.py` | End-to-end routing of text/markdown through `analyze_file()` |

Tests are skipped automatically when `kreuzberg` is not installed.

## License

Add your license here.
