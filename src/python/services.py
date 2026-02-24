"""Business logic — 11 functions replacing 11 COBOL programs.

Each function maps 1:1 to a COBOL program from the Business+Data layer.
All money in INTEGER cents. All interest in INTEGER hundredths.
"""

from __future__ import annotations
import sqlite3
from datetime import date, datetime

from .config import SORT_CODE, VALID_TITLES, VALID_ACCOUNT_TYPES, DEFAULT_RATES
from .dao import CustomerDAO, AccountDAO, TransactionDAO
from .credit import credit_check


class ServiceError(Exception):
    pass

class CustomerNotFound(ServiceError):
    pass

class AccountNotFound(ServiceError):
    pass

class ValidationError(ServiceError):
    pass

class InsufficientFunds(ServiceError):
    pass


def _audit(
    conn: sqlite3.Connection,
    sortcode: str,
    account_number: int,
    trans_type: str,
    description: str,
    amount: int = 0,
) -> None:
    now = datetime.now()
    TransactionDAO.create(
        conn, sortcode, account_number,
        now.strftime("%Y-%m-%d"), now.strftime("%H%M%S"),
        trans_type, description, amount,
    )


# ── INQCUST.cbl ──────────────────────────────────────────

def get_customer(
    conn: sqlite3.Connection, sortcode: str = SORT_CODE, number: int = 0,
) -> dict:
    if number == 0:
        cust = CustomerDAO.get_random(conn, sortcode)
    elif number >= 9999999999:
        cust = CustomerDAO.get_last(conn, sortcode)
    else:
        cust = CustomerDAO.get(conn, sortcode, number)
    if not cust:
        raise CustomerNotFound(f"Customer {number} not found")
    return cust


# ── INQACC.cbl ───────────────────────────────────────────

def get_account(
    conn: sqlite3.Connection, sortcode: str = SORT_CODE, number: int = 0,
) -> dict:
    if number >= 99999999:
        acc = AccountDAO.get_last(conn, sortcode)
    else:
        acc = AccountDAO.get(conn, sortcode, number)
    if not acc:
        raise AccountNotFound(f"Account {number} not found")
    return acc


# ── INQACCCU.cbl ─────────────────────────────────────────

def get_accounts_by_customer(
    conn: sqlite3.Connection, sortcode: str = SORT_CODE, customer_number: int = 0,
) -> list[dict]:
    cust = CustomerDAO.get(conn, sortcode, customer_number)
    if not cust:
        raise CustomerNotFound(f"Customer {customer_number} not found")
    return AccountDAO.get_by_customer(conn, sortcode, customer_number)


# ── CRECUST.cbl (1497 lines → ~20 lines) ─────────────────

def create_customer(
    conn: sqlite3.Connection,
    name: str,
    address: str = "",
    date_of_birth: str = "",
    sortcode: str = SORT_CODE,
) -> dict:
    title = name.split()[0] if name.strip() else ""
    if title not in VALID_TITLES:
        raise ValidationError(f"Invalid title: '{title}'")

    number = CustomerDAO.next_number(conn, sortcode)
    score = credit_check()
    today = date.today().isoformat()

    CustomerDAO.create(conn, sortcode, number, name, address, date_of_birth, score, today)
    _audit(conn, sortcode, 0, "OCC", f"Create customer {number}")
    return CustomerDAO.get(conn, sortcode, number)


# ── CREACC.cbl (1247 lines → ~20 lines) ──────────────────

def create_account(
    conn: sqlite3.Connection,
    customer_number: int,
    account_type: str = "CURRENT",
    interest_rate: int | None = None,
    overdraft_limit: int | None = None,
    sortcode: str = SORT_CODE,
) -> dict:
    if account_type not in VALID_ACCOUNT_TYPES:
        raise ValidationError(f"Invalid account type: '{account_type}'")

    cust = CustomerDAO.get(conn, sortcode, customer_number)
    if not cust:
        raise CustomerNotFound(f"Customer {customer_number} not found")

    defaults = DEFAULT_RATES.get(account_type, {})
    if interest_rate is None:
        interest_rate = defaults.get("interest", 0)
    if overdraft_limit is None:
        overdraft_limit = defaults.get("overdraft", 0)

    number = AccountDAO.next_number(conn, sortcode)
    today = date.today().isoformat()

    AccountDAO.create(
        conn, sortcode, number, customer_number,
        account_type, interest_rate, today, overdraft_limit,
    )
    _audit(conn, sortcode, number, "OCA", f"Create account for cust {customer_number}")
    return AccountDAO.get(conn, sortcode, number)


# ── UPDCUST.cbl ──────────────────────────────────────────

def update_customer(
    conn: sqlite3.Connection,
    number: int,
    name: str | None = None,
    address: str | None = None,
    sortcode: str = SORT_CODE,
) -> dict:
    cust = CustomerDAO.get(conn, sortcode, number)
    if not cust:
        raise CustomerNotFound(f"Customer {number} not found")

    if name is not None:
        title = name.split()[0] if name.strip() else ""
        if title not in VALID_TITLES:
            raise ValidationError(f"Invalid title: '{title}'")

    CustomerDAO.update(conn, sortcode, number, name, address)
    return CustomerDAO.get(conn, sortcode, number)


# ── UPDACC.cbl ───────────────────────────────────────────

def update_account(
    conn: sqlite3.Connection,
    number: int,
    account_type: str | None = None,
    interest_rate: int | None = None,
    overdraft_limit: int | None = None,
    sortcode: str = SORT_CODE,
) -> dict:
    acc = AccountDAO.get(conn, sortcode, number)
    if not acc:
        raise AccountNotFound(f"Account {number} not found")

    if account_type is not None and account_type not in VALID_ACCOUNT_TYPES:
        raise ValidationError(f"Invalid account type: '{account_type}'")

    AccountDAO.update(conn, sortcode, number, account_type, interest_rate, overdraft_limit)
    return AccountDAO.get(conn, sortcode, number)


# ── DELACC.cbl ───────────────────────────────────────────

def delete_account(
    conn: sqlite3.Connection, number: int, sortcode: str = SORT_CODE,
) -> bool:
    acc = AccountDAO.get(conn, sortcode, number)
    if not acc:
        raise AccountNotFound(f"Account {number} not found")
    AccountDAO.delete(conn, sortcode, number)
    _audit(conn, sortcode, number, "ODA", f"Delete account {number}")
    return True


# ── DELCUS.cbl — cascade delete ──────────────────────────

def delete_customer(
    conn: sqlite3.Connection, number: int, sortcode: str = SORT_CODE,
) -> bool:
    cust = CustomerDAO.get(conn, sortcode, number)
    if not cust:
        raise CustomerNotFound(f"Customer {number} not found")

    accounts = AccountDAO.get_by_customer(conn, sortcode, number)
    for acc in accounts:
        delete_account(conn, acc["number"], sortcode)

    CustomerDAO.delete(conn, sortcode, number)
    _audit(conn, sortcode, 0, "ODC", f"Delete customer {number}")
    return True


# ── XFRFUN.cbl (1924 lines → ~15 lines) ─────────────────

def transfer_funds(
    conn: sqlite3.Connection,
    from_number: int,
    to_number: int,
    amount: int,
    sortcode: str = SORT_CODE,
) -> dict:
    """No overdraft check — matches COBOL XFRFUN behavior."""
    from_acc = AccountDAO.get(conn, sortcode, from_number)
    to_acc = AccountDAO.get(conn, sortcode, to_number)
    if not from_acc:
        raise AccountNotFound(f"From-account {from_number} not found")
    if not to_acc:
        raise AccountNotFound(f"To-account {to_number} not found")

    new_from_avail = from_acc["available_balance"] - amount
    new_from_actual = from_acc["actual_balance"] - amount
    AccountDAO.update_balance(conn, sortcode, from_number, new_from_avail, new_from_actual)

    new_to_avail = to_acc["available_balance"] + amount
    new_to_actual = to_acc["actual_balance"] + amount
    AccountDAO.update_balance(conn, sortcode, to_number, new_to_avail, new_to_actual)

    _audit(conn, sortcode, from_number, "TFR", f"Transfer to {to_number}", amount)
    _audit(conn, sortcode, to_number, "TFR", f"Transfer from {from_number}", amount)

    return {
        "from_balance": new_from_actual,
        "to_balance": new_to_actual,
    }


# ── DBCRFUN.cbl (861 lines → ~15 lines) ─────────────────

def debit_credit(
    conn: sqlite3.Connection,
    number: int,
    amount: int,
    is_debit: bool,
    sortcode: str = SORT_CODE,
) -> dict:
    acc = AccountDAO.get(conn, sortcode, number)
    if not acc:
        raise AccountNotFound(f"Account {number} not found")

    signed = -amount if is_debit else amount

    if is_debit:
        if acc["account_type"] in ("MORTGAGE", "LOAN"):
            raise ValidationError("Cannot debit MORTGAGE/LOAN account")
        if acc["available_balance"] + signed < 0:
            raise InsufficientFunds("Insufficient funds for debit")

    new_avail = acc["available_balance"] + signed
    new_actual = acc["actual_balance"] + signed
    AccountDAO.update_balance(conn, sortcode, number, new_avail, new_actual)

    ttype = "DEB" if is_debit else "CRE"
    _audit(conn, sortcode, number, ttype, f"{'Debit' if is_debit else 'Credit'} {amount}", abs(signed))

    return {"available_balance": new_avail, "actual_balance": new_actual}
