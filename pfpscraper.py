"""Background bot: saves tracked friends' Discord avatars to a folder on change.

Gateway-connected while the PC is on. On startup it reconciles anyone who
changed while offline; then reacts to live avatar-update events. Near-zero
API cost (only downloads bytes when an avatar actually changes).
"""
import io
import json
import logging
from datetime import datetime
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent

# Runs headless under pythonw (no stdout/stderr), so log to a file in utf-8 --
# printing would die on the console's local codec.
logging.basicConfig(filename=HERE / "pfpscraper.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    encoding="utf-8")
log = logging.getLogger("pfpscraper")
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
STATE_PATH = HERE / "state.json"
OUT = Path(CONFIG["output_dir"])
USERS = CONFIG["users"]              # {user_id: slug}
STAMPS = CONFIG.get("stamps", {})    # {slug: [letters]}
SAVE_MAIN = CONFIG.get("save_main", False)  # also store global pfp as -main
GUILD_ID = CONFIG.get("guild_id")    # restrict to this server (else all guilds)
CURRENT = OUT / "current"            # always mirrors the newest set
SIZE = 512


def in_scope(guild) -> bool:
    return GUILD_ID is None or str(guild.id) == str(GUILD_ID)


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


def targets(slug: str, suffix: str = ""):
    """Filenames to write for a slug (plain name; date is the folder)."""
    if slug in STAMPS:
        return [(f"{slug}-{L}{suffix}.png", L) for L in STAMPS[slug]]
    return [(f"{slug}{suffix}.png", None)]


def sources(member: discord.Member):
    """(kind, filename-suffix, asset) to save for a member.

    Default: the per-server avatar (guild avatar if set, else global).
    If SAVE_MAIN, also the main/global avatar as `<slug>-main.png` — but only
    when it differs from the server one (else it's the same image)."""
    out = [("server", "", member.display_avatar)]
    if SAVE_MAIN:
        main = member.avatar or member.default_avatar
        if main.key != member.display_avatar.key:
            out.append(("main", "-main", main))
    return out


async def save_member(member: discord.Member, state: dict) -> bool:
    """Save member's avatar(s) if the hash changed. Returns True if any saved."""
    uid = str(member.id)
    slug = USERS.get(uid)
    if slug is None:
        return False

    seen = state.setdefault(uid, {})
    if isinstance(seen, str):  # migrate old single-hash format
        seen = state[uid] = {}
    date = datetime.now().strftime("%y%m%d")
    dirs = [OUT / date, CURRENT]  # dated history + always-latest mirror
    changed = False

    for kind, suffix, asset in sources(member):
        if seen.get(kind) == asset.key:
            continue
        files = targets(slug, suffix)
        if all((d / name).exists() for d in dirs for name, _ in files):
            seen[kind] = asset.key  # already have today's copy; remember hash
            continue
        base = to_png(await asset.replace(size=SIZE).read())
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            for name, letter in files:
                (stamp(base, letter) if letter else base).save(d / name)
        seen[kind] = asset.key
        changed = True
        log.info("saved %s (%s): %s", slug, kind, [n for n, _ in files])

    save_state(state)
    return changed


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    CURRENT.mkdir(parents=True, exist_ok=True)  # always exists, even if nothing changed
    state = load_state()
    saved = 0
    for guild in client.guilds:
        if not in_scope(guild):
            continue
        for member in guild.members:
            if str(member.id) in USERS:
                if await save_member(member, state):
                    saved += 1
    log.info("ready as %s: reconciled, %s new avatar(s)", client.user, saved)


@client.event
async def on_member_update(before, after):
    if in_scope(after.guild) and str(after.id) in USERS:
        await save_member(after, load_state())


@client.event
async def on_user_update(before, after):
    # global avatar change: find the member in the scoped guild
    for guild in client.guilds:
        if not in_scope(guild):
            continue
        m = guild.get_member(after.id)
        if m and str(m.id) in USERS:
            await save_member(m, load_state())
            return


if __name__ == "__main__":
    # log_handler=None: don't let discord.py attach its own stderr handler
    client.run(load_token(), log_handler=None)
