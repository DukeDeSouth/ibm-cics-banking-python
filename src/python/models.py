"""Pydantic models — replace DFHCOMMAREA copybooks.

CUSTOMER.cpy  → CustomerCreate / CustomerResponse
ACCOUNT.cpy   → AccountCreate / AccountResponse
PROCTRAN.cpy  → TransactionResponse
CREACC.cpy, XFRFUN.cpy, PAYDBCR.cpy → request models
"""

from typing import List, Optional, Union
from pydantic import BaseModel


# ── Requests ──────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name: str
    address: str = ""
    date_of_birth: str = ""  # YYYY-MM-DD


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class AccountCreate(BaseModel):
    customer_number: int
    account_type: str = "CURRENT"
    interest_rate: Optional[int] = None   # hundredths: 250 = 2.50%
    overdraft_limit: Optional[int] = None  # cents


class AccountUpdate(BaseModel):
    account_type: Optional[str] = None
    interest_rate: Optional[int] = None
    overdraft_limit: Optional[int] = None


class TransferRequest(BaseModel):
    from_account: int
    to_account: int
    amount: int  # cents, positive


class DebitCreditRequest(BaseModel):
    amount: int  # cents, positive
    is_debit: bool


# ── Responses ─────────────────────────────────────────────

class CustomerResponse(BaseModel):
    sortcode: str
    number: int
    name: str
    address: str
    date_of_birth: Optional[str] = None
    credit_score: int = 0
    cs_review_date: Optional[str] = None


class AccountResponse(BaseModel):
    sortcode: str
    number: int
    customer_number: int
    account_type: str
    interest_rate: int
    opened: Optional[str] = None
    overdraft_limit: int
    last_statement: Optional[str] = None
    next_statement: Optional[str] = None
    available_balance: int  # cents
    actual_balance: int  # cents


class TransactionResponse(BaseModel):
    id: int
    sortcode: str
    account_number: int
    trans_date: str
    trans_time: str
    trans_type: str
    description: str
    amount: int  # cents


class ApiResult(BaseModel):
    success: bool
    message: str = ""
    data: Union[dict, list, None] = None
