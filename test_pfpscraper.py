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
    # same-day re-change gets a time tag
    assert d.targets("bitzy", "-1230") == [("bitzy-1230.png", None)]


def test_multiple_changes_same_day():
    # Real save_member against a temp dir with fake member/assets.
    import asyncio, io, tempfile, types
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp())
    d.OUT, d.STATE_PATH, d.SAVE_MAIN = tmp, tmp / "state.json", True
    state = {}
    uid, slug = next(iter(d.USERS.items()))
    colors = {}

    async def fake_fetch(asset):
        await asyncio.sleep(0.01)  # let concurrent handlers interleave
        buf = io.BytesIO()
        Image.new("RGBA", (8, 8), colors.setdefault(asset.key, (len(colors) * 40, 0, 0, 255))).save(buf, "PNG")
        return buf.getvalue()
    d.fetch_bytes = fake_fetch

    def member(server, main):
        a = lambda k: types.SimpleNamespace(key=k)
        return types.SimpleNamespace(id=int(uid), display_avatar=a(server), avatar=a(main), default_avatar=a("dflt"))

    clock = iter(["120000", "130000", "140000"])
    real_dt = d.datetime
    class FakeDT:
        @staticmethod
        def now():
            return real_dt.strptime("261001" + next(clock), "%y%m%d%H%M%S")
    d.datetime = FakeDT

    async def run():
        m1 = member("h1", "h1")
        # member_update + user_update fire together for one change -> one save
        await asyncio.gather(d.save_member(m1, state), d.save_member(m1, state))
        await d.save_member(member("h2", "h2"), state)  # 2nd change same day
    try:
        asyncio.run(run())
    finally:
        d.datetime = real_dt

    day = sorted(p.name for p in (tmp / "server" / "261001").iterdir())
    assert len(day) == 2 * len(d.targets(slug)), day  # both changes kept, no dupes
    assert any("-1" in n for n in day), day          # 2nd is time-tagged
    cur = tmp / "server" / "current" / d.targets(slug)[0][0]
    assert Image.open(cur).getpixel((0, 0)) == colors["h2"], "current/ not latest"
    assert (tmp / "main" / "261001").is_dir() and (tmp / "main" / "current").is_dir()
    assert state[uid] == {"server": "h2", "main": "h2"}


if __name__ == "__main__":
    test_stamp_produces_distinct_images()
    test_targets()
    test_multiple_changes_same_day()
    print("ok")
