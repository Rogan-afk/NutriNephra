# ernexus/formatting.py
from __future__ import annotations
import re
from textwrap import wrap

_BULLET = "•"  # nice, compact bullet

def _collapse_ws(s: str) -> str:
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    return s.strip()

def _strip_refs_artifacts(s: str) -> str:
    # Remove leftover citation markers like [12], (2021), “Figure 2:”, etc.
    s = re.sub(r"\[[0-9,\- ]{1,8}\]", "", s)
    s = re.sub(r"\((?:19|20)\d{2}\)", "", s)
    s = re.sub(r"^\s*(figure|table)\s*\d+[:\-]\s*", "", s, flags=re.I)
    return s.strip()

def _normalize_punctuation(s: str) -> str:
    s = re.sub(r"\s*–\s*", " – ", s)
    s = re.sub(r"\s*—\s*", " — ", s)
    s = re.sub(r"\s*-\s*", " - ", s)  # unify dashes in source text
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def sanitize_summary(s: str) -> str:
    """Normalize any summary/snippet to be clean, single-line-ish text."""
    return _normalize_punctuation(_strip_refs_artifacts(_collapse_ws(s)))

def bulletize(s: str, max_line=88) -> str:
    """
    Turn raw sentences into 4–8 short bullet lines.
    """
    s = sanitize_summary(s)
    # Split on typical separators
    parts = re.split(r"(?<=[.;:])\s+|•|\u2022|- ", s)
    parts = [p.strip(" .;:-") for p in parts if p.strip(" .;:-")]
    # Keep it tight
    bullets = []
    for p in parts:
        if len(p) > max_line:
            # hard wrap long ones
            wrapped = wrap(p, width=max_line)
            if wrapped:
                bullets.append(wrapped[0])
        else:
            bullets.append(p)
        if len(bullets) >= 8:
            break
    if not bullets:
        bullets = [s[:max_line]]
    return "\n".join(f"{_BULLET} {b}" for b in bullets)

def tighten_answer(ans: str, max_line=120) -> str:
    """
    Best-effort compressor for model outputs.
    - Keep bullets short
    - Remove “Consult with healthcare providers …”
    - Ensure a single neutral disclaimer line at end
    """
    if not ans:
        return ans

    # Remove common “consult” phrasing (your request)
    ans = re.sub(r"(?i)\bconsult\s+with\s+(?:your\s+)?healthcare\s+provider[s]?\b.*", "", ans)
    ans = re.sub(r"(?i)\bseek\s+medical\s+advice\b.*", "", ans)

    # Convert dense runs of text into bullets if needed
    lines = [ln.strip() for ln in ans.splitlines() if ln.strip()]
    # Pull out existing bullets or make them
    if sum(1 for ln in lines if ln.startswith(("-", "*", "•"))) < 2:
        # not really a list → build bullets
        ans = bulletize(" ".join(lines), max_line=max_line)
    else:
        # soft-wrap long bullet lines
        fixed = []
        for ln in lines:
            if ln.startswith(("-", "*", "•")) and len(ln) > max_line:
                fixed.append(ln[:max_line-1] + "…")
            else:
                fixed.append(ln)
        ans = "\n".join(fixed)

    # Add neutral disclaimer if not present
    if "not a substitute for medical advice" not in ans.lower():
        ans += "\n\n**Note:** Educational summary only; not a substitute for medical advice."
    return ans.strip()

def short_snippet(s: str, width=160) -> str:
    s = sanitize_summary(s)
    return (s[: width - 1] + "…") if len(s) > width else s

def format_image_caption(summary: str, width=140) -> str:
    return short_snippet(summary, width=width)
