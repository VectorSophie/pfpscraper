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

## Run
`python discscraper.py`, or double-click `run.bat` (silent, no console). Drop a shortcut to `run.bat` in your Startup folder to launch at login.

## Output
`<output_dir>/<YYMMDD>/<slug>.png` — one dated folder per day, 512px static PNG. Stamped users get `<slug>-A.png`, `<slug>-B.png`, etc. Same-day duplicates are skipped.

## Test
`python test_discscraper.py`
