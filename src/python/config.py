"""Constants extracted from COBOL copybooks and BANKDATA.cbl."""

SORT_CODE = "987654"
COMPANY_NAME = "CICS Bank Sample Application"
DB_PATH = "banking.db"
MAX_ACCOUNTS_PER_QUERY = 20

VALID_TITLES = [
    "Mr", "Mrs", "Miss", "Ms", "Dr", "Drs",
    "Professor", "Lord", "Sir", "Lady", "",
]

VALID_ACCOUNT_TYPES = ["CURRENT", "SAVING", "LOAN", "MORTGAGE", "ISA"]

# Interest in hundredths (250 = 2.50%), overdraft in cents
DEFAULT_RATES = {
    "ISA":      {"interest": 250, "overdraft": 0},
    "SAVING":   {"interest": 150, "overdraft": 0},
    "CURRENT":  {"interest": 0,   "overdraft": 0},
    "LOAN":     {"interest": 750, "overdraft": 0},
    "MORTGAGE": {"interest": 450, "overdraft": 0},
}
