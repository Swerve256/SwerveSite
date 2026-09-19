# SwerveSite 2.0 — Stats Publishing

## Goal

The public website never connects directly to MySQL or the local Flask backend.

SwerveSite now uses two separate stats moments because the OBS Ending screen needs fresh numbers *before* the stream is closed, while the public website should only show finalized validated data.

## Phase 1 — provisional Ending screen recap

The local Ending screen is intentionally separate from the public website snapshot.

Flow:

1. Shaun presses the Stream Deck Ending multi-action.
2. Stream Deck triggers the Streamer.bot action `Build Live Recap` before the OBS scene change.
3. Streamer.bot runs `C:\stream-backend\build_live_recap.py`.
4. The script reads the current open stream and writes `C:\stream-backend\live-recap.json`.
5. The local Flask backend serves the Ending screen at `http://127.0.0.1:5000/ending` and the provisional JSON at `/live-recap.json`.
6. OBS switches to the Ending scene and displays the freshly generated recap.

The live recap can include:

- current stream title
- elapsed duration
- current message count
- current unique chatters
- current top chatter
- current stream top chatters
- provisional streak leaders, including tonight for viewers who participated

This data is **provisional** because the stream has not yet been approved as a valid historical stream.

## Phase 2 — finalized public stats snapshot

After the stream ends:

1. Streamer.bot closes the logical stream.
2. Shaun receives the Yes/No validation popup.
3. If the stream is rejected (`is_validated = 0`), no public stats are published.
4. If the stream is approved (`is_validated = 1`), `tools/build_stats.py` generates the official `data/stats.json` snapshot from validated history only.
5. `tools/publish_stats.py` verifies the expected Git branch, validates the generated JSON, stages **only** `data/stats.json`, commits it, and pushes it to GitHub.
6. GitHub Pages serves the finalized snapshot to the website.

During development the guarded publish branch defaults to `swerve-2.0`. At launch, `SWERVE_SITE_BRANCH` can be changed to the production branch without changing the script.

## Public data contract

`data/stats.json` contains only community-facing aggregate data:

- latest validated stream ID/date/title/game/duration
- latest stream messages + unique chatters
- latest stream top chatter
- current top streaks
- latest stream top chatters
- all-time top chatters
- validated stream count
- all-time validated-stream message count
- all-time unique chatters

It does **not** contain database credentials, platform user IDs, email addresses, private configuration, or raw message text.

## Local generator

`tools/build_stats.py` reads the database using environment variables:

- `SWERVE_DB_HOST` — defaults to `localhost`
- `SWERVE_DB_USER` — defaults to `root`
- `SWERVE_DB_PASSWORD` — required
- `SWERVE_DB_NAME` — defaults to `stream_stats`

The script writes `data/stats.json` in the local repository checkout.

## Guarded publisher

`tools/publish_stats.py` is designed to be called only after successful validation.

Safety rules built into the script:

- refuses to publish from the wrong Git branch
- requires the generated JSON to contain a timestamp and latest stream ID
- stages only `data/stats.json`
- never runs `git add .`
- stores no GitHub token or database password
- does nothing when the generated snapshot has not changed

The local repository must already have working Git authentication before the automated push step can be enabled.

## Streak rule

The public streak leaderboard follows the same rule as `!streak`:

- only validated streams count
- one or more stored interactions means the viewer attended
- work backward from the newest validated stream
- stop at the first missed validated stream
- rejected/test streams are ignored

The provisional Ending recap adds the current open stream only for viewers who have participated tonight.

The public JSON stores usernames and streak counts only. Viewer database IDs are not published.

## OBS recap

The OBS Ending screen is local and reads `live-recap.json`. It does not wait on GitHub and does not require the stream to be validated first.

The public site reads `data/stats.json`, which is the finalized validated source of truth.

This separation prevents an unvalidated/test stream from becoming permanent public history while still allowing the Ending screen to show tonight's live recap before the stream is closed.
