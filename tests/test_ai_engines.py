import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(ROOT)
)
from engines.ai_strings_engine import analyze

result = analyze([
    "Adobe Photoshop",
    "ICC_PROFILE",
    "GPSLatitude",
    "GPSLongitude",
])

print(result)