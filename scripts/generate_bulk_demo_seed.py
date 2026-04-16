#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Motiv — bulk demo SQL generator (50–100 synthetic app_user rows + related data)
#
# Data model / write surfaces (see sql/motivdata_schema.sql and migrations in sql/):
#   admin, group_admin, app_user — auth & profiles
#   motiv_group, user_group — groups & membership
#   group_invite — GA invites (migration_group_invite.sql)
#   group_workout, group_workout_attendance — scheduling & RSVP
#   challenge, user_challenge_leave, challenge_participant_exclusion — challenges
#   workout, workout_log, exercise — workout history & sets/reps/weight
#   post — feed posts (multipart API on User/PU, GroupAdmin/post-GA, Admin/PostA)
#
# Interactive pages checklist: Descriptions_of_each_Page.txt
#
# Prerequisites before running generated SQL in MySQL Workbench:
#   1) motivdata_schema.sql (+ migrations you use in prod)
#   2) motivdata_seed.sql (or equivalent) so motiv_group and exercise rows exist
#   3) Backup DB if not disposable — this script does not TRUNCATE or DELETE.
#
# Generated accounts: bulkdemo+00001@motiv.test … password123 (same @pw hash as seed)
# -----------------------------------------------------------------------------
"""Emit SQL to stdout. See module comment block for inventory and prerequisites."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

# Same scrypt hash as sql/motivdata_seed.sql (login password: password123)
PW_HASH = (
    "scrypt:32768:8:1$ytdxORmJta7mFCdr$"
    "56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70"
)


def _sql_str(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "''") + "'"


def _week_bounds(today: date) -> tuple[date, date]:
    """Calendar week Monday 00:00 concept as dates: Monday through following Sunday."""
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)
    return monday, next_monday


def emit_ga_expansion_block(today: date) -> None:
    """
    Emit the fixed-size bulk demo topology requested by product:
      - 20 group admins
      - 2 groups per group admin (40 total)
      - 5 scheduled workouts + 5 challenges per group admin (100 each total)
      - 40 users with 1 post each and current-week workouts/logs
    """
    monday, _next_monday = _week_bounds(today)

    # Ensure baseline exercise ids used by generated workout_log rows are available.
    print("-- Ensure baseline exercise rows exist for workout_log FK references.")
    print(
        "INSERT INTO exercise (exercise_id, exercise_name, exercise_muscle_group, exercise_difficulty_level) VALUES "
        "(1, 'Back Squat', 'Legs', 'intermediate'),"
        "(2, 'Bench Press', 'Chest', 'intermediate'),"
        "(3, 'Sit-ups', 'Abs', 'beginner'),"
        "(4, 'Deadlift', 'Back', 'advanced'),"
        "(5, 'Treadmill Run', 'Cardio', 'beginner') "
        "ON DUPLICATE KEY UPDATE "
        "exercise_name = VALUES(exercise_name), "
        "exercise_muscle_group = VALUES(exercise_muscle_group), "
        "exercise_difficulty_level = VALUES(exercise_difficulty_level);"
    )
    print()

    # Pick a stable admin owner for all generated groups.
    print("-- Anchor admin (created if missing) used as motiv_group.admin_id owner.")
    print(
        "INSERT INTO admin (admin_name, admin_first_name, admin_last_name, admin_email, password_hash) "
        "VALUES ('Bulk Anchor Admin', 'Bulk', 'Anchor', 'bulk-anchor-admin@motiv.test', @pw) "
        "ON DUPLICATE KEY UPDATE "
        "admin_name = VALUES(admin_name), "
        "admin_first_name = VALUES(admin_first_name), "
        "admin_last_name = VALUES(admin_last_name), "
        "password_hash = VALUES(password_hash), "
        "admin_id = LAST_INSERT_ID(admin_id);"
    )
    print("SET @bulk_admin_id := LAST_INSERT_ID();")
    print()

    group_vars: list[str] = []

    for ga_idx in range(1, 21):
        ga_email = f"ga-bulk+{ga_idx:04d}@motiv.test"
        ga_name = f"GA Bulk {ga_idx:02d}"
        ga_first = "GA"
        ga_last = f"Bulk{ga_idx:02d}"
        ga_uname = f"ga_bulk_{ga_idx:04d}"

        print(f"-- --- bulk group admin {ga_idx}: {ga_email}")
        print(
            "INSERT INTO group_admin "
            "(group_admin_name, group_admin_first_name, group_admin_last_name, group_admin_email, password_hash) "
            f"VALUES ({_sql_str(ga_name)}, {_sql_str(ga_first)}, {_sql_str(ga_last)}, {_sql_str(ga_email)}, @pw) "
            "ON DUPLICATE KEY UPDATE "
            "group_admin_name = VALUES(group_admin_name), "
            "group_admin_first_name = VALUES(group_admin_first_name), "
            "group_admin_last_name = VALUES(group_admin_last_name), "
            "password_hash = VALUES(password_hash), "
            "group_admin_id = LAST_INSERT_ID(group_admin_id);"
        )
        print("SET @gaid := LAST_INSERT_ID();")

        # Create linked app_user with same email so GA dashboard metrics can resolve workouts by email.
        print(
            "INSERT INTO app_user "
            "(user_name, user_first_name, user_last_name, user_email, password_hash, is_active) "
            f"VALUES ({_sql_str(ga_uname)}, {_sql_str(ga_first)}, {_sql_str(ga_last)}, {_sql_str(ga_email)}, @pw, 1) "
            "ON DUPLICATE KEY UPDATE "
            "user_name = VALUES(user_name), "
            "user_first_name = VALUES(user_first_name), "
            "user_last_name = VALUES(user_last_name), "
            "password_hash = VALUES(password_hash), "
            "is_active = 1, "
            "user_id = LAST_INSERT_ID(user_id);"
        )
        print("SET @ga_uid := LAST_INSERT_ID();")

        # Two groups per GA; capture deterministic SQL variables for later user assignments.
        for local_group_idx in range(1, 3):
            global_group_idx = ((ga_idx - 1) * 2) + local_group_idx
            grp_var = f"@grp_{global_group_idx:03d}"
            group_vars.append(grp_var)
            group_name = f"Bulk GA{ga_idx:02d} Group {local_group_idx}"
            group_desc = (
                f"Synthetic demo group {local_group_idx} for GA {ga_idx:02d} "
                "to validate dashboards, groups, and invites."
            )
            print(
                "INSERT INTO motiv_group "
                "(group_name, group_description, group_date_created, admin_id, group_admin_id) "
                f"VALUES ({_sql_str(group_name)}, {_sql_str(group_desc)}, {_sql_str(today.isoformat())}, @bulk_admin_id, @gaid);"
            )
            print(f"SET {grp_var} := LAST_INSERT_ID();")

        # Five scheduled group workouts per GA (alternating between the GA's two groups).
        for workout_idx in range(1, 6):
            target_group_var = group_vars[-2] if (workout_idx % 2 == 1) else group_vars[-1]
            scheduled_date = monday + timedelta(days=(workout_idx - 1))
            scheduled_time = f"{6 + workout_idx:02d}:00:00"
            workout_title = f"GA{ga_idx:02d} Scheduled Workout {workout_idx}"
            workout_desc = f"Auto-generated scheduled workout {workout_idx} for GA {ga_idx:02d}."
            location = f"Demo Facility {ga_idx:02d}"
            print(
                "INSERT INTO group_workout "
                "(group_workout_title, group_workout_description, group_workout_scheduled_date, "
                "group_workout_scheduled_time, group_workout_start_date, group_workout_end_date, "
                "group_workout_location, group_id, group_admin_id) "
                f"VALUES ({_sql_str(workout_title)}, {_sql_str(workout_desc)}, "
                f"{_sql_str(scheduled_date.isoformat())}, {_sql_str(scheduled_time)}, "
                f"{_sql_str(scheduled_date.isoformat())}, {_sql_str(scheduled_date.isoformat())}, "
                f"{_sql_str(location)}, {target_group_var}, @gaid);"
            )

        # Five challenges per GA (alternating between the GA's two groups).
        for challenge_idx in range(1, 6):
            target_group_var = group_vars[-2] if (challenge_idx % 2 == 1) else group_vars[-1]
            start_date = monday + timedelta(days=(challenge_idx - 1) * 7)
            end_date = start_date + timedelta(days=6)
            challenge_title = f"GA{ga_idx:02d} Challenge {challenge_idx}"
            challenge_goal = f"Complete challenge {challenge_idx} goals for GA {ga_idx:02d} groups."
            challenge_status = "active" if challenge_idx <= 2 else "upcoming"
            print(
                "INSERT INTO challenge "
                "(challenge_title, challenge_date, challenge_start_date, challenge_end_date, "
                "challenge_status, challenge_goal, group_admin_id, group_id) "
                f"VALUES ({_sql_str(challenge_title)}, {_sql_str(start_date.isoformat())}, "
                f"{_sql_str(start_date.isoformat())}, {_sql_str(end_date.isoformat())}, "
                f"{_sql_str(challenge_status)}, {_sql_str(challenge_goal)}, @gaid, {target_group_var});"
            )

        print()

    # 40 users, one per generated group, each with one post and current-week workouts/logs.
    for user_idx in range(1, 41):
        user_email = f"user-bulk+{user_idx:04d}@motiv.test"
        user_name = f"user_bulk_{user_idx:04d}"
        first = "User"
        last = f"Bulk{user_idx:04d}"
        target_group_var = group_vars[user_idx - 1]
        d0 = monday + timedelta(days=(user_idx - 1) % 7)
        d1 = monday + timedelta(days=((user_idx + 2) - 1) % 7)

        print(f"-- --- bulk app user {user_idx}: {user_email}")
        print(
            "INSERT INTO app_user "
            "(user_name, user_first_name, user_last_name, user_email, password_hash, is_active) "
            f"VALUES ({_sql_str(user_name)}, {_sql_str(first)}, {_sql_str(last)}, {_sql_str(user_email)}, @pw, 1) "
            "ON DUPLICATE KEY UPDATE "
            "user_name = VALUES(user_name), "
            "user_first_name = VALUES(user_first_name), "
            "user_last_name = VALUES(user_last_name), "
            "password_hash = VALUES(password_hash), "
            "is_active = 1, "
            "user_id = LAST_INSERT_ID(user_id);"
        )
        print("SET @uid := LAST_INSERT_ID();")

        print(f"INSERT IGNORE INTO user_group (user_id, group_id) VALUES (@uid, {target_group_var});")
        print(
            "INSERT INTO post (post_content, post_photo_path, post_created, post_time, post_date, admin_id, user_id) "
            f"VALUES ({_sql_str(f'Auto post from bulk user {user_idx:04d}')}, NULL, NOW(), NULL, "
            f"{_sql_str(today.isoformat())}, NULL, @uid);"
        )

        # Two current-week workouts + one workout_log each.
        for w_idx, w_date in enumerate((d0, d1), start=1):
            duration = 25 + ((user_idx * 3 + w_idx) % 40)
            ex_id = ((user_idx + w_idx) % 5) + 1
            sets = 3 + ((user_idx + w_idx) % 3)
            reps = 8 + ((user_idx * 2 + w_idx) % 10)
            weight = float(45 + ((user_idx * 7 + w_idx * 9) % 155))
            print(
                "INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id) "
                f"VALUES ({_sql_str(w_date.isoformat())}, {duration}, @uid, NULL);"
            )
            print("SET @wid := LAST_INSERT_ID();")
            print(
                "INSERT INTO workout_log "
                "(workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id) "
                f"VALUES ({sets}, {reps}, {weight:.2f}, @wid, {ex_id});"
            )
        print()


def emit_user_block(i: int, today: date) -> None:
    """Emit INSERT app_user, memberships, workouts+logs, optional post for index i (1-based)."""
    mon, _next_m = _week_bounds(today)
    email = f"bulkdemo+{i:05d}@motiv.test"
    uname = f"bd{i:05d}"
    first = "Bulk"
    last = f"User{i:05d}"
    dur = 30 + (i % 50)

    # Four workout dates: Mon/Tue this week, prior Monday, two weeks ago Wed
    d0 = mon
    d1 = mon + timedelta(days=1)
    d2 = mon - timedelta(days=7)
    d3 = mon - timedelta(days=11)

    print()
    print(f"-- --- synthetic user {i}: {email}")
    print(
        "INSERT INTO app_user "
        "(user_name, user_first_name, user_last_name, user_email, password_hash, is_active) "
        f"VALUES ({_sql_str(uname)}, {_sql_str(first)}, {_sql_str(last)}, "
        f"{_sql_str(email)}, @pw, 1);"
    )
    print("SET @uid := LAST_INSERT_ID();")
    print(
        "INSERT IGNORE INTO user_group (user_id, group_id)\n"
        "SELECT @uid, g.group_id\n"
        "FROM (SELECT group_id FROM motiv_group ORDER BY group_id LIMIT 3) g;"
    )

    def emit_workout(d: date, n_logs: int) -> None:
        wdur = dur + (d.day % 20)
        print(
            "INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id) "
            f"VALUES ({_sql_str(d.isoformat())}, {wdur}, @uid, NULL);"
        )
        print("SET @wid := LAST_INSERT_ID();")
        for ln in range(n_logs):
            ex_id = ((i + ln + d.day) % 5) + 1
            sets = 3 + ((i + ln) % 4)
            reps = 8 + ((i * 3 + ln * 7) % 15)
            wt = float(50 + ((i * 11 + ln) % 180))
            print(
                "INSERT INTO workout_log "
                "(workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id) "
                f"VALUES ({sets}, {reps}, {wt:.2f}, @wid, {ex_id});"
            )

    emit_workout(d0, 2)
    emit_workout(d1, 1)
    emit_workout(d2, 2)
    emit_workout(d3, 1)

    if i % 5 == 0:
        pc = f"Auto post from bulk demo user {i} — logged {dur} min weeks recently."
        print(
            "INSERT INTO post (post_content, post_photo_path, post_created, post_time, post_date, admin_id, user_id) "
            f"VALUES ({_sql_str(pc)}, NULL, NOW(), NULL, {_sql_str(today.isoformat())}, NULL, @uid);"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print MySQL bulk INSERT script for Motiv demo data (stdout). "
            "Supports synthetic app users (--scenario users) and fixed-size "
            "group-admin expansion topology (--scenario ga-expansion)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python3 scripts/generate_bulk_demo_seed.py --count 75 > /tmp/bulk75.sql\n"
            "  python3 scripts/generate_bulk_demo_seed.py --scenario ga-expansion > /tmp/ga_expansion.sql\n"
            "  # Review /tmp/bulk75.sql, then run in MySQL Workbench against motivdata.\n"
            "\n"
            "--scenario users: --count is clamped to 50–100 (default 75).\n"
            "--scenario ga-expansion: emits fixed 20 GA + 40 user topology.\n"
            "\n"
            "Login: bulkdemo+00001@motiv.test / password123 (same as seed accounts)\n"
            "\n"
            "Safety: no DELETE/TRUNCATE; uses bulkdemo+*****@motiv.test namespace only."
        ),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=75,
        metavar="N",
        help="number of app_user rows to generate (clamped to 50–100, default 75)",
    )
    parser.add_argument(
        "--scenario",
        choices=("users", "ga-expansion"),
        default="users",
        help=(
            "generation scenario: 'users' (default synthetic app users) or "
            "'ga-expansion' (20 group admins, 40 groups, 40 users + related records)"
        ),
    )
    args = parser.parse_args()
    today = date.today()

    print("-- Generated by scripts/generate_bulk_demo_seed.py")
    print("-- Review before execute. On failure: ROLLBACK;")
    print("USE motivdata;")
    print("START TRANSACTION;")
    print()
    print(f"SET @pw := {_sql_str(PW_HASH)};")
    print()
    if args.scenario == "users":
        raw_n = int(args.count)
        n = max(50, min(100, raw_n))
        if n != raw_n:
            print(
                f"-- NOTE: --count {raw_n} clamped to {n} (allowed range 50–100)",
                file=sys.stderr,
            )
        print("-- Scenario: users")
        print("-- Requires at least one motiv_group row and exercise ids 1..5.")
        for i in range(1, n + 1):
            emit_user_block(i, today)
    else:
        print("-- Scenario: ga-expansion")
        print("-- Expected inserts: 20 group_admin, 20 GA-linked app_user, 40 motiv_group,")
        print("-- 100 group_workout (scheduled), 100 challenge, 40 app_user,")
        print("-- 40 user_group memberships, 40 post, 80 workout, 80 workout_log.")
        emit_ga_expansion_block(today)

    print()
    print("-- Validation checks after COMMIT (run manually):")
    print(
        "-- SELECT COUNT(*) AS ga_count FROM group_admin WHERE group_admin_email LIKE 'ga-bulk+%@motiv.test';"
    )
    print(
        "-- SELECT COUNT(*) AS ga_linked_users FROM app_user WHERE user_email LIKE 'ga-bulk+%@motiv.test';"
    )
    print(
        "-- SELECT COUNT(*) AS bulk_groups FROM motiv_group WHERE group_name LIKE 'Bulk GA% Group %';"
    )
    print(
        "-- SELECT COUNT(*) AS bulk_users FROM app_user WHERE user_email LIKE 'user-bulk+%@motiv.test';"
    )
    print(
        "-- SELECT COUNT(*) AS bulk_user_posts FROM post p JOIN app_user u ON u.user_id = p.user_id "
        "WHERE u.user_email LIKE 'user-bulk+%@motiv.test';"
    )
    print(
        "-- SELECT COUNT(*) AS bulk_week_workouts FROM workout w JOIN app_user u ON u.user_id = w.user_id "
        "WHERE u.user_email LIKE 'user-bulk+%@motiv.test' "
        "AND w.workout_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY) "
        "AND w.workout_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY);"
    )
    print("COMMIT;")
    return 0


if __name__ == "__main__":
    sys.exit(main())
