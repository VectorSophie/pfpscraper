# pfpscraper

Background bot that saves tracked Discord friends' avatars to a local folder whenever they change. Built for hosting tierlists — one folder of current pfps, kept fresh automatically.

Event-driven (gateway), near-zero API cost: it only downloads an image when someone actually changes their avatar. Runs while your PC is on; on startup it catches up on anything that changed while you were offline.

## Setup
1. `pip install -r requirements.txt`
2. Enable the **Server Members Intent** for the bot in the Discord Developer Portal.
3. Put your bot token in `.env`:
   ```
   DISCORD_TOKEN=your_token_here
   ```
4. Edit `config.json`:
   - `output_dir` — where images go.
   - `users` — `{ "<discord_user_id>": "<slug>" }`. Only listed users are tracked.
   - `stamps` — optional `{ "<slug>": ["A", "B"] }` to save multiple copies with a letter stamped bottom-right (bold white, dark outline).
   - `save_main` — optional bool (default `false`). By default only the **per-server** avatar is saved. Set `true` to also save each user's main/global pfp as `<slug>-main.png` (skipped when it's the same image as the server one).

## Run
`python pfpscraper.py`, or double-click `run.bat` (silent, no console). Drop a shortcut to `run.bat` in your Startup folder to launch at login.

## Output
`<output_dir>/<YYMMDD>/<slug>.png` — one dated folder per day, 512px static PNG (the per-server avatar). Stamped users get `<slug>-A.png`, `<slug>-B.png`, etc. With `save_main`, the global pfp is also written as `<slug>-main.png`. Same-day duplicates are skipped.

`<output_dir>/current/` always mirrors the newest set — every save writes to both the dated folder and `current/`, so point your tierlist at `current/` and it's never stale.

## Test
`python test_pfpscraper.py`
