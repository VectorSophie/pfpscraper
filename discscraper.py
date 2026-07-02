"""Background bot: saves tracked friends' Discord avatars to a folder on change.

Gateway-connected while the PC is on. On startup it reconciles anyone who
changed while offline; then reacts to live avatar-update events. Near-zero
API cost (only downloads bytes when an avatar actually changes).
"""
import io
import json
from datetime import datetime
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
STATE_PATH = HERE / "state.json"
OUT = Path(CONFIG["output_dir"])
USERS = CONFIG["users"]              # {user_id: slug}
STAMPS = CONFIG.get("stamps", {})    # {slug: [letters]}
SIZE = 512


def load_token():
    for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DISCORD_TOKEN"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DISCORD_TOKEN not found in .env")


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def to_png(data: bytes) -> Image.Image:
    """Decode any avatar (webp/gif/png) to a static RGBA image (first frame)."""
    return Image.open(io.BytesIO(data)).convert("RGBA")


def stamp(img: Image.Image, letter: str) -> Image.Image:
    """Draw `letter` bottom-right: bold white with a thin dark outline."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    fontsize = img.height // 4
    try:
        font = ImageFont.truetype("arialbd.ttf", fontsize)
    except OSError:
        font = ImageFont.load_default()
    stroke = max(2, fontsize // 16)
    l, t, r, b = draw.textbbox((0, 0), letter, font=font, stroke_width=stroke)
    margin = img.width // 20
    x = img.width - (r - l) - margin - l
    y = img.height - (b - t) - margin - t
    draw.text((x, y), letter, font=font, fill="white",
              stroke_width=stroke, stroke_fill=(0, 0, 0))
    return img


def targets(slug: str):
    """Filenames to write for a slug (plain name; date is the folder)."""
    if slug in STAMPS:
        return [(f"{slug}-{L}.png", L) for L in STAMPS[slug]]
    return [(f"{slug}.png", None)]


async def save_member(member: discord.Member, state: dict) -> bool:
    """Save member's avatar if its hash changed. Returns True if saved."""
    uid = str(member.id)
    slug = USERS.get(uid)
    if slug is None:
        return False
    key = member.display_avatar.key  # avatar hash; changes when pfp changes
    if state.get(uid) == key:
        return False

    date = datetime.now().strftime("%y%m%d")
    day_dir = OUT / date
    files = targets(slug)
    if all((day_dir / name).exists() for name, _ in files):
        state[uid] = key  # already have today's copy; just remember the hash
        save_state(state)
        return False

    day_dir.mkdir(parents=True, exist_ok=True)
    data = await member.display_avatar.replace(size=SIZE).read()
    base = to_png(data)
    for name, letter in files:
        img = stamp(base, letter) if letter else base
        img.save(day_dir / name)
    state[uid] = key
    save_state(state)
    print(f"saved {slug}: {[n for n, _ in files]}")
    return True


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    OUT.mkdir(parents=True, exist_ok=True)
    state = load_state()
    saved = 0
    for guild in client.guilds:
        for member in guild.members:
            if str(member.id) in USERS:
                if await save_member(member, state):
                    saved += 1
    print(f"ready as {client.user} — reconciled, {saved} new avatar(s)")


@client.event
async def on_member_update(before, after):
    if str(after.id) in USERS:
        await save_member(after, load_state())


@client.event
async def on_user_update(before, after):
    # global avatar change: find the member wherever we share a guild
    for guild in client.guilds:
        m = guild.get_member(after.id)
        if m and str(m.id) in USERS:
            await save_member(m, load_state())
            return


if __name__ == "__main__":
    client.run(load_token())
