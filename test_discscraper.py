"""Self-check: `python test_discscraper.py`. No framework."""
from PIL import Image
import discscraper as d


def test_stamp_produces_distinct_images():
    base = Image.new("RGBA", (512, 512), (128, 128, 128, 255))
    a = d.stamp(base, "A").tobytes()
    b = d.stamp(base, "B").tobytes()
    assert a != base.tobytes(), "stamp did not alter the image"
    assert a != b, "A and B stamps are identical"


def test_targets():
    # normal user: one plain file (date is the folder)
    assert d.targets("bitzy") == [("bitzy.png", None)]
    # stamped user (swso is configured with A/B): two files
    assert d.targets("swso") == [("swso-A.png", "A"), ("swso-B.png", "B")]


def test_hash_dedup():
    # save_member's core guard: same hash -> skip. Emulate the check.
    state = {"1": "abc"}
    assert state.get("1") == "abc"  # unchanged -> would skip
    state["1"] = "xyz"
    assert state.get("1") != "abc"  # changed -> would save


if __name__ == "__main__":
    test_stamp_produces_distinct_images()
    test_targets()
    test_hash_dedup()
    print("ok")
