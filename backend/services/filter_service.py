from pathlib import Path
from typing import List, Optional
import re
import datetime
from models.file_models import FileInfo


def filter_files(files: List[FileInfo], filters: dict) -> List[FileInfo]:
    """Apply a dict of filters to a list of FileInfo objects."""
    result = list(files)

    extensions = filters.get("extensions")
    if extensions:
        ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
        result = [f for f in result if f.extension.lower() in ext_set]

    size_min = filters.get("size_min")
    if size_min is not None:
        result = [f for f in result if f.size_bytes >= int(size_min)]

    size_max = filters.get("size_max")
    if size_max is not None:
        result = [f for f in result if f.size_bytes <= int(size_max)]

    date_from = filters.get("date_from")
    if date_from:
        df = datetime.datetime.fromisoformat(date_from)
        result = [f for f in result
                  if datetime.datetime.fromisoformat(f.modified_time) >= df]

    date_to = filters.get("date_to")
    if date_to:
        dt = datetime.datetime.fromisoformat(date_to)
        result = [f for f in result
                  if datetime.datetime.fromisoformat(f.modified_time) <= dt]

    keyword_include = filters.get("keyword_include")
    if keyword_include:
        kw = keyword_include.lower()
        result = [f for f in result if kw in f.stem.lower()]

    keyword_exclude = filters.get("keyword_exclude")
    if keyword_exclude:
        kw = keyword_exclude.lower()
        result = [f for f in result if kw not in f.stem.lower()]

    regex_pattern = filters.get("regex_pattern")
    if regex_pattern:
        try:
            pat = re.compile(regex_pattern, re.IGNORECASE)
            result = [f for f in result if pat.search(f.stem)]
        except re.error:
            raise ValueError(f"Invalid regex pattern: {regex_pattern}")

    return result
