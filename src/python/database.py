"""SQLite schema and connection management.

Replaces: DB2 (ACCDB2.cpy, PROCDB2.cpy, CONTDB2.cpy) + VSAM (CUSTOMER file).
All money stored as INTEGER cents. Interest as INTEGER hundredths.
"""

import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    sortcode    TEXT    NOT NULL DEFAULT '987654',
    number      INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    address     TEXT    NOT NULL DEFAULT '',
    date_of_birth TEXT,
    credit_score  INTEGER DEFAULT 0,
    cs_review_date TEXT,
    PRIMARY KEY (sortcode, number)
);

CREATE TABLE IF NOT EXISTS accounts (
    sortcode          TEXT    NOT NULL DEFAULT '987654',
    number            INTEGER NOT NULL,
    customer_number   INTEGER NOT NULL,
    account_type      TEXT    NOT NULL DEFAULT 'CURRENT',
    interest_rate     INTEGER DEFAULT 0,
    opened            TEXT,
    overdraft_limit   INTEGER DEFAULT 0,
    last_statement    TEXT,
    next_statement    TEXT,
    available_balance INTEGER DEFAULT 0,
    actual_balance    INTEGER DEFAULT 0,
    PRIMARY KEY (sortcode, number),
    FOREIGN KEY (sortcode, customer_number)
        REFERENCES customers(sortcode, number)
);

CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sortcode        TEXT    NOT NULL,
    account_number  INTEGER NOT NULL,
    trans_date      TEXT    NOT NULL,
    trans_time      TEXT    NOT NULL,
    trans_type      TEXT    NOT NULL,
    description     TEXT    DEFAULT '',
    amount          INTEGER DEFAULT 0
);
"""


def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db(db_path: str = DB_PATH):
    """Context manager: auto-commit on success, rollback on error."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
