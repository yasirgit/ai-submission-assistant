"""Identity of a submission's business content, used to reject duplicates."""

import hashlib
import json


def content_fingerprint(company_id: str, coverage: dict, narrative: str) -> str:
    payload = {
        "company_id": company_id,
        "coverage": coverage,
        "narrative": " ".join(narrative.split()),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()
