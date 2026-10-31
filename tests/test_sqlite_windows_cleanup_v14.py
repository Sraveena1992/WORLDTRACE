"""Database handles must be closed after commit or rollback on Windows."""
import sqlite3
from worldtrace import storage

def test_sqlite_transaction_closes_handle(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    with storage.connect() as conn:
        conn.execute("SELECT 1").fetchone()
    try:
        conn.execute("SELECT 1")
    except sqlite3.ProgrammingError as exc:
        assert "closed" in str(exc).lower()
    else:
        raise AssertionError("SQLite handle remained open after context exit")
    dbfile=tmp_path/"worldtrace.sqlite3"
    assert dbfile.exists()
    dbfile.unlink()
    assert not dbfile.exists()

def test_sqlite_rollback_also_closes(monkeypatch,tmp_path):
    monkeypatch.setenv("WORLDTRACE_DATA_DIR",str(tmp_path))
    try:
        with storage.connect() as conn:
            conn.execute("SELECT 1")
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass
    try:
        conn.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        pass
    else:
        raise AssertionError("Failed transaction leaked SQLite handle")
