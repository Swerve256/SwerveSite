"""Generate public SwerveSite stats from the local stream_stats MySQL database.

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
from datetime import datetime
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "stats.json"

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
        validated_ids = [row["stream_id"] for row in streams]

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
            SELECT viewer_id, MAX(username) AS username, COUNT(*) AS message_count
            FROM chat_messages
            WHERE stream_id = %s
              AND LOWER(COALESCE(username, '')) <> 'swervebot'
            GROUP BY viewer_id
            ORDER BY message_count DESC, username ASC
            LIMIT 10
            """,
            (latest_id,),
        )
        latest_chatters = cur.fetchall()

        cur.execute(
            """
            SELECT cm.viewer_id,
                   MAX(cm.username) AS username,
                   COUNT(*) AS message_count
            FROM chat_messages cm
            JOIN streams s ON s.stream_id = cm.stream_id
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(cm.username, '')) <> 'swervebot'
            GROUP BY cm.viewer_id
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
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(cm.username, '')) <> 'swervebot'
            """
        )
        all_time = cur.fetchone()

        # Fetch one attendance row per viewer per validated stream. Python then
        # walks the validated stream sequence newest -> oldest and stops at the
        # first miss, matching the live !streak rule.
        cur.execute(
            """
            SELECT DISTINCT cm.viewer_id, cm.stream_id, cm.username
            FROM chat_messages cm
            JOIN streams s ON s.stream_id = cm.stream_id
            WHERE s.is_validated = 1
              AND LOWER(COALESCE(cm.username, '')) <> 'swervebot'
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
        for viewer_id, attended in attended_by_viewer.items():
            streak = 0
            for stream_id in validated_ids:
                if stream_id in attended:
                    streak += 1
                else:
                    break
            if streak > 0:
                streaks.append({
                    "viewer_id": viewer_id,
                    "username": names.get(viewer_id, f"Viewer {viewer_id}"),
                    "streak": streak,
                })

        streaks.sort(key=lambda item: (-item["streak"], item["username"].lower()))

        payload = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "latest_stream": {
                "stream_id": latest_id,
                "date": latest["start_time"].date().isoformat() if latest["start_time"] else None,
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
                "total_messages": int(all_time["total_messages"] or 0),
                "unique_chatters": int(all_time["unique_chatters"] or 0),
            },
        }

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {OUTPUT}")
        print(f"Latest validated stream: {latest_id}")
        print(f"Current streak leaders: {len(payload['streak_leaders'])}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
