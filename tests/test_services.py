"""Tests for banking services — verifies COBOL business logic translation."""

import os
import tempfile
import pytest

from src.python.database import init_db, get_connection
from src.python import services
from src.python.services import (
    CustomerNotFound, AccountNotFound, ValidationError, InsufficientFunds,
)
from src.python.dao import CustomerDAO, AccountDAO


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    conn = get_connection(path)
    yield conn
    conn.close()
    os.unlink(path)


SORTCODE = "987654"


class TestCreateCustomer:

    def test_valid_title(self, db):
        cust = services.create_customer(db, "Mr John Smith", "1 Oak Ave", "1990-01-15")
        db.commit()
        assert cust["name"] == "Mr John Smith"
        assert cust["number"] == 1
        assert 1 <= cust["credit_score"] <= 999

    def test_invalid_title(self, db):
        with pytest.raises(ValidationError, match="Invalid title"):
            services.create_customer(db, "King John", "1 Oak Ave")

    def test_empty_title_allowed(self, db):
        cust = services.create_customer(db, "", "1 Oak Ave")
        db.commit()
        assert cust["number"] == 1

    def test_auto_increment(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        c2 = services.create_customer(db, "Mrs B", "addr")
        db.commit()
        assert c2["number"] == 2


class TestCreateAccount:

    def test_basic(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        acc = services.create_account(db, 1, "CURRENT")
        db.commit()
        assert acc["account_type"] == "CURRENT"
        assert acc["interest_rate"] == 0
        assert acc["available_balance"] == 0

    def test_default_rates(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        acc = services.create_account(db, 1, "ISA")
        db.commit()
        assert acc["interest_rate"] == 250  # 2.50%

    def test_invalid_type(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        with pytest.raises(ValidationError, match="Invalid account type"):
            services.create_account(db, 1, "CHECKING")

    def test_customer_not_found(self, db):
        with pytest.raises(CustomerNotFound):
            services.create_account(db, 999, "CURRENT")


class TestDebitCredit:

    def _setup_account(self, db, balance=50000):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        services.create_account(db, 1, "CURRENT")
        db.commit()
        AccountDAO.update_balance(db, SORTCODE, 1, balance, balance)
        db.commit()

    def test_credit(self, db):
        self._setup_account(db, 0)
        result = services.debit_credit(db, 1, 50000, is_debit=False)
        db.commit()
        assert result["available_balance"] == 50000
        assert result["actual_balance"] == 50000

    def test_debit(self, db):
        self._setup_account(db, 50000)
        result = services.debit_credit(db, 1, 10000, is_debit=True)
        db.commit()
        assert result["available_balance"] == 40000

    def test_insufficient_funds(self, db):
        self._setup_account(db, 5000)
        with pytest.raises(InsufficientFunds):
            services.debit_credit(db, 1, 6000, is_debit=True)

    def test_mortgage_debit_blocked(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        services.create_account(db, 1, "MORTGAGE")
        db.commit()
        AccountDAO.update_balance(db, SORTCODE, 1, 100000, 100000)
        db.commit()
        with pytest.raises(ValidationError, match="MORTGAGE"):
            services.debit_credit(db, 1, 1000, is_debit=True)


class TestTransfer:

    def _setup_two_accounts(self, db, bal1=100000, bal2=50000):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        services.create_account(db, 1, "CURRENT")
        db.commit()
        services.create_account(db, 1, "SAVING")
        db.commit()
        AccountDAO.update_balance(db, SORTCODE, 1, bal1, bal1)
        AccountDAO.update_balance(db, SORTCODE, 2, bal2, bal2)
        db.commit()

    def test_basic_transfer(self, db):
        self._setup_two_accounts(db)
        result = services.transfer_funds(db, 1, 2, 20000)
        db.commit()
        assert result["from_balance"] == 80000
        assert result["to_balance"] == 70000

    def test_no_overdraft_check(self, db):
        """XFRFUN allows negative balance — matches COBOL."""
        self._setup_two_accounts(db, bal1=5000, bal2=0)
        result = services.transfer_funds(db, 1, 2, 10000)
        db.commit()
        assert result["from_balance"] == -5000  # negative allowed!

    def test_account_not_found(self, db):
        self._setup_two_accounts(db)
        with pytest.raises(AccountNotFound):
            services.transfer_funds(db, 1, 999, 1000)


class TestDeleteCustomer:

    def test_cascade_delete(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        services.create_account(db, 1, "CURRENT")
        services.create_account(db, 1, "SAVING")
        db.commit()
        assert len(AccountDAO.get_by_customer(db, SORTCODE, 1)) == 2

        services.delete_customer(db, 1)
        db.commit()

        assert CustomerDAO.get(db, SORTCODE, 1) is None
        assert len(AccountDAO.get_by_customer(db, SORTCODE, 1)) == 0

    def test_not_found(self, db):
        with pytest.raises(CustomerNotFound):
            services.delete_customer(db, 999)


class TestGetCustomer:

    def test_normal(self, db):
        services.create_customer(db, "Mr A", "addr")
        db.commit()
        cust = services.get_customer(db, SORTCODE, 1)
        assert cust["name"] == "Mr A"

    def test_not_found(self, db):
        with pytest.raises(CustomerNotFound):
            services.get_customer(db, SORTCODE, 999)
