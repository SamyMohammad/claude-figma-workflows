from figma_core.errors import CoreError


def test_error_keeps_machine_code_and_safe_message():
    error = CoreError("FONT_MISSING", "Required font is unavailable")
    assert error.code == "FONT_MISSING"
    assert str(error) == "Required font is unavailable"
