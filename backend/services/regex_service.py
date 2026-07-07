from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import re


def validate_pattern(pattern: str) -> Tuple[bool, Optional[str]]:
    """Validate a regex pattern. Returns (is_valid, error_message)."""
    try:
        re.compile(pattern)
        return True, None
    except re.error as e:
        return False, str(e)


def extract_fields(
    files: List[Union[str, object]],
    pattern: str,
) -> Dict[str, Dict[str, str]]:
    """Run a named/group regex against each file stem.

    Args:
        files: List of file paths (str) or FileInfo objects
        pattern: Regex pattern with optional named groups
    
    Returns {filepath: {group_name: matched_value}}.
    """
    is_valid, err = validate_pattern(pattern)
    if not is_valid:
        raise ValueError(f"Invalid regex pattern: {err}")

    compiled = re.compile(pattern)
    extracted: Dict[str, Dict[str, str]] = {}

    for f in files:
        # Handle both string paths and FileInfo objects
        if isinstance(f, str):
            fpath = f
            stem = Path(f).stem
        else:
            fpath = f.full_path
            stem = f.stem
        
        m = compiled.search(stem)
        if not m:
            continue
        groups = {}
        # named groups first
        if m.groupdict():
            groups.update({k: (v or "") for k, v in m.groupdict().items()})
        # indexed groups (1-based) without explicit names
        else:
            for i, val in enumerate(m.groups(), start=1):
                groups[str(i)] = val or ""
        extracted[fpath] = groups

    return extracted


def group_by_field(
    extracted: Dict[str, Dict[str, str]],
    field: str,
) -> Dict[str, List[str]]:
    """Group file paths by a single extracted field value."""
    groups: Dict[str, List[str]] = {}
    for filepath, fields in extracted.items():
        key = fields.get(field, "__ungrouped__")
        groups.setdefault(key, []).append(filepath)
    # Sort each bucket for stable output
    for k in groups:
        groups[k].sort()
    return groups
