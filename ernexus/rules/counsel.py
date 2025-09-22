from __future__ import annotations

# Lightweight rule helper (no patient data; just general flags)
FLAG_WORDS = [
    ("grapefruit", "May interact with certain meds; verify with clinician."),
    ("star fruit", "Neurotoxic risk in kidney disease; generally avoid."),
    ("herbal", "Herbal supplements can accumulate or interact; caution."),
]

def diet_safety_notes(user_q: str) -> str:
    q = user_q.lower()
    notes = []
    for word, msg in FLAG_WORDS:
        if word in q:
            notes.append(f"{word}: {msg}")
    return "; ".join(notes)
