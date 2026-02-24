"""Test data generator — replaces BANKDATA.cbl (1463 lines).

Arrays of names, surnames, towns, streets extracted verbatim from COBOL.
"""

from __future__ import annotations
import random
import sqlite3
from datetime import date, timedelta

from .dao import CustomerDAO, AccountDAO, TransactionDAO
from .config import VALID_ACCOUNT_TYPES, DEFAULT_RATES

FORENAMES = [
    "Michael", "Will", "Geoff", "Chris", "Dave", "Luke", "Adam", "Giuseppe",
    "James", "Jon", "Andy", "Lou", "Robert", "Sam", "Frederick", "Buford",
    "William", "Howard", "Anthony", "Bruce", "Peter", "Stephen", "Donald",
    "Dennis", "Harold", "Amy", "Belinda", "Charlotte", "Donna", "Felicia",
    "Gretchen", "Henrietta", "Imogen", "Josephine", "Kimberley", "Lucy",
    "Monica", "Natalie", "Ophelia", "Patricia", "Querida", "Rachel",
    "Samantha", "Tanya", "Ulrika", "Virginia", "Wendy", "Xaviera",
    "Yvonne", "Zsa Zsa",
]

SURNAMES = [
    "Jones", "Davidson", "Baker", "Smith", "Taylor", "Evans", "Roberts",
    "Wright", "Walker", "Green", "Price", "Downton", "Gatting", "Robinson",
    "Justice", "Tell", "Stark", "Strange", "Parker", "Blake", "Jackson",
    "Groves", "Palmer", "Lloyd", "Hughes", "Briggs", "Higins", "Goodwin",
    "Valmont", "Brown", "Hopkins", "Bonney", "Jenkins", "Lloyd", "Wilmore",
    "Franklin", "Renton", "Seward", "Morris", "Johnson", "Brennan",
    "Thomson", "Barker", "Corbett", "Weber", "Leigh", "Croft", "Walken",
    "Dubois", "Stephens",
]

TOWNS = [
    "Norwich", "Acle", "Aylsham", "Wymondham", "Attleborough", "Cromer",
    "Cambridge", "Peterborough", "Weobley", "Wembley", "Hereford",
    "Ross-on-Wye", "Hay-on-Wye", "Nottingham", "Northampton", "Nuneaton",
    "Oxford", "Oswestry", "Ormskirk", "Royston", "Chilcomb", "Winchester",
    "Wrexham", "Crewe", "Plymouth", "Portsmouth", "Forfar", "Fife",
    "Aberdeen", "Glasgow", "Birmingham", "Bolton", "Whitby", "Manchester",
    "Chester", "Leicester", "Lowestoft", "Ipswich", "Colchester", "Dover",
    "Brighton", "Salisbury", "Bristol", "Bath", "Gloucester", "Cheltenham",
    "Durham", "Carlisle", "York", "Exeter",
]

TREES = [
    "Acacia", "Birch", "Cypress", "Douglas", "Elm", "Fir", "Gorse",
    "Holly", "Ironwood", "Joshua", "Kapok", "Laburnam", "Maple", "Nutmeg",
    "Oak", "Pine", "Quercine", "Rowan", "Sycamore", "Thorn", "Ulmus",
    "Viburnum", "Willow", "Xylophone", "Yew", "Zebratree",
]

ROADS = [
    "Avenue", "Boulevard", "Close", "Crescent", "Drive", "Escalade",
    "Frontage", "Lane", "Mews", "Rise", "Court", "Opening", "Loke",
    "Square", "Houses", "Gate", "Street", "Grove", "March",
]

TITLES_WEIGHTED = [
    "Mr", "Mr", "Mr", "Mr", "Mr",
    "Mrs", "Mrs", "Mrs", "Mrs", "Mrs",
    "Miss", "Miss", "Miss", "Miss",
    "Ms", "Ms", "Ms", "Ms", "Ms", "Ms",
    "Dr", "Dr", "Dr", "Dr", "Dr",
    "Drs",
    "Professor", "Professor", "Professor",
    "Lord",
    "Sir", "Sir",
    "Lady", "Lady",
]


def _random_dob() -> str:
    start = date(1940, 1, 1)
    end = date(2000, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()


def _random_address() -> str:
    num = random.randint(1, 99)
    tree = random.choice(TREES)
    road = random.choice(ROADS)
    town = random.choice(TOWNS)
    return f"{num} {tree} {road}, {town}"


def generate_test_data(
    conn: sqlite3.Connection,
    sortcode: str,
    num_customers: int = 10,
    accounts_per_customer: int = 2,
) -> dict:
    """Generate random customers and accounts, mimicking BANKDATA.cbl."""
    created_customers = 0
    created_accounts = 0

    for _ in range(num_customers):
        title = random.choice(TITLES_WEIGHTED)
        forename = random.choice(FORENAMES)
        surname = random.choice(SURNAMES)
        name = f"{title} {forename} {surname}"
        address = _random_address()
        dob = _random_dob()
        score = random.randint(1, 999)
        today = date.today().isoformat()

        cust_num = CustomerDAO.next_number(conn, sortcode)
        CustomerDAO.create(conn, sortcode, cust_num, name, address, dob, score, today)
        created_customers += 1

        for _ in range(accounts_per_customer):
            acc_type = random.choice(VALID_ACCOUNT_TYPES)
            defaults = DEFAULT_RATES.get(acc_type, {})
            interest = defaults.get("interest", 0)
            overdraft = defaults.get("overdraft", 0)
            acc_num = AccountDAO.next_number(conn, sortcode)
            AccountDAO.create(
                conn, sortcode, acc_num, cust_num,
                acc_type, interest, today, overdraft,
            )
            initial_balance = random.randint(0, 1000000)
            AccountDAO.update_balance(conn, sortcode, acc_num, initial_balance, initial_balance)
            created_accounts += 1

    return {"customers": created_customers, "accounts": created_accounts}
