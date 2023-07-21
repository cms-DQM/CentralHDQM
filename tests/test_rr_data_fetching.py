import os
import sys

sys.path.append(os.path.dirname(os.path.realpath("./backend")))

from backend.rr_extractor import get_rr_run, is_significant
from test_data import RUN_REGISTRY_RUN_355555_DATA, RUN_REGISTRY_RUN_355556_DATA


def test_get_rr_run():
    """
    Test fetching data from RR.
    Needs CLIENT_ID and CLIENT_SECRET to be in .env
    """
    result = get_rr_run(355555)
    assert result == {"rr_run_class": "Cosmics22", "rr_significant": True}


def test_is_significant_true():
    """
    Test logic for is_significant.
    """
    assert is_significant(
        RUN_REGISTRY_RUN_355555_DATA,
        RUN_REGISTRY_RUN_355555_DATA["rr_attributes"]["class"],
    )

    assert not is_significant(
        RUN_REGISTRY_RUN_355556_DATA,
        RUN_REGISTRY_RUN_355556_DATA["rr_attributes"]["class"],
    )
