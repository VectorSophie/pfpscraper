# discscraper — design

Background bot that saves a friend's Discord avatar to a central folder whenever it changes. Event-driven, near-zero API cost, low maintenance.

## Purpose
Keep `C:\Users\PC\OneDrive\Desktop\league` stocked with current avatars for tierlist hosting, without manual re-downloading. Only tracks a fixed set of friends, saved under hand-chosen slugs.

## Architecture
Single discord.py process, gateway-connected while the PC is on. No polling.

Files:
- `discscraper.py` — the bot.
- `config.json` — hand/auto-filled: `token`, `output_dir`, `users` (`{ "<user_id>": "<slug>" }`), `stamps` (`{ "<slug>": ["A","B"] }`).
- `state.json` — auto: `{ "<user_id>": "<last_avatar_hash>" }`.
- `run.bat` — `pythonw discscraper.py`, placed in Startup for silent launch at login.

Dependencies: `discord.py`, `Pillow` (stamping only).

## Flow
1. **Startup reconciliation:** for each mapped member, compare current `display_avatar` hash to `state.json`. Changed/new → save. Covers avatars that changed while the PC was off.
2. **Live:** `on_member_update` (server avatar) and `on_user_update` (global avatar). Mapped user + hash changed → save.
3. **Save:** `display_avatar` (per-server avatar if set, else global) as static PNG, 512px → write `<output_dir>/<YYMMDD>/<slug>.png` (one folder per day). Skip write if that file exists (no same-day churn). Update `state.json`. If `save_main` is set, also save the global pfp as `<slug>-main.png` (skipped when identical to the server one).

## Stamping (swso)
For any slug listed in `stamps`, write one file per letter into the day folder: `<slug>-<L>.png`. Same source image, letter drawn bottom-right via Pillow — bold white, thin dark outline, ~1/4 image height.

## Setup (once)
- Enable **Server Members Intent** in the Discord Developer Portal.
- Populate `config.json`: assisted by pulling the server roster (id, username, nickname, avatar) and auto-matching to existing filename slugs; uncertain nickname matches flagged for user confirmation.

## Non-goals
- No database (two JSON files).
- No polling fallback (startup reconciliation covers gaps).
- Animated avatars saved as static PNG frame.

## Test
One self-check: stamping produces two distinct files and hash-change detection triggers a save (mocked avatar hash). No framework.
