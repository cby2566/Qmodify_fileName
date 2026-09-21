from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import sys
import uuid
import datetime


def _split_name(path: Path, is_dir: bool) -> Tuple[str, str]:
    """Return (mutable part, preserved tail) of a path's name.

    Files only transform their stem and keep the extension; directories have
    no extension concept, so the whole name is transformed.
    """
    if is_dir:
        return path.name, ""
    return path.stem, path.suffix


def _norm_key(path_str: str) -> str:
    """Normalize a path for conflict comparison.

    Windows filesystems are case-insensitive, so ``A`` and ``a`` collide there.
    """
    key = str(Path(path_str)).replace("/", "\\") if sys.platform == "win32" else str(path_str)
    return key.lower() if sys.platform == "win32" else key


def _path_depth(path_str: str) -> int:
    """Number of path components outside the drive/root (used for ordering).

    ``C:\\a\\b`` -> 2, ``/a/b/c`` -> 3. Deeper paths must be renamed first so
    that renaming a parent never invalidates a child path mid-batch.
    """
    parts = Path(path_str).parts
    return sum(1 for p in parts if p not in ("\\", "/") and not p.endswith(("\\", ":")))


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    """True when ``ancestor`` is a strict ancestor directory path of ``descendant``."""
    if ancestor == descendant:
        return False
    try:
        a = Path(ancestor)
        d = Path(descendant)
        return a in d.parents
    except (OSError, ValueError):
        return False


def _mark_parent_child_conflicts(previews: List[dict]) -> None:
    """Flag batches that rename both a directory and something inside/under it.

    Renaming the parent first would invalidate the child's path, so such
    batches are rejected at preview time instead of failing mid-execution.
    """
    paths = [p["original_path"] for p in previews]
    for p in previews:
        if p["status"] != "normal":
            continue
        for other in paths:
            if _is_ancestor(other, p["original_path"]):
                p["status"] = "conflict"
                p["conflict_reason"] = (
                    f"父目录也在本次批次中：{other}"
                )
                break


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

    Whether a path is a directory is resolved server-side via ``Path.is_dir()``
    so the client cannot desync the stem/suffix split.
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
        is_dir = src.is_dir()
        body, tail = _split_name(src, is_dir)
        fields = extracted_map.get(fpath, {})
        new_stem = apply_rules(body, rules, fields, idx)
        new_name = f"{new_stem}{tail}"
        new_full = str(src.parent / new_name)

        # Track for intra-batch conflict detection. Compare case-insensitively
        # on Windows so that only-case-different targets are caught too.
        key = _norm_key(new_full)
        new_name_counts.setdefault(key, 0)
        new_name_counts[key] += 1

        previews.append({
            "original_path": fpath,
            "original_name": src.name,
            "new_name": new_name,
            "new_path": new_full,
            "new_stem": new_stem,
            "status": "unchanged" if new_full == fpath else "normal",
            "index": idx,
            "is_dir": is_dir,
        })

    # Second pass: mark intra-batch conflicts (same new_path from >1 source)
    for p in previews:
        if new_name_counts[_norm_key(p["new_path"])] > 1:
            p["status"] = "conflict"
            p.setdefault("conflict_reason", "批次内多个条目产生相同的目标名称")

    # Third pass: mark conflicts with anything existing on disk in the same dir
    existing = set()
    for fpath in files:
        src = Path(fpath)
        try:
            if src.parent.exists():
                existing.update(_norm_key(str(x)) for x in src.parent.iterdir())
        except OSError:
            pass

    # The original names themselves are not conflicts (they will be vacated).
    existing -= {_norm_key(f) for f in files}
    for p in previews:
        if p["status"] == "normal" and _norm_key(p["new_path"]) in existing:
            p["status"] = "conflict"
            p["conflict_reason"] = "目标名称已被占用"

    # Fourth pass: reject batches touching a directory and its own descendants.
    _mark_parent_child_conflicts(previews)

    return previews


def _safe_rename(src: Path, dst: Path) -> None:
    """Rename with a two-step hop for case-only changes.

    Windows may refuse an in-place case rename (``Foo`` -> ``foo``), so route
    it through a temporary name.
    """
    if src.parent == dst.parent and src.name != dst.name and src.name.lower() == dst.name.lower():
        tmp = src.with_name(f"__rename_tmp_{uuid.uuid4().hex}")
        src.rename(tmp)
        try:
            tmp.rename(dst)
        except Exception:
            tmp.rename(src)  # restore the original name on failure
            raise
        return
    src.rename(dst)


def execute_rename(operations: List[dict]) -> Tuple[str, List[dict]]:
    """Execute a list of rename operations as an all-or-nothing batch.

    Each dict: {"original_path": ..., "new_path": ...}
    Operations run deepest-first so that a rename never invalidates a
    not-yet-processed path. If any step fails, the already-applied steps are
    rolled back in reverse order before returning.
    Returns (batch_id, results).
    """
    batch_id = uuid.uuid4().hex
    ts = datetime.datetime.now().isoformat()
    results: List[dict] = []

    ordered = sorted(operations, key=lambda op: _path_depth(op["original_path"]), reverse=True)
    applied: List[Tuple[Path, Path]] = []

    for op in ordered:
        src = Path(op["original_path"])
        dst = Path(op["new_path"])
        if src == dst:
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "success",
                "message": "unchanged",
                "is_dir": src.is_dir(),
                "created_at": ts,
            })
            continue
        try:
            if not src.exists():
                raise FileNotFoundError(f"Source missing: {src}")
            if dst.exists() and _norm_key(str(src)) != _norm_key(str(dst)):
                raise FileExistsError(f"Target already exists: {dst}")
            _safe_rename(src, dst)
            applied.append((src, dst))
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "success",
                "message": "renamed",
                "is_dir": src.is_dir(),
                "created_at": ts,
            })
        except Exception as e:
            results.append({
                "batch_id": batch_id,
                "original_path": str(src),
                "new_path": str(dst),
                "status": "failed",
                "message": str(e),
                "is_dir": src.is_dir(),
                "created_at": ts,
            })
            rollback_errors = _rollback(applied)
            for r in results:
                if r["status"] == "success":
                    r["status"] = "rolled_back"
                    r["message"] = "batch rolled back"
            results.append({
                "batch_id": batch_id,
                "original_path": "",
                "new_path": "",
                "status": "rolled_back",
                "message": (
                    f"批次整体回滚（失败原因：{e}）"
                    + (f"；回滚时另有 {len(rollback_errors)} 项失败" if rollback_errors else "")
                ),
                "is_dir": False,
                "created_at": ts,
            })
            break

    return batch_id, results


def _rollback(applied: List[Tuple[Path, Path]]) -> List[str]:
    """Reverse the applied renames, newest first. Returns error messages."""
    errors: List[str] = []
    for src, dst in reversed(applied):
        try:
            if dst.exists() and not src.exists():
                dst.rename(src)
        except Exception as e:  # pragma: no cover - defensive
            errors.append(f"{dst} -> {src}: {e}")
    return errors

