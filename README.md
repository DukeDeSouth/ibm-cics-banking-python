# ibm-cics-banking-python

IBM's [cics-banking-sample-application-cbsa](https://github.com/cicsdev/cics-banking-sample-application-cbsa) re-architectured from COBOL/CICS/DB2 to Python/FastAPI/SQLite.

**29 COBOL programs** (27,300 lines) across three layers — BMS terminal screens, CICS middleware, DB2/VSAM storage — replaced by **~1,300 lines of Python** with a web UI.

## What changed

| COBOL | Python |
|-------|--------|
| 9 BMS screens (3270 terminal) | Single-page web app (`static/index.html`) |
| EXEC CICS LINK / COMMAREA | FastAPI routes + Pydantic models |
| DB2 + VSAM | SQLite (all money stored as INTEGER cents) |
| CRDTAGY1-5 (async CICS tasks) | ThreadPoolExecutor with 5 workers |
| BANKDATA.cbl (1,463 lines of test data) | `seed.py` with arrays extracted from COBOL |

## Run

```bash
pip install -r requirements.txt
python -m uvicorn src.python.main:app --port 8000
# Open http://localhost:8000
```

Click **Generate Test Data** on the home page to create 10 customers with 20 accounts.

## Test

```bash
python -m pytest tests/ -v
```

19 tests covering: customer CRUD, account CRUD, debit/credit, transfers, insufficient funds, MORTGAGE/LOAN debit restrictions, cascade delete, title validation.

## Structure

```
src/cobol/           ← Original IBM COBOL programs (29 files)
copybooks/           ← COBOL copybooks (37 files)
src/python/
  config.py          ← Constants from copybooks (sortcode, valid titles, account types)
  models.py          ← Pydantic models replacing DFHCOMMAREA
  database.py        ← SQLite schema replacing DB2 + VSAM
  dao.py             ← Data access replacing EXEC SQL / READ FILE
  credit.py          ← Mock credit check replacing CRDTAGY1-5
  services.py        ← 11 functions = 11 COBOL programs
  api.py             ← 15 REST endpoints replacing EXEC CICS LINK
  main.py            ← FastAPI entry point
  seed.py            ← Test data generator from BANKDATA.cbl
static/index.html    ← Web UI replacing BMS screens
tests/               ← pytest
```

## COBOL program → Python function mapping

| COBOL Program | Python function | What it does |
|---------------|-----------------|--------------|
| INQCUST.cbl | `get_customer()` | Lookup customer by number |
| INQACC.cbl | `get_account()` | Lookup account by number |
| INQACCCU.cbl | `get_accounts_by_customer()` | List accounts for a customer (max 20) |
| CRECUST.cbl | `create_customer()` | Create customer with credit check |
| CREACC.cbl | `create_account()` | Create account with default rates |
| UPDCUST.cbl | `update_customer()` | Update customer name/address |
| UPDACC.cbl | `update_account()` | Update account type/rates |
| DELACC.cbl | `delete_account()` | Delete single account |
| DELCUS.cbl | `delete_customer()` | Cascade delete: accounts then customer |
| XFRFUN.cbl | `transfer_funds()` | Transfer between accounts (no overdraft check — matches COBOL) |
| DBCRFUN.cbl | `debit_credit()` | Debit or credit an account |

## Key design decisions

- **Money as integers.** All balances stored as cents (`$12.34` = `1234`). Interest rates as hundredths (`2.50%` = `250`). Avoids floating-point issues, matches COBOL `PIC S9(10)V99 COMP-3` precision.
- **No overdraft check on transfers.** The original XFRFUN.cbl doesn't check — neither do we.
- **MORTGAGE/LOAN can't be debited.** Matches DBCRFUN.cbl validation (fail code '4').
- **Title validation.** Only these titles are accepted: Mr, Mrs, Miss, Ms, Dr, Drs, Professor, Lord, Sir, Lady, and empty string. Extracted from CRECUST.cbl EVALUATE block.

## License

COBOL source: [Eclipse Public License 2.0](https://www.eclipse.org/legal/epl-2.0/) (IBM).
Python translation: same license.
