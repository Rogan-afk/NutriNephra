import re
from typing import Tuple

BANNED = [
    r"\bkill\b",
    r"\bbomb\b",
    r"\bhate\b",
]

INJECTION_SIGNS = [
    r"ignore (all|previous) instructions",
    r"act as",
    r"system prompt",
]

def validate_query(q: str) -> Tuple[bool, str]:
    if not q or len(q) < 3:
        return False, "Please enter a meaningful question."

    if sum(ch.isalpha() for ch in q) < 3:
        return False, "Query looks like gibberish. Try rephrasing with more detail."

    for pat in BANNED:
        if re.search(pat, q, flags=re.IGNORECASE):
            return False, "Your query includes disallowed content. Please rephrase academically."

    for pat in INJECTION_SIGNS:
        if re.search(pat, q, flags=re.IGNORECASE):
            return False, "Nice try 😅 but I can’t change my safety rules. Ask about CKD/ESRD diet or microbiome."

    return True, ""
