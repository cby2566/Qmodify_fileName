import csv
import io
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional


def _resolve_fields(data: List[dict], fields: Optional[List[str]]) -> List[str]:
    if fields:
        return fields
    if not data:
        return []
    return list(data[0].keys())


def export_to_csv(
    data: List[dict],
    fields: Optional[List[str]] = None,
    output_path: Optional[str] = None,
) -> str:
    """Export data to CSV. Returns the file path."""
    chosen = _resolve_fields(data, fields)
    if output_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".csv", prefix="rename_export_")
        output_path = tmp

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=chosen, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in chosen})

    return str(Path(output_path).resolve())


def export_to_txt(
    data: List[dict],
    fields: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    separator: str = "\t",
) -> str:
    """Export data to a delimited text file. Returns the file path."""
    chosen = _resolve_fields(data, fields)
    if output_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".txt", prefix="rename_export_")
        output_path = tmp

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(separator.join(chosen) + "\n")
        for row in data:
            line = separator.join(str(row.get(k, "")) for k in chosen)
            f.write(line + "\n")

    return str(Path(output_path).resolve())
