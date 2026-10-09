from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pytest

from figma_core.budget import mark_sent, reserve
from figma_core.errors import CoreError


def _reserve(args):
    db, request_id = args
    return reserve(db, "observed-window", 1, request_id)


def test_two_callers_cannot_spend_one_remaining_call(tmp_path):
    db = tmp_path / "budget.sqlite3"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda n: reserve(db, "observed-window", 1, str(n)), range(2)))
    assert sorted(results) == [False, True]


def test_two_processes_cannot_spend_one_remaining_call(tmp_path):
    db = tmp_path / "budget.sqlite3"
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(_reserve, [(db, "one"), (db, "two")]))
    assert sorted(results) == [False, True]


def test_reservation_is_one_shot(tmp_path):
    db = tmp_path / "budget.sqlite3"
    assert reserve(db, "window", 1, "request")
    assert reserve(db, "window", 1, "request")
    mark_sent(db, "request")
    assert not reserve(db, "window", 1, "request")
    with pytest.raises(CoreError):
        mark_sent(db, "request")
    with pytest.raises(CoreError):
        reserve(db, "other", 1, "request")
