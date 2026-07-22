import sqlite3
import uuid
import datetime
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# 支持环境变量配置数据目录（桌面模式），默认为 backend/data/
_data_dir = os.environ.get("FILERENAMER_DATA_DIR")
if _data_dir:
    DB_PATH = Path(_data_dir) / "logs.db"
else:
    DB_PATH = Path(__file__).resolve().parent.parent / "data" / "logs.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create the rename_logs table if it does not exist."""
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rename_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                original_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'success',
                message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_batch_id
            ON rename_logs(batch_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_created_at
            ON rename_logs(created_at)
        """)


def log_batch(
    batch_id: str,
    operations: List[dict],
    directory: str = "",
) -> str:
    """Persist a batch of rename operations. Returns the batch_id."""
    ts = datetime.datetime.now().isoformat()
    with _conn() as conn:
        for op in operations:
            conn.execute(
                """INSERT INTO rename_logs
                   (batch_id, original_path, new_path, status, message, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    batch_id,
                    op.get("original_path", ""),
                    op.get("new_path", ""),
                    op.get("status", "success"),
                    op.get("message"),
                    op.get("created_at", ts),
                ),
            )
    return batch_id


def get_logs(
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None,
) -> Tuple[List[dict], int]:
    """Return (rows, total_count) with optional filters."""
    filters = filters or {}
    where = []
    params = []

    if filters.get("batch_id"):
        where.append("batch_id = ?")
        params.append(filters["batch_id"])
    if filters.get("status"):
        where.append("status = ?")
        params.append(filters["status"])
    if filters.get("date_from"):
        where.append("created_at >= ?")
        params.append(filters["date_from"])
    if filters.get("date_to"):
        where.append("created_at <= ?")
        params.append(filters["date_to"])

    where_clause = (" WHERE " + " AND ".join(where)) if where else ""

    with _conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM rename_logs{where_clause}", params
        ).fetchone()[0]

        offset = (max(page, 1) - 1) * page_size
        rows = conn.execute(
            f"""SELECT id, batch_id, original_path, new_path, status, message, created_at
                FROM rename_logs{where_clause}
                ORDER BY id DESC LIMIT ? OFFSET ?""",
            params + [page_size, offset],
        ).fetchall()

    return [dict(r) for r in rows], total


def clear_logs(older_than_days=None) -> int:
    """Delete logs. If older_than_days is given, only delete entries older than that."""
    with _conn() as conn:
        if older_than_days is not None:
            cutoff = (
                datetime.datetime.now() - datetime.timedelta(days=older_than_days)
            ).isoformat()
            cur = conn.execute(
                "DELETE FROM rename_logs WHERE created_at < ?", (cutoff,)
            )
        else:
            cur = conn.execute("DELETE FROM rename_logs")
        return cur.rowcount


def get_batch(batch_id: str) -> Optional[dict]:
    """Return a single batch summary with its operations."""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT id, batch_id, original_path, new_path, status, message, created_at
               FROM rename_logs WHERE batch_id = ?
               ORDER BY id ASC""",
            (batch_id,),
        ).fetchall()
    if not rows:
        return None
    operations = [dict(r) for r in rows]
    return {
        "batch_id": batch_id,
        "total": len(operations),
        "succeeded": sum(1 for o in operations if o["status"] == "success"),
        "failed": sum(1 for o in operations if o["status"] != "success"),
        "created_at": operations[0]["created_at"],
        "operations": operations,
    }


def get_all_batches() -> List[dict]:
    """Return a summary of all operation batches, ordered by most recent."""
    with _conn() as conn:
        rows = conn.execute("""
            SELECT batch_id, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as succeeded,
                   SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as failed,
                   MIN(created_at) as created_at
            FROM rename_logs
            GROUP BY batch_id
            ORDER BY created_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


# Auto-initialize on import
init_db()
