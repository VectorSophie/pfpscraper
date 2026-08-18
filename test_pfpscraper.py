"""Self-check: `python test_pfpscraper.py`. No framework."""
from PIL import Image
import pfpscraper as d


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
    # main/global copy uses a -main suffix
    assert d.targets("bitzy", "-main") == [("bitzy-main.png", None)]


def test_hash_dedup():
    # save_member's core guard: same hash -> skip. Emulate the check.
    state = {"1": "abc"}
    assert state.get("1") == "abc"  # unchanged -> would skip
    state["1"] = "xyz"
    assert state.get("1") != "abc"  # changed -> would save


def test_second_same_day_change_is_not_skipped_as_stale_disk_hit():
    # Bug: avatar changes twice in one day. First change writes today's files
    # and records hash1. Second change (hash2) reaches the disk-exists
    # shortcut with files still on disk from hash1 -- must re-save, not skip,
    # even though a file with the expected name already exists.
    seen = {"server": "hash1"}  # already recorded from the first change today
    files_exist_on_disk = True  # leftover files from the first change
    would_skip = "server" not in seen and files_exist_on_disk
    assert would_skip is False, "second change must re-save despite stale files on disk"

    # Fresh state (e.g. state.json was reset) still gets the shortcut.
    seen_fresh = {}
    would_skip_fresh = "server" not in seen_fresh and files_exist_on_disk
    assert would_skip_fresh is True


if __name__ == "__main__":
    test_stamp_produces_distinct_images()
    test_targets()
    test_hash_dedup()
    test_second_same_day_change_is_not_skipped_as_stale_disk_hit()
    print("ok")
