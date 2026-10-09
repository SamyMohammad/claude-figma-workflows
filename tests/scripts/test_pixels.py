import pytest
from PIL import Image

from figma_core.errors import CoreError
from figma_core.pixels import measure


def policy():
    return {"schemaVersion": 1, "channelTolerance": 0, "maxChangedRatio": 0.02,
            "ignored": [], "critical": []}


def test_transparent_rgb_does_not_change_visible_result():
    reference = Image.new("RGBA", (10, 10), (255, 0, 0, 0))
    actual = Image.new("RGBA", (10, 10), (0, 255, 0, 0))
    assert measure(reference, actual, policy())["changedPixels"] == 0


def test_alpha_only_change_is_visible():
    reference = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    actual = Image.new("RGBA", (1, 1), (0, 0, 0, 255))
    result = measure(reference, actual, policy())
    assert result["changedPixels"] == 1
    assert result["status"] == "failed"
    assert result["diff"].getpixel((0, 0)) != (0, 0, 0)
    assert result["overlay"].getpixel((0, 0))[:3] == (127, 0, 0)


@pytest.mark.parametrize("changed, expected", [(2, "passed"), (3, "failed")])
def test_global_ratio_boundary(changed, expected):
    reference = Image.new("RGBA", (10, 10), "white")
    actual = reference.copy()
    for x in range(changed):
        actual.putpixel((x, 0), (0, 0, 0, 255))
    result = measure(reference, actual, policy())
    assert result["changedRatio"] == changed / 100
    assert result["status"] == expected


def test_channel_tolerance_is_strictly_greater():
    reference = Image.new("RGBA", (2, 1), (0, 0, 0, 255))
    actual = reference.copy()
    actual.putpixel((0, 0), (5, 0, 0, 255))
    actual.putpixel((1, 0), (6, 0, 0, 255))
    config = policy()
    config["channelTolerance"] = 5
    assert measure(reference, actual, config)["changedPixels"] == 1


def test_small_missing_control_fails_critical_region():
    reference = Image.new("RGBA", (100, 100), "white")
    actual = reference.copy()
    actual.putpixel((0, 0), (0, 0, 0, 255))
    config = policy()
    config["critical"] = [{"id": "control", "box": [0, 0, 1, 1], "maxChangedRatio": 0}]
    result = measure(reference, actual, config)
    assert result["status"] == "failed"
    assert result["criticalResults"] == [{"id": "control", "changedPixels": 1,
                                          "eligiblePixels": 1, "changedRatio": 1.0,
                                          "status": "failed"}]


def test_overlapping_ignored_masks_count_once():
    reference = Image.new("RGBA", (10, 10), "white")
    actual = Image.new("RGBA", (10, 10), "black")
    config = policy()
    config["ignored"] = [{"box": [0, 0, 3, 3], "reason": "synthetic area"},
                         {"box": [2, 2, 3, 3], "reason": "another area"}]
    result = measure(reference, actual, config)
    assert (result["eligiblePixels"], result["changedPixels"]) == (83, 83)


def test_empty_eligible_area_is_invalid():
    reference = Image.new("RGBA", (10, 10), "white")
    config = policy()
    config["ignored"] = [{"box": [0, 0, 10, 10], "reason": "synthetic invalid mask"}]
    with pytest.raises(CoreError, match="eligible"):
        measure(reference, reference, config)


def test_critical_region_cannot_overlap_ignored_region():
    reference = Image.new("RGBA", (10, 10), "white")
    config = policy()
    config["ignored"] = [{"box": [0, 0, 2, 2], "reason": "synthetic mask"}]
    config["critical"] = [{"id": "control", "box": [1, 1, 2, 2], "maxChangedRatio": 0}]
    with pytest.raises(CoreError, match="overlap"):
        measure(reference, reference, config)


def test_invalid_policy_and_out_of_bounds_region_are_rejected():
    reference = Image.new("RGBA", (10, 10), "white")
    config = policy()
    del config["channelTolerance"]
    with pytest.raises(CoreError, match="channelTolerance"):
        measure(reference, reference, config)
    config = policy()
    config["critical"] = [{"id": "control", "box": [9, 9, 2, 2], "maxChangedRatio": 0}]
    with pytest.raises(CoreError, match="region"):
        measure(reference, reference, config)


def test_different_image_sizes_are_rejected():
    with pytest.raises(CoreError, match="size"):
        measure(Image.new("RGBA", (10, 10)), Image.new("RGBA", (9, 10)), policy())
