# SwerveSite 2.0 — Stats Publishing

## Goal

The public website and OBS recap page should never connect directly to MySQL or the local Flask backend.

The publishing flow is:

1. Streamer.bot records chat + stream activity locally.
2. Stream ends.
3. Shaun validates the stream with the Yes/No popup.
4. If the stream is validated (`is_validated = 1`), `tools/build_stats.py` generates `data/stats.json` from MySQL.
5. A later automation step commits only the generated public JSON to GitHub.
6. GitHub Pages serves the updated stats to both `stats.html` and `recap.html`.

If the stream is rejected (`is_validated = 0`), nothing should be published.

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

## Streak rule

The public streak leaderboard follows the same rule as `!streak`:

- only validated streams count
- one or more stored interactions means the viewer attended
- work backward from the newest validated stream
- stop at the first missed validated stream
- rejected/test streams are ignored

The public JSON stores usernames and streak counts only. Viewer database IDs are not published.

## OBS recap

`recap.html` reads the same `data/stats.json` as the public stats page. This gives the website and OBS one source of truth while allowing completely different presentations.

The final automation will be attached to the successful validation path so publishing occurs only after Shaun approves a real stream.
