# -*- coding: utf-8 -*-
"""
Minimal TypeSafe System One client (standard library only, Python 3.9+).

Docs: https://docs.typesafe.ai/api
"""

import json
import os
import random
import time
import urllib.error
import urllib.request

API_KEY_ENV = "TYPESAFE_API_KEY"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
RETRY_STATUSES = {429, 500, 502, 503, 504, 529}


class TypeSafeError(Exception):
    """Raised when TypeSafe is unconfigured or a request ultimately fails."""


def is_configured():
    return bool(os.environ.get(API_KEY_ENV))


def system_one(state, questions, model=DEFAULT_MODEL, timeout=15.0, max_retries=4):
    """Ask typed questions about `state`; returns the response's `answers` dict keyed by question id."""
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise TypeSafeError(f"{API_KEY_ENV} is not set")
    base_url = os.environ.get("TYPESAFE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    body = json.dumps({"state": state, "model": model, "questions": questions}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/v1/systemone",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())["answers"]
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_STATUSES or attempt == max_retries:
                detail = e.read().decode("utf-8", "replace")[:300]
                raise TypeSafeError(f"TypeSafe request failed ({e.code}): {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == max_retries:
                raise TypeSafeError(f"TypeSafe request failed: {e}") from e
        time.sleep(min(20.0, 0.5 * 2 ** attempt) * (1 + random.random() / 4))
