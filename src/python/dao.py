"""Data Access Objects — replace EXEC SQL and VSAM READ/WRITE.

CustomerDAO  ← INQCUST, CRECUST, UPDCUST, DELCUS (VSAM)
AccountDAO   ← INQACC, INQACCCU, CREACC, UPDACC, DELACC (DB2)
TransactionDAO ← PROCTRAN INSERT (DB2)
"""

from __future__ import annotations
import sqlite3
from .config import MAX_ACCOUNTS_PER_QUERY


class CustomerDAO:

    @staticmethod
    def get(conn: sqlite3.Connection, sortcode: str, number: int) -> dict | None:
        row = conn.execute(
            "SELECT * FROM customers WHERE sortcode=? AND number=?",
            (sortcode, number),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_random(conn: sqlite3.Connection, sortcode: str) -> dict | None:
        row = conn.execute(
            "SELECT * FROM customers WHERE sortcode=? ORDER BY RANDOM() LIMIT 1",
            (sortcode,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_last(conn: sqlite3.Connection, sortcode: str) -> dict | None:
        row = conn.execute(
            "SELECT * FROM customers WHERE sortcode=? ORDER BY number DESC LIMIT 1",
            (sortcode,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        sortcode: str,
        number: int,
        name: str,
        address: str,
        date_of_birth: str,
        credit_score: int,
        cs_review_date: str,
    ) -> None:
        conn.execute(
            """INSERT INTO customers
               (sortcode, number, name, address, date_of_birth, credit_score, cs_review_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sortcode, number, name, address, date_of_birth, credit_score, cs_review_date),
        )

    @staticmethod
    def update(
        conn: sqlite3.Connection,
        sortcode: str,
        number: int,
        name: str | None = None,
        address: str | None = None,
    ) -> bool:
        sets, params = [], []
        if name is not None:
            sets.append("name=?")
            params.append(name)
        if address is not None:
            sets.append("address=?")
            params.append(address)
        if not sets:
            return False
        params.extend([sortcode, number])
        cur = conn.execute(
            f"UPDATE customers SET {', '.join(sets)} WHERE sortcode=? AND number=?",
            params,
        )
        return cur.rowcount > 0

    @staticmethod
    def delete(conn: sqlite3.Connection, sortcode: str, number: int) -> bool:
        cur = conn.execute(
            "DELETE FROM customers WHERE sortcode=? AND number=?",
            (sortcode, number),
        )
        return cur.rowcount > 0

    @staticmethod
    def next_number(conn: sqlite3.Connection, sortcode: str) -> int:
        row = conn.execute(
            "SELECT COALESCE(MAX(number), 0) + 1 AS next_num FROM customers WHERE sortcode=?",
            (sortcode,),
        ).fetchone()
        return row["next_num"]

    @staticmethod
    def count(conn: sqlite3.Connection, sortcode: str) -> int:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM customers WHERE sortcode=?",
            (sortcode,),
        ).fetchone()
        return row["cnt"]

    @staticmethod
    def list_all(conn: sqlite3.Connection, sortcode: str, limit: int = 100) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM customers WHERE sortcode=? ORDER BY number LIMIT ?",
            (sortcode, limit),
        ).fetchall()
        return [dict(r) for r in rows]


class AccountDAO:

    @staticmethod
    def get(conn: sqlite3.Connection, sortcode: str, number: int) -> dict | None:
        row = conn.execute(
            "SELECT * FROM accounts WHERE sortcode=? AND number=?",
            (sortcode, number),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_last(conn: sqlite3.Connection, sortcode: str) -> dict | None:
        row = conn.execute(
            "SELECT * FROM accounts WHERE sortcode=? ORDER BY number DESC LIMIT 1",
            (sortcode,),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_customer(
        conn: sqlite3.Connection,
        sortcode: str,
        customer_number: int,
        limit: int = MAX_ACCOUNTS_PER_QUERY,
    ) -> list[dict]:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE sortcode=? AND customer_number=? ORDER BY number LIMIT ?",
            (sortcode, customer_number, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        sortcode: str,
        number: int,
        customer_number: int,
        account_type: str,
        interest_rate: int,
        opened: str,
        overdraft_limit: int,
    ) -> None:
        conn.execute(
            """INSERT INTO accounts
               (sortcode, number, customer_number, account_type, interest_rate,
                opened, overdraft_limit, available_balance, actual_balance)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)""",
            (sortcode, number, customer_number, account_type, interest_rate,
             opened, overdraft_limit),
        )

    @staticmethod
    def update(
        conn: sqlite3.Connection,
        sortcode: str,
        number: int,
        account_type: str | None = None,
        interest_rate: int | None = None,
        overdraft_limit: int | None = None,
    ) -> bool:
        sets, params = [], []
        if account_type is not None:
            sets.append("account_type=?")
            params.append(account_type)
        if interest_rate is not None:
            sets.append("interest_rate=?")
            params.append(interest_rate)
        if overdraft_limit is not None:
            sets.append("overdraft_limit=?")
            params.append(overdraft_limit)
        if not sets:
            return False
        params.extend([sortcode, number])
        cur = conn.execute(
            f"UPDATE accounts SET {', '.join(sets)} WHERE sortcode=? AND number=?",
            params,
        )
        return cur.rowcount > 0

    @staticmethod
    def update_balance(
        conn: sqlite3.Connection,
        sortcode: str,
        number: int,
        available_balance: int,
        actual_balance: int,
    ) -> bool:
        cur = conn.execute(
            "UPDATE accounts SET available_balance=?, actual_balance=? WHERE sortcode=? AND number=?",
            (available_balance, actual_balance, sortcode, number),
        )
        return cur.rowcount > 0

    @staticmethod
    def delete(conn: sqlite3.Connection, sortcode: str, number: int) -> bool:
        cur = conn.execute(
            "DELETE FROM accounts WHERE sortcode=? AND number=?",
            (sortcode, number),
        )
        return cur.rowcount > 0

    @staticmethod
    def next_number(conn: sqlite3.Connection, sortcode: str) -> int:
        row = conn.execute(
            "SELECT COALESCE(MAX(number), 0) + 1 AS next_num FROM accounts WHERE sortcode=?",
            (sortcode,),
        ).fetchone()
        return row["next_num"]

    @staticmethod
    def count(conn: sqlite3.Connection, sortcode: str) -> int:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM accounts WHERE sortcode=?",
            (sortcode,),
        ).fetchone()
        return row["cnt"]


class TransactionDAO:

    @staticmethod
    def create(
        conn: sqlite3.Connection,
        sortcode: str,
        account_number: int,
        trans_date: str,
        trans_time: str,
        trans_type: str,
        description: str,
        amount: int,
    ) -> None:
        conn.execute(
            """INSERT INTO transactions
               (sortcode, account_number, trans_date, trans_time, trans_type, description, amount)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sortcode, account_number, trans_date, trans_time, trans_type, description, amount),
        )

    @staticmethod
    def get_by_account(
        conn: sqlite3.Connection,
        sortcode: str,
        account_number: int,
        limit: int = 50,
    ) -> list[dict]:
        rows = conn.execute(
            """SELECT * FROM transactions
               WHERE sortcode=? AND account_number=?
               ORDER BY id DESC LIMIT ?""",
            (sortcode, account_number, limit),
        ).fetchall()
        return [dict(r) for r in rows]
