from pathlib import Path
from typing import List, Optional
import re
import datetime
from models.file_models import FileInfo


def _get_filter(filters: dict, snake_name: str, camel_name: str = None):
    if snake_name in filters:
        return filters.get(snake_name)
    if camel_name and camel_name in filters:
        return filters.get(camel_name)
    return None


def filter_files(files: List[FileInfo], filters: dict) -> List[FileInfo]:
    """Apply a dict of filters to a list of FileInfo objects."""
    result = list(files)

    extensions = _get_filter(filters, "extensions")
    if extensions:
        ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
        result = [f for f in result if f.extension.lower() in ext_set]

    size_min = _get_filter(filters, "size_min", "sizeMin")
    if size_min is not None:
        result = [f for f in result if f.size_bytes >= int(size_min)]

    size_max = _get_filter(filters, "size_max", "sizeMax")
    if size_max is not None:
        result = [f for f in result if f.size_bytes <= int(size_max)]

    date_from = _get_filter(filters, "date_from", "dateFrom")
    if date_from:
        df = datetime.datetime.fromisoformat(date_from)
        result = [f for f in result
                  if datetime.datetime.fromisoformat(f.modified_time) >= df]

    date_to = _get_filter(filters, "date_to", "dateTo")
    if date_to:
        dt = datetime.datetime.fromisoformat(date_to)
        result = [f for f in result
                  if datetime.datetime.fromisoformat(f.modified_time) <= dt]

    keyword_include = _get_filter(filters, "keyword_include", "keywordInclude")
    if keyword_include:
        kw = keyword_include.lower()
        result = [f for f in result if kw in f.stem.lower()]

    keyword_exclude = _get_filter(filters, "keyword_exclude", "keywordExclude")
    if keyword_exclude:
        kw = keyword_exclude.lower()
        result = [f for f in result if kw not in f.stem.lower()]

    regex_pattern = _get_filter(filters, "regex_pattern", "regexPattern")
    if regex_pattern:
        try:
            pat = re.compile(regex_pattern, re.IGNORECASE)
            result = [f for f in result if pat.search(f.stem)]
        except re.error:
            raise ValueError(f"Invalid regex pattern: {regex_pattern}")

    return result
