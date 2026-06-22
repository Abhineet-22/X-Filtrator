from __future__ import annotations

from io import StringIO

from utils.exporter import export_txt
from utils.exporter import _strip_tesseract_leak_lines


def test_strip_tesseract_leak_lines_keeps_real_output() -> None:
    text = """ObjectCache(0x1)::~ObjectCache(): WARNING! LEAK! object 0x2 still has count 1 (id /usr/share/tesseract-ocr/5/tessdata/eng.traineddatalstm-punc-dawg)
real line
ObjectCache(0x3)::~ObjectCache(): WARNING! LEAK! object 0x4 still has count 1 (id /usr/share/tesseract-ocr/5/tessdata/eng.traineddatalstm-word-dawg)
"""

    assert _strip_tesseract_leak_lines(text) == "real line"


def test_export_txt_filters_tesseract_leak_lines() -> None:
    report = {
        "file": "/tmp/sample.txt",
        "mime_type": "text/plain",
        "stat": {},
        "forensic": {"risk_level": "none", "flags": []},
        "metadata": {
            "kreuzberg": {
                "engine": "kreuzberg",
                "status": "ok",
                "text_preview": "ObjectCache(0x1)::~ObjectCache(): WARNING! LEAK! object 0x2 still has count 1 (id /usr/share/tesseract-ocr/5/tessdata/eng.traineddatalstm-punc-dawg)\nvisible text",
            }
        },
    }

    buffer = StringIO()
    export_txt(report, buffer)

    output = buffer.getvalue()

    assert "ObjectCache(" not in output
    assert "visible text" in output