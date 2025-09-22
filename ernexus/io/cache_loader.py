import os
import pickle
from typing import Tuple
from unstructured import *
# Expected files
FILENAMES = [
    "tables.pkl",
    "texts.pkl",
    "images.pkl",
    "text_summaries.pkl",
    "table_summaries.pkl",
    "image_summaries.pkl",
]

def _load_one(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

def load_cached_data(directory: str) -> Tuple[list, list, list, list, list, list]:
    """Load the six expected .pkl artifacts from directory.
    Returns (tables, texts, images, text_summaries, table_summaries, image_summaries).
    Raises helpful errors if something is missing.
    """
    missing = [fn for fn in FILENAMES if not os.path.exists(os.path.join(directory, fn))]
    if missing:
        raise FileNotFoundError(
            "Missing required cache files: " + ", ".join(missing) +
            f"\nPlace them under: {directory}"
        )

    tables = _load_one(os.path.join(directory, "tables.pkl"))
    texts = _load_one(os.path.join(directory, "texts.pkl"))
    images = _load_one(os.path.join(directory, "images.pkl"))
    text_summaries = _load_one(os.path.join(directory, "text_summaries.pkl"))
    table_summaries = _load_one(os.path.join(directory, "table_summaries.pkl"))
    image_summaries = _load_one(os.path.join(directory, "image_summaries.pkl"))

    return tables, texts, images, text_summaries, table_summaries, image_summaries
