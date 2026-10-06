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


# ---------------------------------------------------------------------------
# Provenance ("span") tracking
#
# The preview UI highlights which parts of the new name each rule produced.
# Diffing old/new strings after the fact is fragile (coincidental characters
# anchor the diff), so the engine tracks provenance while applying rules.
# The stem is kept as a list of pieces:
#
#     {"text": str, "origin": Optional[{"rule": int, "type": str}]}
#
# origin is None for text inherited from the original stem. Every rule
# rewrites the piece list; concatenating the piece texts always equals the
# stem the plain string implementation would have produced.
# ---------------------------------------------------------------------------


def _pieces_text(pieces: List[dict]) -> str:
    return "".join(p["text"] for p in pieces)


def _mk_piece(text: str, origin: Optional[dict]) -> dict:
    return {"text": text, "origin": origin}


def _insert_piece(pieces: List[dict], offset: int, text: str, origin: dict) -> List[dict]:
    """Insert ``text`` at char ``offset`` of the concatenated stem."""
    if not text:
        return pieces
    new_piece = _mk_piece(text, origin)
    if offset <= 0:
        return [new_piece] + pieces
    out: List[dict] = []
    pos = 0
    done = False
    for p in pieces:
        p_start = pos
        p_end = pos + len(p["text"])
        pos = p_end
        if not done and p_start < offset < p_end:
            cut = offset - p_start
            out.append(_mk_piece(p["text"][:cut], p["origin"]))
            out.append(new_piece)
            out.append(_mk_piece(p["text"][cut:], p["origin"]))
            done = True
            continue
        out.append(p)
        if not done and p_end == offset:
            out.append(new_piece)
            done = True
    if not done:
        out.append(new_piece)
    return out


def _replace_span(pieces: List[dict], start: int, end: int, text: str, origin: dict) -> List[dict]:
    """Replace chars ``[start, end)`` of the concatenated stem with ``text``."""
    if start == end:
        return _insert_piece(pieces, start, text, origin)
    out: List[dict] = []
    pos = 0
    inserted = False
    for p in pieces:
        p_start = pos
        p_end = pos + len(p["text"])
        pos = p_end
        if p_end <= start or p_start >= end:
            out.append(p)
            continue
        if p_start < start:
            out.append(_mk_piece(p["text"][: start - p_start], p["origin"]))
        if not inserted:
            if text:
                out.append(_mk_piece(text, origin))
            inserted = True
        if p_end > end:
            out.append(_mk_piece(p["text"][end - p_start :], p["origin"]))
    return [p for p in out if p["text"]]


def _plain_replace_pieces(pieces: List[dict], search: str, replace: str, origin: dict) -> List[dict]:
    """Mirror ``str.replace`` semantics (left-to-right, non-overlapping)."""
    text = _pieces_text(pieces)
    if search == "":
        # "abc".replace("", "-") == "-a-b-c-": an insertion at every gap.
        edits = [(i, i) for i in range(len(text) + 1)]
    else:
        edits = []
        pos = 0
        while True:
            i = text.find(search, pos)
            if i < 0:
                break
            edits.append((i, i + len(search)))
            pos = i + len(search)
    for start, end in reversed(edits):
        pieces = _replace_span(pieces, start, end, replace, origin)
    return pieces


def _regex_replace_pieces(pieces: List[dict], pattern: str, replace: str, origin: dict) -> List[dict]:
    """Mirror ``re.sub`` exactly by letting ``sub`` itself compute the matches.

    The callback records each match range and its expanded replacement; the
    edits are then replayed on the piece list right-to-left so offsets stay
    valid. Since ``re.sub`` produces the match list itself, zero-width-match
    edge cases can never diverge from the classic implementation.
    """
    edits: List[Tuple[int, int, str]] = []

    def _record(m) -> str:
        expanded = m.expand(replace)
        edits.append((m.start(), m.end(), expanded))
        return expanded

    try:
        re.sub(pattern, _record, _pieces_text(pieces))
    except re.error as e:
        raise ValueError(f"Invalid regex in find_replace: {e}")
    for start, end, expanded in reversed(edits):
        pieces = _replace_span(pieces, start, end, expanded, origin)
    return pieces


def apply_rules_tracked(
    stem: str,
    rules: List[dict],
    extracted_fields: Optional[Dict[str, str]] = None,
    sequence_index: int = 0,
) -> Tuple[str, List[dict]]:
    """Apply a chain of rename rules and report which span each rule produced.

    Returns ``(new_stem, spans)``. Each span is
    ``{"start", "end", "type", "rule"}`` in new-stem coordinates, which are
    also valid on the full new name because the extension is appended
    untouched. ``rule`` is the index of the rule in the original chain
    (disabled rules included).
    """
    pieces: List[dict] = [_mk_piece(stem, None)] if stem else []

    for rule_index, rule in enumerate(rules):
        if not rule.get("enabled", True):
            continue
        rtype = rule.get("rule_type")
        origin = {"rule": rule_index, "type": rtype}

        if rtype == "add_prefix":
            pieces = _insert_piece(pieces, 0, rule.get("prefix", ""), origin)

        elif rtype == "add_suffix":
            pieces = _insert_piece(pieces, len(_pieces_text(pieces)), rule.get("suffix", ""), origin)

        elif rtype == "insert_text":
            pos = rule.get("position", 0)
            pos = max(0, min(pos, len(_pieces_text(pieces))))
            pieces = _insert_piece(pieces, pos, rule.get("text", ""), origin)

        elif rtype == "find_replace":
            search = rule.get("search", "")
            replace = rule.get("replace", "")
            if rule.get("is_regex", False):
                pieces = _regex_replace_pieces(pieces, search, replace, origin)
            else:
                pieces = _plain_replace_pieces(pieces, search, replace, origin)

        elif rtype == "sequence":
            start = rule.get("start", 1)
            step = rule.get("step", 1)
            padding = rule.get("padding", 2)
            seq_pos = rule.get("sequence_position", "prefix")
            token = str(start + step * sequence_index).zfill(padding)
            at = 0 if seq_pos == "prefix" else len(_pieces_text(pieces))
            pieces = _insert_piece(pieces, at, token, origin)

        elif rtype == "template":
            template = rule.get("template", "")
            fields = dict(extracted_fields or {})
            # built-in fields
            fields.setdefault("__stem__", stem)
            fields.setdefault("__index__", str(sequence_index + 1))
            try:
                rendered = template.format(**fields)
            except KeyError:
                # If template field is missing, keep original stem.
                # This happens when regex doesn't match this file.
                continue
            pieces = [_mk_piece(rendered, origin)] if rendered else []

        elif rtype == "case_transform":
            case_type = rule.get("case_type", "lower")
            text = _pieces_text(pieces)
            if case_type == "lower":
                transformed = text.lower()
            elif case_type == "upper":
                transformed = text.upper()
            elif case_type == "title":
                transformed = text.title()
            elif case_type == "capitalize":
                transformed = text.capitalize()
            else:
                continue
            if len(transformed) == len(text):
                # Positions preserved: re-split the transformed string at the
                # old piece boundaries so provenance stays exact (per-piece
                # transforms would diverge at boundaries for title/capitalize).
                new_pieces: List[dict] = []
                pos = 0
                for p in pieces:
                    end = pos + len(p["text"])
                    new_pieces.append(_mk_piece(transformed[pos:end], p["origin"]))
                    pos = end
                pieces = [p for p in new_pieces if p["text"]]
            else:
                # Length-changing transforms ('ß'.upper() == 'SS') make
                # provenance unmappable — drop highlighting for the whole stem
                # rather than paint the wrong characters.
                pieces = [_mk_piece(transformed, None)] if transformed else []

        # unknown rule_types are silently skipped

    new_stem = _pieces_text(pieces)
    spans: List[dict] = []
    pos = 0
    for p in pieces:
        if p["origin"] and p["text"]:
            span = {
                "start": pos,
                "end": pos + len(p["text"]),
                "type": p["origin"]["type"],
                "rule": p["origin"]["rule"],
            }
            last = spans[-1] if spans else None
            if (
                last
                and last["end"] == span["start"]
                and last["type"] == span["type"]
                and last["rule"] == span["rule"]
            ):
                last["end"] = span["end"]
            else:
                spans.append(span)
        pos += len(p["text"])
    return new_stem, spans


def apply_rules(
    stem: str,
    rules: List[dict],
    extracted_fields: Optional[Dict[str, str]] = None,
    sequence_index: int = 0,
) -> str:
    """Apply a chain of rename rules to a single file stem and return the new stem."""
    return apply_rules_tracked(stem, rules, extracted_fields, sequence_index)[0]




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
        new_stem, spans = apply_rules_tracked(body, rules, fields, idx)
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
            "spans": spans,
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

