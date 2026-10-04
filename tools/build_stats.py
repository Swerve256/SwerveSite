r"""Generate public SwerveSite stats from the local stream_stats MySQL database.

No credentials are stored in this repository. The script loads database settings
from environment variables and, when present, from a local .env file.

Default local .env path on the stream PC:
  C:\stream-backend\.env

Supported variables:
  SWERVE_DB_HOST (default: localhost)
  SWERVE_DB_USER (default: root)
  SWERVE_DB_PASSWORD (required)
  SWERVE_DB_NAME (default: stream_stats)
  SWERVE_ENV_FILE (optional override for the .env path)

The script only publishes aggregate/community-facing data to data/stats.json.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "stats.json"
CENTRAL_TZ = ZoneInfo("America/Chicago")

DEFAULT_ENV_FILE = Path(r"C:\stream-backend\.env")
ENV_FILE = Path(os.environ.get("SWERVE_ENV_FILE", str(DEFAULT_ENV_FILE)))
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


def db_config() -> dict:
    password = os.environ.get("SWERVE_DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "SWERVE_DB_PASSWORD is not set. "
            f"Set it in the environment or in {ENV_FILE}."
        )

    return {
        "host": os.environ.get("SWERVE_DB_HOST", "localhost"),
        "user": os.environ.get("SWERVE_DB_USER", "root"),
        "password": password,
        "database": os.environ.get("SWERVE_DB_NAME", "stream_stats"),
    }


def fmt_duration(start_time, end_time) -> str:
    if not start_time or not end_time:
        return "—"
    seconds = max(0, int((end_time - start_time).total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def central_stream_date(start_time):
    if start_time is None:
        return None
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    else:
        start_time = start_time.astimezone(timezone.utc)
    return start_time.astimezone(CENTRAL_TZ).date()


def calculate_daily_streak(streams, attended_stream_ids) -> int:
    """Count consecutive attended Central streaming days, not individual streams."""
    grouped: dict[object, set[int]] = defaultdict(set)
    for stream in streams:
        stream_date = central_stream_date(stream.get("start_time"))
        if stream_date is not None:
            grouped[stream_date].add(int(stream["stream_id"]))

    attended = {int(stream_id) for stream_id in attended_stream_ids}
    today = datetime.now(CENTRAL_TZ).date()
    streak = 0

    for stream_date in sorted(grouped.keys(), reverse=True):
        attended_day = any(stream_id in attended for stream_id in grouped[stream_date])

        if attended_day:
            streak += 1
            continue

        # Do not break a streak during the current Central day. Shaun may stream
        # again later, and attending either stream should preserve the day.
        if stream_date == today:
            continue

        break

    return streak


def main() -> None:
    conn = mysql.connector.connect(**db_config())
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT stream_id, platform, title, game, start_time, end_time
            FROM streams
            WHERE is_validated = 1
            ORDER BY start_time DESC, stream_id DESC
            """
        )
        streams = cur.fetchall()

        if not streams:
            raise RuntimeError("No validated streams found")

        latest = streams[0]
        latest_id = latest["stream_id"]

        # Total stream history is intentionally independent of streak validation.
        cur.execute("SELECT COUNT(*) AS total_streams FROM streams")
        total_stream_row = cur.fetchone()
        total_streams = int(total_stream_row["total_streams"] or 0)

        cur.execute(
            """
            SELECT COUNT(*) AS messages,
                   COUNT(DISTINCT viewer_id) AS unique_chatters
            FROM chat_messages
            WHERE stream_id = %s
              AND LOWER(COALESCE(username, '')) <> 'swervebot'
            """,
            (latest_id,),
        )
        latest_counts = cur.fetchone()

        cur.execute(
            """
            SELECT
                cm.viewer_id,
                COALESCE(NULLIF(v.alias, ''), v.username, MAX(cm.username)) AS username,
                COUNT(*) AS message_count
            FROM chat_messages cm
            LEFT JOIN viewers v ON v.viewer_id = cm.viewer_id
            WHERE cm.stream_id = %s
              AND LOWER(COALESCE(v.username, cm.username, '')) NOT IN ('swervebot', 'swerve256')
            GROUP BY cm.viewer_id, v.alias, v.username
            ORDER BY message_count DESC, username ASC
            LIMIT 10
            """,
            (latest_id,),
        )
        latest_chatters = cur.fetchall()

        cur.execute(
            """
            SELECT
                cm.viewer_id,
                COALESCE(NULLIF(v.alias, ''), v.username, MAX(cm.username)) AS username,
                COUNT(*) AS message_count
            FROM chat_messages cm
            JOIN streams s ON s.stream_id = cm.stream_id
            LEFT JOIN viewers v ON v.viewer_id = cm.viewer_id
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(v.username, cm.username, '')) NOT IN ('swervebot', 'swerve256')
            GROUP BY cm.viewer_id, v.alias, v.username
            ORDER BY message_count DESC, username ASC
            LIMIT 10
            """
        )
        all_time_chatters = cur.fetchall()

        cur.execute(
            """
            SELECT COUNT(*) AS total_messages,
                   COUNT(DISTINCT cm.viewer_id) AS unique_chatters
            FROM chat_messages cm
            JOIN streams s ON s.stream_id = cm.stream_id
            LEFT JOIN viewers v ON v.viewer_id = cm.viewer_id
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(v.username, cm.username, '')) NOT IN ('swervebot', 'swerve256')
            """
        )
        all_time = cur.fetchone()

        # Fetch one attendance row per viewer per validated stream. Lifetime
        # attendance still counts streams; current streaks group those streams
        # into Central calendar days.
        cur.execute(
            """
            SELECT DISTINCT
                cm.viewer_id,
                cm.stream_id,
                COALESCE(NULLIF(v.alias, ''), v.username, cm.username) AS username,
                COALESCE(v.username, cm.username, '') AS base_username
            FROM chat_messages cm
            JOIN streams s ON s.stream_id = cm.stream_id
            LEFT JOIN viewers v ON v.viewer_id = cm.viewer_id
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(v.username, cm.username, '')) NOT IN ('swervebot', 'swerve256')
            """
        )
        attendance_rows = cur.fetchall()

        attended_by_viewer: dict[int, set[int]] = defaultdict(set)
        names: dict[int, str] = {}
        for row in attendance_rows:
            viewer_id = int(row["viewer_id"])
            attended_by_viewer[viewer_id].add(int(row["stream_id"]))
            if row.get("username"):
                names[viewer_id] = row["username"]

        streaks = []
        attendance_leaders = []

        for viewer_id, attended in attended_by_viewer.items():
            username = names.get(viewer_id, f"Viewer {viewer_id}")

            streak = calculate_daily_streak(streams, attended)
            if streak > 0:
                streaks.append({
                    "viewer_id": viewer_id,
                    "username": username,
                    "streak": streak,
                })

            # Lifetime attendance remains every distinct validated stream attended.
            attendance_leaders.append({
                "viewer_id": viewer_id,
                "username": username,
                "streams": len(attended),
            })

        streaks.sort(key=lambda item: (-item["streak"], item["username"].lower()))
        attendance_leaders.sort(
            key=lambda item: (-item["streams"], item["username"].lower())
        )

        cur.execute(
            """
            SELECT
                viewer_id,
                COALESCE(NULLIF(alias, ''), username) AS username,
                watch_minutes
            FROM viewers
            WHERE watch_minutes > 0
              AND LOWER(COALESCE(username, '')) NOT IN ('swerve256', 'swervebot')
            ORDER BY watch_minutes DESC, username ASC
            LIMIT 10
            """
        )
        watchtime_leaders = cur.fetchall()

        payload = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "latest_stream": {
                "stream_id": latest_id,
                "date": central_stream_date(latest["start_time"]).isoformat() if latest["start_time"] else None,
                "title": latest.get("title") or latest.get("game") or f"Stream #{latest_id}",
                "game": latest.get("game") or "",
                "duration": fmt_duration(latest.get("start_time"), latest.get("end_time")),
                "messages": int(latest_counts["messages"] or 0),
                "unique_chatters": int(latest_counts["unique_chatters"] or 0),
                "top_chatter": latest_chatters[0]["username"] if latest_chatters else "—",
            },
            "streak_leaders": [
                {"username": row["username"], "streak": row["streak"]}
                for row in streaks[:10]
            ],
            "attendance_leaders": [
                {"username": row["username"], "streams": row["streams"]}
                for row in attendance_leaders[:10]
            ],
            "watchtime_leaders": [
                {
                    "username": row["username"],
                    "watch_minutes": int(row["watch_minutes"] or 0),
                }
                for row in watchtime_leaders
            ],
            "top_chatters": [
                {"username": row["username"], "messages": int(row["message_count"])}
                for row in latest_chatters
            ],
            "all_time_chatters": [
                {"username": row["username"], "messages": int(row["message_count"])}
                for row in all_time_chatters
            ],
            "all_time": {
                "validated_streams": len(streams),
                "total_streams": total_streams,
                "total_messages": int(all_time["total_messages"] or 0),
                "unique_chatters": int(all_time["unique_chatters"] or 0),
            },
        }

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {OUTPUT}")
        print(f"Latest validated stream: {latest_id}")
        print(f"Current streak leaders: {len(payload['streak_leaders'])}")
        print(f"All-time attendance leaders: {len(payload['attendance_leaders'])}")
        print(f"Watch time leaders: {len(payload['watchtime_leaders'])}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
