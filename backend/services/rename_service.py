from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import uuid
import datetime
import shutil


def apply_rules(
    stem: str,
    rules: List[dict],
    extracted_fields: Optional[Dict[str, str]] = None,
    sequence_index: int = 0,
) -> str:
    """Apply a chain of rename rules to a single file stem and return the new stem."""
    result = stem
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        rtype = rule.get("rule_type")

        if rtype == "add_prefix":
            prefix = rule.get("prefix", "")
            result = f"{prefix}{result}"

        elif rtype == "add_suffix":
            suffix = rule.get("suffix", "")
            result = f"{result}{suffix}"

        elif rtype == "insert_text":
            pos = rule.get("position", 0)
            text = rule.get("text", "")
            pos = max(0, min(pos, len(result)))
            result = result[:pos] + text + result[pos:]

        elif rtype == "find_replace":
            search = rule.get("search", "")
            replace = rule.get("replace", "")
            is_regex = rule.get("is_regex", False)
            if is_regex:
                try:
                    result = re.sub(search, replace, result)
                except re.error as e:
                    raise ValueError(f"Invalid regex in find_replace: {e}")
            else:
                result = result.replace(search, replace)

        elif rtype == "sequence":
            start = rule.get("start", 1)
            step = rule.get("step", 1)
            padding = rule.get("padding", 2)
            seq_pos = rule.get("sequence_position", "prefix")
            value = start + step * sequence_index
            token = str(value).zfill(padding)
            if seq_pos == "prefix":
                result = f"{token}{result}"
            else:
                result = f"{result}{token}"

        elif rtype == "template":
            template = rule.get("template", "")
            fields = dict(extracted_fields or {})
            # built-in fields
            fields.setdefault("__stem__", stem)
            fields.setdefault("__index__", str(sequence_index + 1))
            try:
                result = template.format(**fields)
            except KeyError as e:
                # If template field is missing, keep original stem
                # This happens when regex doesn't match this file
                pass

        elif rtype == "case_transform":
            case_type = rule.get("case_type", "lower")
            if case_type == "lower":
                result = result.lower()
            elif case_type == "upper":
                result = result.upper()
            elif case_type == "title":
                result = result.title()
            elif case_type == "capitalize":
                result = result.capitalize()

        # unknown rule_types are silently skipped

    return result


def generate_preview(
    files: List[str],
    rules: List[dict],
    regex_pattern: Optional[str] = None,
) -> List[dict]:
    """Build a preview of rename operations.

    Returns dicts with original_name, new_name, status.
    Status is one of "normal", "conflict", "unchanged".
    """
    from services.regex_service import extract_fields, validate_pattern

    # Build extracted fields per file using regex_pattern
    extracted_map: Dict[str, Dict[str, str]] = {}
    if regex_pattern:
        is_valid, err = validate_pattern(regex_pattern)
        if is_valid:
            extracted_map = extract_fields(files, regex_pattern)

    previews: List[dict] = []
    new_name_counts: Dict[str, int] = {}

    for idx, fpath in enumerate(files):
        src = Path(fpath)
        stem = src.stem
        fields = extracted_map.get(fpath, {})
        new_stem = apply_rules(stem, rules, fields, idx)
        new_name = f"{new_stem}{src.suffix}"
        new_full = str(src.parent / new_name)

        # Track for intra-batch conflict detection
        new_name_counts.setdefault(new_full, 0)
        new_name_counts[new_full] += 1

        previews.append({
            "original_path": fpath,
            "original_name": src.name,
            "new_name": new_name,
            "new_path": new_full,
            "new_stem": new_stem,
            "status": "unchanged" if new_full == fpath else "normal",
            "index": idx,
        })

    # Second pass: mark intra-batch conflicts (same new_path from >1 source)
    for p in previews:
        if new_name_counts[p["new_path"]] > 1:
            p["status"] = "conflict"

    # Third pass: mark conflicts with existing files on disk
    existing = set()
    for fpath in files:
        src = Path(fpath)
        # Also mark all sibling files that exist on disk
        try:
            if src.parent.exists():
                existing.update(str(x) for x in src.parent.iterdir() if x.is_file())
        except OSError:
            pass

    existing -= set(files)  # the original names themselves don't count as conflicts
    for p in previews:
        if p["status"] == "normal" and p["new_path"] in existing:
            p["status"] = "conflict"

    return previews


def execute_rename(operations: List[dict]) -> Tuple[str, List[dict]]:
    """Execute a list of rename operations.

    Each dict: {"original_path": ..., "new_path": ...}
    Returns (batch_id, results).
    """
    batch_id = uuid.uuid4().hex
    ts = datetime.datetime.now().isoformat()
    results: List[dict] = []

    for op in operations:
        src = Path(op["original_path"])
        dst = Path(op["new_path"])
        if src == dst:
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "success",
                "message": "unchanged",
                "created_at": ts,
            })
            continue
        try:
            if dst.exists():
                raise FileExistsError(f"Target already exists: {dst}")
            src.rename(dst)
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "success",
                "message": "renamed",
                "created_at": ts,
            })
        except Exception as e:
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "failed",
                "message": str(e),
                "created_at": ts,
            })

    return batch_id, results
