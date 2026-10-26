"""Generate deterministic synthetic idle-game events for pipeline testing.

This is simulated data, not real player behavior or Kolibri Games data.
"""

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


def generate_events(players=500, days=14, seed=42):
    if players < 1 or days < 2:
        raise ValueError("players must be positive and days must be at least 2")

    rng = random.Random(seed)
    rows = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for n in range(1, players + 1):
        pid = f"player_{n:06d}"
        install = start + timedelta(
            days=rng.randint(0, 6),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        channel = rng.choice(["organic", "paid_social", "search"])
        platform = rng.choice(["android", "ios"])
        engagement = rng.betavariate(2.5, 2.0)
        balance, level, upgrade_cost = 100, 1, 100
        previous_active_day = 0
        session_number = 0

        def emit(ts, name, session=None, day=0, reward=0, cost=None):
            rows.append({
                "player_id": pid,
                "event_timestamp_utc": ts.isoformat(),
                "event_name": name,
                "session_id": session,
                "days_since_install": day,
                "level": level,
                "currency_balance": balance,
                "reward_amount": reward,
                "upgrade_cost": cost,
                "acquisition_channel": channel,
                "platform": platform,
            })

        emit(install, "install")

        for day in range(days):
            active = day == 0 or rng.random() < min(
                0.90, (0.15 + 0.65 * engagement) * (0.90 ** (day - 1))
            )
            if not active:
                continue

            sessions_today = 1 + int(rng.random() < 0.18)

            for _ in range(sessions_today):
                session_number += 1
                sid = f"{pid}_session_{session_number:03d}"
                ts = install + timedelta(
                    days=day, minutes=rng.randint(5, 120)
                )
                ts += timedelta(minutes=session_number * 2)

                emit(ts, "session_start", sid, day)

                if day == 0 and session_number == 1:
                    if rng.random() < 0.65 + 0.25 * engagement:
                        emit(ts + timedelta(seconds=20),
                             "tutorial_complete", sid, day)

                if day > previous_active_day and day > 0:
                    if rng.random() < 0.65:
                        reward = min(
                            500,
                            25 * (day - previous_active_day)
                            + rng.randint(0, 20),
                        )
                        balance += reward
                        emit(ts + timedelta(seconds=40),
                             "offline_reward_claim", sid, day, reward)

                if balance >= upgrade_cost and rng.random() < 0.50:
                    balance -= upgrade_cost
                    level += 1
                    emit(ts + timedelta(seconds=60),
                         "upgrade_completed", sid, day, cost=upgrade_cost)
                    upgrade_cost = int(upgrade_cost * 1.5)

                emit(ts + timedelta(seconds=90), "session_end", sid, day)
                previous_active_day = day

    df = pd.DataFrame(rows)
    df = df.sort_values(
        ["event_timestamp_utc", "player_id", "event_name"],
        kind="mergesort",
    ).reset_index(drop=True)
    df.insert(
        0, "event_id",
        [f"synthetic_event_{i:09d}" for i in range(1, len(df) + 1)],
    )
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", type=int, default=500)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic/idle_game_events.csv"),
    )
    args = parser.parse_args()

    df = generate_events(args.players, args.days, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)

    print("DATA STATUS: SYNTHETIC — NOT REAL PLAYER DATA")
    print(f"File: {args.output.resolve()}")
    print(f"Rows: {len(df):,}")
    print(f"Players: {df['player_id'].nunique():,}")
    print("\nEvent counts:")
    print(df["event_name"].value_counts().to_string())


if __name__ == "__main__":
    main()
