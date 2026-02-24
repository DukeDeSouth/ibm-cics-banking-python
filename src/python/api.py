"""FastAPI routes — replace BMS SEND/RECEIVE MAP + EXEC CICS LINK.

9 BMS screens → 15 REST endpoints under /api/.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
import sqlite3

from .config import SORT_CODE, COMPANY_NAME
from .database import get_connection, DB_PATH
from .models import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    AccountCreate, AccountUpdate, AccountResponse,
    TransferRequest, DebitCreditRequest,
    TransactionResponse, ApiResult,
)
from . import services
from .services import ServiceError

router = APIRouter(prefix="/api")


def _get_db():
    conn = get_connection(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ok(data=None, message: str = "") -> dict:
    return {"success": True, "message": message, "data": data}


def _fail(message: str) -> dict:
    return {"success": False, "message": message, "data": None}


# ── Info (GETCOMPY + GETSCODE) ────────────────────────────

@router.get("/info")
def get_info():
    return _ok({"company": COMPANY_NAME, "sortcode": SORT_CODE})


# ── Customers ─────────────────────────────────────────────

@router.get("/customers")
def list_customers(conn: sqlite3.Connection = Depends(_get_db)):
    from .dao import CustomerDAO
    rows = CustomerDAO.list_all(conn, SORT_CODE)
    return _ok(rows)


@router.get("/customers/{number}")
def get_customer(number: int, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        cust = services.get_customer(conn, SORT_CODE, number)
        return _ok(cust)
    except ServiceError as e:
        return _fail(str(e))


@router.post("/customers")
def create_customer(req: CustomerCreate, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        cust = services.create_customer(conn, req.name, req.address, req.date_of_birth)
        return _ok(cust, "Customer created")
    except ServiceError as e:
        return _fail(str(e))


@router.put("/customers/{number}")
def update_customer(number: int, req: CustomerUpdate, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        cust = services.update_customer(conn, number, req.name, req.address)
        return _ok(cust, "Customer updated")
    except ServiceError as e:
        return _fail(str(e))


@router.delete("/customers/{number}")
def delete_customer(number: int, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        services.delete_customer(conn, number)
        return _ok(message="Customer deleted")
    except ServiceError as e:
        return _fail(str(e))


# ── Accounts ──────────────────────────────────────────────

@router.get("/customers/{number}/accounts")
def get_customer_accounts(number: int, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        accs = services.get_accounts_by_customer(conn, SORT_CODE, number)
        return _ok(accs)
    except ServiceError as e:
        return _fail(str(e))


@router.get("/accounts/{number}")
def get_account(number: int, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        acc = services.get_account(conn, SORT_CODE, number)
        return _ok(acc)
    except ServiceError as e:
        return _fail(str(e))


@router.post("/accounts")
def create_account(req: AccountCreate, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        acc = services.create_account(
            conn, req.customer_number, req.account_type,
            req.interest_rate, req.overdraft_limit,
        )
        return _ok(acc, "Account created")
    except ServiceError as e:
        return _fail(str(e))


@router.put("/accounts/{number}")
def update_account(number: int, req: AccountUpdate, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        acc = services.update_account(
            conn, number, req.account_type, req.interest_rate, req.overdraft_limit,
        )
        return _ok(acc, "Account updated")
    except ServiceError as e:
        return _fail(str(e))


@router.delete("/accounts/{number}")
def delete_account(number: int, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        services.delete_account(conn, number)
        return _ok(message="Account deleted")
    except ServiceError as e:
        return _fail(str(e))


# ── Financial ─────────────────────────────────────────────

@router.post("/transfers")
def transfer(req: TransferRequest, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        result = services.transfer_funds(conn, req.from_account, req.to_account, req.amount)
        return _ok(result, "Transfer completed")
    except ServiceError as e:
        return _fail(str(e))


@router.post("/accounts/{number}/debit-credit")
def debit_credit(number: int, req: DebitCreditRequest, conn: sqlite3.Connection = Depends(_get_db)):
    try:
        result = services.debit_credit(conn, number, req.amount, req.is_debit)
        return _ok(result, "Debit applied" if req.is_debit else "Credit applied")
    except ServiceError as e:
        return _fail(str(e))


# ── Transactions ──────────────────────────────────────────

@router.get("/transactions/{account_number}")
def get_transactions(account_number: int, conn: sqlite3.Connection = Depends(_get_db)):
    from .dao import TransactionDAO
    rows = TransactionDAO.get_by_account(conn, SORT_CODE, account_number)
    return _ok(rows)


# ── Seed ──────────────────────────────────────────────────

@router.post("/seed")
def run_seed(conn: sqlite3.Connection = Depends(_get_db)):
    from .seed import generate_test_data
    try:
        stats = generate_test_data(conn, SORT_CODE)
        return _ok(stats, "Test data generated")
    except Exception as e:
        return _fail(str(e))
