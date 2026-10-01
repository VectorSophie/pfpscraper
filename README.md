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
   - `save_main` — optional bool (default `false`). Also save each user's main/global (default) pfp into its own `main/` folder.

## Run
- Windows: `python pfpscraper.py`, or double-click `run.bat` (silent). Put a shortcut to `run.bat` in your Startup folder to launch at login.
- Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then run it as a systemd user service (`~/.config/systemd/user/pfpscraper.service`, `ExecStart=<repo>/.venv/bin/python pfpscraper.py`, `systemctl --user enable --now pfpscraper`).

## Output
```
<output_dir>/server/<YYMMDD>/<slug>.png   what the server shows (server pfp, else global)
<output_dir>/server/current/<slug>.png    always the newest -> point the tierlist here
<output_dir>/main/<YYMMDD>/<slug>.png     global/default pfp (only with save_main)
<output_dir>/main/current/<slug>.png
```
512px static PNG. Stamped users get `<slug>-A.png`, `<slug>-B.png`, etc. If someone changes their pfp again on the same day, the earlier file is kept and the new one is saved as `<slug>-HHMMSS.png`. `current/` always holds the newest one under the plain name.

## Test
`python test_pfpscraper.py`
