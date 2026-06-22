from __future__ import annotations

import json
import time
from typing import Any

from engines.ai_provider import generate


PROMPT_TEMPLATE = """
You are a digital forensic analyst.

Analyze the following extracted strings.

Identify:

1. Software names
2. Usernames
3. Email addresses
4. URLs
5. GPS indicators
6. Editing software
7. Malware indicators
8. Hidden payload indicators
9. Suspicious findings

Return a JSON object only.

Do not use markdown.
Do not use code fences.
Do not explain your reasoning.
Do not include any text before or after the JSON.

Schema:

{{
  "summary": "",
  "risk_level": "low|medium|high",
  "software": [],
  "urls": [],
  "emails": [],
  "possible_usernames": [],
  "suspicious_indicators": [],
  "investigator_notes": []
}}

Strings:

{strings}
"""


def analyze(
    strings: list[str],
) -> dict[str, Any]:

    start_time = time.perf_counter()

    if not strings:

        return {
            "engine": "ai_strings",
            "status": "empty",
        }

    strings_blob = "\n".join(
        strings[:300]
    )

    prompt = PROMPT_TEMPLATE.format(
        strings=strings_blob
    )
    provider_response: dict[str, Any] = {}

    raw = ""

    try:

        provider_response = generate(
            prompt
        )

        raw = provider_response["text"]

        result = json.loads(raw)

        result["engine"] = "ai_strings"
        result["status"] = "ok"

        result["provider"] = (
            provider_response["provider"]
        )

        result["model"] = (
            provider_response["model"]
        )

        result["strings_analyzed"] = (
            len(strings)
        )

        result["inference_time"] = round(
            time.perf_counter() - start_time,
            2,
        )

        return result

    except json.JSONDecodeError as exc:

        return {
            "engine": "ai_strings",
            "status": "parse_error",
            "error": str(exc),
            "provider": provider_response.get(
                "provider",
                "unknown",
            ) if "provider_response" in locals() else "unknown",
            "model": provider_response.get(
                "model",
                "unknown",
            ) if "provider_response" in locals() else "unknown",
            "raw_response": raw if "raw" in locals() else "",
        }

    except Exception as exc:

        return {
            "engine": "ai_strings",
            "status": "error",
            "error": str(exc),
        }