import pytest

from figma_core.errors import CoreError
from figma_core.iterations import next_correction, record_correction


def test_fifth_correction_is_blocked():
    assert next_correction(0) == 1
    assert next_correction(3) == 4
    with pytest.raises(CoreError, match="four"):
        next_correction(4)


def test_correction_count_survives_resume(tmp_path):
    for count in range(1, 5):
        assert record_correction(tmp_path / "iterations.sqlite", "node", "a" * 64, "b" * 64) == count
    with pytest.raises(CoreError, match="four"):
        record_correction(tmp_path / "iterations.sqlite", "node", "a" * 64, "b" * 64)
    assert record_correction(tmp_path / "iterations.sqlite", "node", "c" * 64, "b" * 64) == 1
    assert record_correction(tmp_path / "iterations.sqlite", "node", "a" * 64, "d" * 64) == 1
