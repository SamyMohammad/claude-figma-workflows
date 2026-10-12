import pytest

from figma_core.dispatch import dispatch, parse_figma_url, select_platform
from figma_core.errors import CoreError


def test_ambiguous_platform_requires_selection():
    with pytest.raises(CoreError, match="target"):
        select_platform(["flutter", "compose"], None)


def test_flutter_android_host_does_not_imply_compose():
    assert select_platform(["flutter"], None) == "flutter"


def test_missing_adapter_has_no_success_fallback():
    with pytest.raises(CoreError, match="unavailable"):
        dispatch("flutter", [])


def test_dispatch_exact_installed_id():
    assert dispatch("compose", ["figma-compose:build"]) == "figma-compose:build"


def test_explicit_target_must_match_evidence():
    with pytest.raises(CoreError, match="target"):
        select_platform(["flutter"], "compose")


def test_figma_url_normalizes_node():
    assert parse_figma_url("https://www.figma.com/design/AbC123/Page?node-id=1-22") == ("AbC123", "1:22")


@pytest.mark.parametrize("url", ["http://figma.com/design/abc/x", "https://evilfigma.com/design/abc/x",
                                      "https://figma.com/board/abc/x", "https://figma.com/design/abc/x?node-id=bad",
                                      "https://figma.com:bad/design/abc/x"])
def test_invalid_figma_url(url):
    with pytest.raises(CoreError, match="Figma"):
        parse_figma_url(url)
