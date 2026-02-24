"""Mock credit check — replaces CRDTAGY1-5.cbl.

Original: 5 CICS child transactions, each with random 0-3s delay and score 1-999.
Python: ThreadPoolExecutor with 5 workers, shortened delay.
"""

import random
import time
from concurrent.futures import ThreadPoolExecutor


def single_agency(agency_id: int) -> int:
    time.sleep(random.uniform(0, 0.3))
    return random.randint(1, 999)


def credit_check(num_agencies: int = 5) -> int:
    """Run parallel credit agencies and return average score."""
    with ThreadPoolExecutor(max_workers=num_agencies) as pool:
        futures = [pool.submit(single_agency, i) for i in range(num_agencies)]
        scores = [f.result(timeout=10) for f in futures]
    return sum(scores) // len(scores)
