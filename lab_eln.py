"""Local electronic lab notebook.

The SQLite database and all attached original files live together in one
folder. Every public method opens and closes its own short-lived connection so
that Streamlit reruns do not leak file handles. Attachments are stored under a
UUID name; the original filename is kept only as metadata.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

MAX_MEDIA_BYTES = 50 * 1024 * 1024
#: Common formats shown in the documentation. The universal importer accepts
#: any other extension too, except for the executable formats below.
ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".heic", ".bmp",
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".csv",
    ".tsv", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".odp",
    ".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mov",
    ".zip", ".7z",
}
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr", ".ps1", ".dll",
    ".app", ".sh", ".jar", ".vbs", ".js",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
#: Folder colours offered by the dashboard. The notebook stores the chosen
#: hex value so that every surface can render the same practicum colour.
PRACTICUM_COLORS = (
    "#8FC7B2",
    "#F2B989",
    "#9CB9E8",
    "#D7A9D4",
    "#E7C96F",
    "#E89B9B",
    "#A8C98A",
    "#C5B4E3",
)


def now() -> str:
    """UTC timestamp with second precision, used for all audit fields."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def normalize_color(value: str | None, fallback: str = PRACTICUM_COLORS[0]) -> str:
    """Return a validated, lower-case ``#rrggbb`` colour or *fallback*."""
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
        except ValueError:
            pass
        else:
            return text.lower()
    fallback_text = str(fallback or PRACTICUM_COLORS[0]).strip()
    if len(fallback_text) == 7 and fallback_text.startswith("#"):
        try:
            int(fallback_text[1:], 16)
        except ValueError:
            return PRACTICUM_COLORS[0].lower()
        return fallback_text.lower()
    return PRACTICUM_COLORS[0].lower()


class ELNStore:
    """Small, dependency-free repository for practica, days and source notes."""

    def __init__(self, folder: Path | str):
        self.folder = Path(folder).expanduser().resolve()
        self.folder.mkdir(parents=True, exist_ok=True)
        self.media_folder = self.folder / "media"
        self.media_folder.mkdir(exist_ok=True)
        self.db = self.folder / "lab_notebook.sqlite3"
        self._init_schema()

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        """Connection scope that commits on success, rolls back on error and closes."""
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    # Backwards-compatible name for callers that used ``with store.connect()``.
    def connect(self) -> Iterator[sqlite3.Connection]:
        return self.session()

    def _init_schema(self) -> None:
        with self.session() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS practica (
                  id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  field TEXT NOT NULL DEFAULT '',
                  color TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS days (
                  id TEXT PRIMARY KEY,
                  practicum_id TEXT NOT NULL REFERENCES practica(id),
                  date TEXT NOT NULL,
                  title TEXT NOT NULL,
                  supervisor TEXT NOT NULL DEFAULT '',
                  author TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS days_parent ON days(practicum_id, date);
                CREATE TABLE IF NOT EXISTS entries (
                  id TEXT PRIMARY KEY,
                  day_id TEXT NOT NULL REFERENCES days(id),
                  title TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS entries_parent ON entries(day_id, created_at);
                CREATE TABLE IF NOT EXISTS drafts (
                  day_id TEXT PRIMARY KEY REFERENCES days(id),
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS media (
                  id TEXT PRIMARY KEY,
                  entry_id TEXT NOT NULL REFERENCES entries(id),
                  filename TEXT NOT NULL,
                  mime TEXT NOT NULL,
                  stored_name TEXT NOT NULL,
                  sha256 TEXT NOT NULL,
                  bytes INTEGER NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS media_parent ON media(entry_id, created_at);
                CREATE TABLE IF NOT EXISTS protocols (
                  id TEXT PRIMARY KEY,
                  day_id TEXT NOT NULL REFERENCES days(id),
                  style TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  content TEXT NOT NULL,
                  source_ids TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS protocols_parent ON protocols(day_id, created_at);
                CREATE TABLE IF NOT EXISTS todos (
                  id TEXT PRIMARY KEY,
                  text TEXT NOT NULL,
                  due_date TEXT NOT NULL DEFAULT '',
                  done INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL,
                  completed_at TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS todos_order ON todos(done, due_date, created_at);
                """
            )
            practica_columns = {
                row["name"] for row in con.execute("PRAGMA table_info(practica)")
            }
            if "color" not in practica_columns:
                # Databases created before the folder redesign stay readable.
                con.execute(
                    "ALTER TABLE practica ADD COLUMN color TEXT NOT NULL DEFAULT ''"
                )
            existing = con.execute(
                "SELECT id,color FROM practica ORDER BY created_at,id"
            ).fetchall()
            for position, row in enumerate(existing):
                if not str(row["color"] or "").strip():
                    con.execute(
                        "UPDATE practica SET color=? WHERE id=?",
                        (PRACTICUM_COLORS[position % len(PRACTICUM_COLORS)], row["id"]),
                    )
            con.execute("PRAGMA user_version=3")

    @staticmethod
    def _rows(cursor: sqlite3.Cursor) -> list[dict]:
        return [dict(row) for row in cursor.fetchall()]

    # ----------------------------------------------------------------- practica
    def list_practica(self) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                "SELECT * FROM practica ORDER BY created_at DESC, name COLLATE NOCASE"
            ))

    def get_practicum(self, practicum_id: str) -> dict | None:
        with self.session() as con:
            row = con.execute("SELECT * FROM practica WHERE id=?", (practicum_id,)).fetchone()
        return dict(row) if row else None

    def add_practicum(self, name: str, field: str = "", color: str = "") -> str:
        name = name.strip()
        if not name:
            raise ValueError("Practicum name is required")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            trail = con.execute("SELECT COUNT(*) FROM practica").fetchone()[0]
            chosen = normalize_color(
                color, PRACTICUM_COLORS[int(trail) % len(PRACTICUM_COLORS)]
            )
            con.execute(
                """INSERT INTO practica (id,name,field,color,created_at)
                   VALUES (?,?,?,?,?)""",
                (identifier, name, field.strip(), chosen, now()),
            )
        return identifier

    def update_practicum(self, practicum_id: str, name: str, field: str = "") -> None:
        name = name.strip()
        if not name:
            raise ValueError("Practicum name is required")
        with self.session() as con:
            cursor = con.execute(
                "UPDATE practica SET name=?, field=? WHERE id=?",
                (name, field.strip(), practicum_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(practicum_id)

    def set_practicum_color(self, practicum_id: str, color: str) -> None:
        """Persist the folder colour chosen on the dashboard."""
        chosen = normalize_color(color)
        with self.session() as con:
            cursor = con.execute(
                "UPDATE practica SET color=? WHERE id=?", (chosen, practicum_id)
            )
            if cursor.rowcount == 0:
                raise KeyError(practicum_id)

    def delete_practicum(self, practicum_id: str) -> int:
        """Delete a practicum, its days, sources, protocols and media files."""
        with self.session() as con:
            rows = con.execute(
                """SELECT m.stored_name FROM media m
                   JOIN entries e ON e.id=m.entry_id
                   JOIN days d ON d.id=e.day_id
                   WHERE d.practicum_id=?""",
                (practicum_id,),
            ).fetchall()
            con.execute(
                """DELETE FROM protocols WHERE day_id IN
                   (SELECT id FROM days WHERE practicum_id=?)""",
                (practicum_id,),
            )
            con.execute(
                """DELETE FROM drafts WHERE day_id IN
                   (SELECT id FROM days WHERE practicum_id=?)""",
                (practicum_id,),
            )
            con.execute(
                """DELETE FROM media WHERE entry_id IN
                   (SELECT e.id FROM entries e JOIN days d ON d.id=e.day_id
                    WHERE d.practicum_id=?)""",
                (practicum_id,),
            )
            con.execute(
                """DELETE FROM entries WHERE day_id IN
                   (SELECT id FROM days WHERE practicum_id=?)""",
                (practicum_id,),
            )
            cursor = con.execute("DELETE FROM days WHERE practicum_id=?", (practicum_id,))
            con.execute("DELETE FROM practica WHERE id=?", (practicum_id,))
            removed_days = cursor.rowcount
        self._unlink_media([row["stored_name"] for row in rows])
        return removed_days

    # --------------------------------------------------------------------- days
    def list_days(self, practicum_id: str) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                """SELECT * FROM days WHERE practicum_id=?
                   ORDER BY date DESC, created_at DESC""",
                (practicum_id,),
            ))

    def get_day(self, day_id: str) -> dict | None:
        with self.session() as con:
            row = con.execute("SELECT * FROM days WHERE id=?", (day_id,)).fetchone()
        return dict(row) if row else None

    def add_day(self, practicum_id: str, date: str, title: str,
                supervisor: str = "", author: str = "") -> str:
        datetime.strptime(date, "%Y-%m-%d")
        title = title.strip()
        if not title:
            raise ValueError("Experiment-day title is required")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                "INSERT INTO days VALUES (?,?,?,?,?,?,?)",
                (identifier, practicum_id, date, title, supervisor.strip(),
                 author.strip(), now()),
            )
        return identifier

    def update_day(self, day_id: str, *, date: str, title: str,
                   supervisor: str = "", author: str = "") -> None:
        datetime.strptime(date, "%Y-%m-%d")
        title = title.strip()
        if not title:
            raise ValueError("Experiment-day title is required")
        with self.session() as con:
            cursor = con.execute(
                """UPDATE days SET date=?, title=?, supervisor=?, author=?
                   WHERE id=?""",
                (date, title, supervisor.strip(), author.strip(), day_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(day_id)

    def delete_day(self, day_id: str) -> int:
        with self.session() as con:
            rows = con.execute(
                """SELECT m.stored_name FROM media m
                   JOIN entries e ON e.id=m.entry_id WHERE e.day_id=?""",
                (day_id,),
            ).fetchall()
            con.execute("DELETE FROM protocols WHERE day_id=?", (day_id,))
            con.execute("DELETE FROM drafts WHERE day_id=?", (day_id,))
            con.execute(
                """DELETE FROM media WHERE entry_id IN
                   (SELECT id FROM entries WHERE day_id=?)""",
                (day_id,),
            )
            cursor = con.execute("DELETE FROM entries WHERE day_id=?", (day_id,))
            con.execute("DELETE FROM days WHERE id=?", (day_id,))
            removed_entries = cursor.rowcount
        self._unlink_media([row["stored_name"] for row in rows])
        return removed_entries

    # ------------------------------------------------------------------ entries
    def list_entries(self, day_id: str) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                "SELECT * FROM entries WHERE day_id=? ORDER BY created_at,id",
                (day_id,),
            ))

    def get_entry(self, entry_id: str) -> dict | None:
        with self.session() as con:
            row = con.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
        return dict(row) if row else None

    def source_entries(self, day_id: str) -> list[dict]:
        entries = self.list_entries(day_id)
        for entry in entries:
            entry["attachments"] = self.list_media(entry["id"])
        return entries

    def add_entry(self, day_id: str, title: str, kind: str, content: str) -> str:
        if kind not in {"text", "ocr", "transcript"}:
            raise ValueError("Unsupported entry kind")
        if not content.strip():
            raise ValueError("Empty entry")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                "INSERT INTO entries VALUES (?,?,?,?,?,?)",
                (identifier, day_id, title.strip() or kind, kind, content, now()),
            )
        return identifier

    def update_entry(self, entry_id: str, *, title: str, content: str) -> None:
        if not content.strip():
            raise ValueError("Empty entry")
        with self.session() as con:
            cursor = con.execute(
                "UPDATE entries SET title=?, content=? WHERE id=?",
                (title.strip() or "Note", content, entry_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(entry_id)

    def delete_entry(self, entry_id: str) -> None:
        with self.session() as con:
            rows = con.execute(
                "SELECT stored_name FROM media WHERE entry_id=?", (entry_id,)
            ).fetchall()
            con.execute("DELETE FROM media WHERE entry_id=?", (entry_id,))
            con.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        self._unlink_media([row["stored_name"] for row in rows])

    def search_entries(self, query: str, limit: int = 50) -> list[dict]:
        """Case-insensitive search across practicum, day and note text."""
        query = query.strip()
        if not query:
            return []
        escaped = (query.replace("\\", "\\\\")
                   .replace("%", "\\%")
                   .replace("_", "\\_"))
        pattern = f"%{escaped}%"
        with self.session() as con:
            return self._rows(con.execute(
                """SELECT e.*, d.title AS day_title, d.date AS day_date,
                          p.name AS practicum_name, p.id AS practicum_id
                   FROM entries e
                   JOIN days d ON d.id=e.day_id
                   JOIN practica p ON p.id=d.practicum_id
                   WHERE e.content LIKE ? ESCAPE '\\'
                      OR e.title LIKE ? ESCAPE '\\'
                      OR d.title LIKE ? ESCAPE '\\'
                      OR p.name LIKE ? ESCAPE '\\'
                   ORDER BY d.date DESC, e.created_at DESC
                   LIMIT ?""",
                (pattern, pattern, pattern, pattern, int(limit)),
            ))

    def day_summary(self, day_id: str) -> dict:
        with self.session() as con:
            entries = con.execute(
                "SELECT COUNT(*) AS count FROM entries WHERE day_id=?", (day_id,)
            ).fetchone()["count"]
            attachments = con.execute(
                """SELECT COUNT(*) AS count FROM media m
                   JOIN entries e ON e.id=m.entry_id WHERE e.day_id=?""",
                (day_id,),
            ).fetchone()["count"]
            protocols = con.execute(
                "SELECT COUNT(*) AS count FROM protocols WHERE day_id=?", (day_id,)
            ).fetchone()["count"]
        return {"entries": entries, "attachments": attachments, "protocols": protocols}

    # ------------------------------------------------------------------- drafts
    def get_draft(self, day_id: str) -> dict:
        with self.session() as con:
            row = con.execute("SELECT * FROM drafts WHERE day_id=?", (day_id,)).fetchone()
        return dict(row) if row else {"title": "", "content": "", "updated_at": ""}

    def save_draft(self, day_id: str, title: str, content: str) -> None:
        with self.session() as con:
            con.execute(
                """INSERT INTO drafts VALUES (?,?,?,?)
                   ON CONFLICT(day_id) DO UPDATE SET title=excluded.title,
                   content=excluded.content, updated_at=excluded.updated_at""",
                (day_id, title, content, now()),
            )

    def clear_draft(self, day_id: str) -> None:
        with self.session() as con:
            con.execute("DELETE FROM drafts WHERE day_id=?", (day_id,))

    # -------------------------------------------------------------------- media
    def add_media(self, entry_id: str, filename: str, data: bytes) -> str:
        original = Path(filename).name
        suffix = Path(original).suffix.lower()
        if not original:
            raise ValueError("Attachment name is required")
        if suffix in BLOCKED_EXTENSIONS:
            raise ValueError("Unsupported attachment type")
        if not data or len(data) > MAX_MEDIA_BYTES:
            raise ValueError("Attachment must be between 1 byte and 50 MB")
        identifier = str(uuid.uuid4())
        stored_name = identifier + suffix
        path = self.media_folder / stored_name
        digest = hashlib.sha256(data).hexdigest()
        path.write_bytes(data)
        try:
            with self.session() as con:
                con.execute(
                    "INSERT INTO media VALUES (?,?,?,?,?,?,?,?)",
                    (identifier, entry_id, original,
                     mimetypes.guess_type(original)[0] or "application/octet-stream",
                     stored_name, digest, len(data), now()),
                )
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return identifier

    def list_media(self, entry_id: str) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                "SELECT * FROM media WHERE entry_id=? ORDER BY created_at,id",
                (entry_id,),
            ))

    def read_media(self, media_id: str) -> tuple[dict, bytes]:
        with self.session() as con:
            row = con.execute("SELECT * FROM media WHERE id=?", (media_id,)).fetchone()
        if not row:
            raise KeyError(media_id)
        item = dict(row)
        path = self.media_folder / item["stored_name"]
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Attachment checksum mismatch")
        return item, data

    def delete_media(self, media_id: str) -> None:
        with self.session() as con:
            row = con.execute(
                "SELECT stored_name FROM media WHERE id=?", (media_id,)
            ).fetchone()
            con.execute("DELETE FROM media WHERE id=?", (media_id,))
        if row:
            self._unlink_media([row["stored_name"]])

    def verify_media(self) -> list[str]:
        """Return stored names whose bytes no longer match the recorded SHA-256."""
        with self.session() as con:
            rows = self._rows(con.execute("SELECT stored_name,sha256 FROM media"))
        broken = []
        for row in rows:
            path = self.media_folder / row["stored_name"]
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                broken.append(row["stored_name"])
        return broken

    def _unlink_media(self, names: list[str]) -> None:
        for name in names:
            (self.media_folder / name).unlink(missing_ok=True)

    # ------------------------------------------------------------------- todos
    def list_todos(self, include_done: bool = True) -> list[dict]:
        """Open lab tasks first; completed tasks stay visible until deleted."""
        clause = "" if include_done else "WHERE done=0"
        with self.session() as con:
            return self._rows(con.execute(
                f"""SELECT * FROM todos {clause}
                    ORDER BY done, CASE WHEN due_date='' THEN 1 ELSE 0 END,
                             due_date, created_at, id"""
            ))

    def add_todo(self, text: str, due_date: str = "") -> str:
        text = text.strip()
        if not text:
            raise ValueError("To-do text is required")
        if due_date:
            datetime.strptime(due_date, "%Y-%m-%d")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                """INSERT INTO todos (id,text,due_date,done,created_at,completed_at)
                   VALUES (?,?,?,0,?,?)""",
                (identifier, text, due_date, now(), ""),
            )
        return identifier

    def set_todo_done(self, todo_id: str, done: bool) -> None:
        with self.session() as con:
            cursor = con.execute(
                "UPDATE todos SET done=?, completed_at=? WHERE id=?",
                (1 if done else 0, now() if done else "", todo_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(todo_id)

    def delete_todo(self, todo_id: str) -> None:
        with self.session() as con:
            con.execute("DELETE FROM todos WHERE id=?", (todo_id,))

    # ---------------------------------------------------------------- protocols
    def save_protocol(self, day_id: str, style: str, provider: str,
                      content: str, source_ids: list[str]) -> str:
        if style not in {"bullet", "prose", "hybrid"}:
            raise ValueError("Unknown protocol style")
        identifier = str(uuid.uuid4())
        with self.session() as con:
            con.execute(
                "INSERT INTO protocols VALUES (?,?,?,?,?,?,?)",
                (identifier, day_id, style, provider, content,
                 json.dumps(source_ids, ensure_ascii=False), now()),
            )
        return identifier

    def list_protocols(self, day_id: str) -> list[dict]:
        with self.session() as con:
            return self._rows(con.execute(
                "SELECT * FROM protocols WHERE day_id=? ORDER BY created_at DESC,id",
                (day_id,),
            ))

    def get_protocol(self, protocol_id: str) -> dict | None:
        with self.session() as con:
            row = con.execute("SELECT * FROM protocols WHERE id=?", (protocol_id,)).fetchone()
        return dict(row) if row else None

    def delete_protocol(self, protocol_id: str) -> None:
        with self.session() as con:
            con.execute("DELETE FROM protocols WHERE id=?", (protocol_id,))
