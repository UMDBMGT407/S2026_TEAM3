"""
Motiv — Flask + MySQL (flask-mysqldb).
BMGT407-style: cursor → execute → commit → close; JSON CRUD for posts/workouts/exercises.

Setup (see BMGT407 Server-Side Guide):
  python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
  pip install -r requirements.txt
  On macOS if mysqlclient fails: brew install mysql pkg-config
  Copy .env.example to .env and set MYSQL_PASSWORD (and optional SECRET_KEY).
  In MySQL Workbench, run sql/motivdata_schema.sql then sql/motivdata_seed.sql
  (seed password for all demo accounts: password123).
  For user→group-admin promotion, run sql/migration_app_user_is_active.sql once on existing DBs.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    from dotenv import load_dotenv

    # Load from project root (folder containing app.py), not only the shell cwd.
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from flask import Flask, abort, jsonify, redirect, render_template, request, session
from flask_mysqldb import MySQL
from MySQLdb import OperationalError
from MySQLdb.cursors import DictCursor
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(
    __name__,
    template_folder="Templates",
    static_folder="Static",
    static_url_path="/Static",
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD", "")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB", "motivdata")

mysql = MySQL(app)

# Pages under /Admin/ that do not require platform admin session (login + register).
ADMIN_PUBLIC_PAGES = frozenset({"index.html", "CreateAccount.html"})


def safe_next_url(nxt: str | None) -> str | None:
    if not nxt or not isinstance(nxt, str):
        return None
    nxt = nxt.strip()
    if not nxt.startswith("/") or nxt.startswith("//"):
        return None
    if not (
        nxt.startswith("/Admin/")
        or nxt.startswith("/User/")
        or nxt.startswith("/GroupAdmin/")
    ):
        return None
    return nxt


def next_url_allowed_for_role(nxt: str | None, role: str | None) -> bool:
    """Whether a logged-in user with role may be redirected to nxt (open redirect guard + role match)."""
    if not nxt:
        return True
    path = nxt.split("?", 1)[0]
    if path.startswith("/Admin/"):
        fn = path.removeprefix("/Admin/").split("/")[-1]
        if fn in ADMIN_PUBLIC_PAGES:
            return True
        return role == "admin"
    if path.startswith("/User/"):
        return role == "user"
    if path.startswith("/GroupAdmin/"):
        return role == "group_admin"
    return True


def redirect_to_login_with_next(access_denied: bool = False) -> Any:
    q = f"?next={quote(request.path, safe='/')}"
    if access_denied:
        q += "&error=denied"
    return redirect(f"/Admin/index.html{q}")


def default_dashboard_for_role(role: str) -> str:
    if role == "admin":
        return "/Admin/ADash.html"
    if role == "group_admin":
        return "/GroupAdmin/GADash.html"
    return "/User/UDash.html"


def require_roles(*roles: str):
    """BMGT407-style gate: session role must be one of *roles, else login with ?next=."""

    allowed = frozenset(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if session.get("role") not in allowed:
                denied = session.get("role") is not None
                return redirect_to_login_with_next(access_denied=denied)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


# Older name kept so a half-merged file or @require_session_role(...) still loads.
require_session_role = require_roles


def fetch_app_user_for_login(cur, email: str):
    """Return app_user row if password login should succeed (active users only)."""
    try:
        cur.execute(
            "SELECT * FROM app_user WHERE user_email = %s AND is_active = 1",
            (email,),
        )
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cur.execute("SELECT * FROM app_user WHERE user_email = %s", (email,))
    return cur.fetchone()


def allowed_page(filename: str) -> bool:
    if ".." in filename or not filename.endswith(".html") or "/" in filename:
        return False
    return True


def dict_cursor():
    return mysql.connection.cursor(DictCursor)


def serialize_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def parse_date(s: str | None):
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.strptime(s, "%B %d %Y").date()
    except ValueError:
        return None


def parse_int(s: Any, default: int | None = None):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def get_or_create_exercise(cur, name: str, muscle: str | None, difficulty: str | None) -> int:
    name = (name or "").strip() or "Custom"
    cur.execute(
        "SELECT exercise_id FROM exercise WHERE exercise_name = %s LIMIT 1",
        (name,),
    )
    r = cur.fetchone()
    if r:
        return r["exercise_id"] if isinstance(r, dict) else r[0]  # type: ignore[index]
    cur.execute(
        """INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
           VALUES (%s, %s, %s)""",
        (name, muscle or None, difficulty or None),
    )
    return cur.lastrowid


def _offline_page_context(base: dict) -> dict:
    """If MySQL is unreachable, still render pages with empty data."""
    base.update(
        {
            "posts": [],
            "workouts": [],
            "schedules": [],
            "all_groups": [],
            "admin_groups": [],
            "admin_sessions": [],
            "admin_challenges": [],
            "groups": [],
            "admins": [],
            "app_users": [],
            "edit_group": None,
            "edit_session": None,
            "edit_challenge_admin": None,
            "edit_challenge": None,
            "edit_workout": None,
            "edit_ga_group": None,
            "edit_w": None,
            "edit_log": None,
            "edit_ex": None,
            "admin_me": None,
            "user_me": None,
            "ga_me": None,
            "ga_created_groups": [],
            "ga_schedule_sessions": [],
            "ga_created_challenges": [],
            "selected_challenge_id": None,
            "selected_challenge_name": None,
            "selected_challenge_participants": [],
            "selected_workout_id": None,
            "selected_workout": None,
            "selected_workout_attendance": [],
            "selected_group_id": None,
            "selected_group_name": None,
            "selected_group_members": [],
            "admin_user_count": 0,
            "admin_group_count": 0,
            "admin_post_count": 0,
            "admin_workouts_logged_count": 0,
            "admin_sets_done_count": 0,
            "admin_exercises_done_count": 0,
            "admin_reps_done_count": 0,
        }
    )
    return base


def build_template_context(subdir: str, filename: str) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "session_role": session.get("role"),
        "session_email": session.get("email"),
        "session_id": session.get("id"),
    }
    path = f"{subdir}/{filename}"
    try:
        cur = dict_cursor()
    except Exception:
        return _offline_page_context(ctx)
    try:
        if path in ("User/PU.html", "GroupAdmin/post-GA.html", "Admin/PostA.html"):
            cur.execute(
                """
                SELECT p.post_id, p.post_content, p.post_created, u.user_email, p.user_id
                FROM post p
                JOIN app_user u ON p.user_id = u.user_id
                ORDER BY p.post_created DESC
                """
            )
            # Temporary UI requirement: show exactly first 4 shared posts.
            ctx["posts"] = cur.fetchall()[:4]
        elif path == "User/WLU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            if uid:
                cur.execute(
                    """
                    SELECT workout_id, workout_date, workout_duration_minutes
                    FROM workout WHERE user_id = %s
                    ORDER BY workout_date DESC, workout_id DESC
                    """,
                    (uid,),
                )
                ctx["workouts"] = cur.fetchall()
            else:
                ctx["workouts"] = []
        elif path == "User/SU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            if uid:
                cur.execute(
                    """
                    SELECT gw.group_workout_id, gw.group_workout_title,
                           gw.group_workout_scheduled_date, gw.group_workout_location,
                           g.group_name
                    FROM group_workout gw
                    JOIN motiv_group g ON gw.group_id = g.group_id
                    JOIN user_group ug ON ug.group_id = g.group_id
                    WHERE ug.user_id = %s
                    ORDER BY gw.group_workout_scheduled_date DESC
                    """,
                    (uid,),
                )
                ctx["schedules"] = cur.fetchall()
            else:
                ctx["schedules"] = []
        elif path == "Admin/ADash.html":
            ctx["admin_user_count"] = 0
            ctx["admin_group_count"] = 0
            ctx["admin_post_count"] = 0
            ctx["admin_workouts_logged_count"] = 0
            ctx["admin_sets_done_count"] = 0
            ctx["admin_exercises_done_count"] = 0
            ctx["admin_reps_done_count"] = 0
            try:
                cur.execute("SELECT COUNT(*) AS c FROM app_user WHERE is_active = 1")
                row = cur.fetchone()
                ctx["admin_user_count"] = (row or {}).get("c", 0)
            except OperationalError as e:
                if e.args[0] == 1054:
                    cur.execute("SELECT COUNT(*) AS c FROM app_user")
                    row = cur.fetchone()
                    ctx["admin_user_count"] = (row or {}).get("c", 0)
            try:
                cur.execute("SELECT COUNT(*) AS c FROM motiv_group")
                row = cur.fetchone()
                ctx["admin_group_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute("SELECT COUNT(*) AS c FROM post")
                row = cur.fetchone()
                ctx["admin_post_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute("SELECT COUNT(*) AS c FROM workout")
                row = cur.fetchone()
                ctx["admin_workouts_logged_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute("SELECT COALESCE(SUM(workout_num_sets), 0) AS c FROM workout_log")
                row = cur.fetchone()
                ctx["admin_sets_done_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute("SELECT COUNT(DISTINCT exercise_id) AS c FROM workout_log")
                row = cur.fetchone()
                ctx["admin_exercises_done_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute("SELECT COALESCE(SUM(workout_num_reps), 0) AS c FROM workout_log")
                row = cur.fetchone()
                ctx["admin_reps_done_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
        elif path == "Admin/GroupA.html":
            ctx["selected_group_id"] = None
            ctx["selected_group_name"] = None
            ctx["selected_group_members"] = []
            cur.execute(
                """
                SELECT g.group_id, g.group_name,
                  CONCAT(ga.group_admin_first_name, ' ', ga.group_admin_last_name) AS ga_name,
                  (SELECT COUNT(*) FROM user_group ug WHERE ug.group_id = g.group_id) AS member_count
                FROM motiv_group g
                JOIN group_admin ga ON g.group_admin_id = ga.group_admin_id
                ORDER BY g.group_id
                """
            )
            admin_groups = cur.fetchall()
            ctx["admin_groups"] = admin_groups
            if admin_groups:
                selected_group_id = request.args.get("group_id", type=int)
                valid_group_ids = {g["group_id"] for g in admin_groups}
                if selected_group_id not in valid_group_ids:
                    selected_group_id = admin_groups[0]["group_id"]

                ctx["selected_group_id"] = selected_group_id
                cur.execute(
                    """
                    SELECT g.group_name, ga.group_admin_id,
                      ga.group_admin_first_name, ga.group_admin_last_name, ga.group_admin_email
                    FROM motiv_group g
                    JOIN group_admin ga ON ga.group_admin_id = g.group_admin_id
                    WHERE g.group_id = %s
                    LIMIT 1
                    """,
                    (selected_group_id,),
                )
                selected_group = cur.fetchone()
                if selected_group:
                    ctx["selected_group_name"] = selected_group["group_name"]
                    selected_members = [
                        {
                            "member_kind": "group_admin",
                            "member_id_label": f"#GA{selected_group['group_admin_id']}",
                            "member_name": f"{selected_group['group_admin_first_name']} {selected_group['group_admin_last_name']}",
                            "member_role": "Group Admin",
                            "member_email": selected_group["group_admin_email"],
                        }
                    ]
                    cur.execute(
                        """
                        SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email
                        FROM user_group ug
                        JOIN app_user u ON u.user_id = ug.user_id
                        WHERE ug.group_id = %s
                        ORDER BY u.user_first_name, u.user_last_name, u.user_id
                        """,
                        (selected_group_id,),
                    )
                    for u in cur.fetchall():
                        selected_members.append(
                            {
                                "member_kind": "app_user",
                                "user_id": u["user_id"],
                                "member_id_label": f"#U{u['user_id']}",
                                "member_name": f"{u['user_first_name']} {u['user_last_name']}",
                                "member_role": "Member",
                                "member_email": u["user_email"],
                            }
                        )
                    ctx["selected_group_members"] = selected_members
        elif path == "Admin/ChallengeA.html":
            ctx["selected_workout_id"] = None
            ctx["selected_workout"] = None
            ctx["selected_workout_attendance"] = []
            cur.execute(
                """
                SELECT gw.group_workout_id, gw.group_workout_title, g.group_id, g.group_name,
                  gw.group_workout_scheduled_date, gw.group_workout_location
                FROM group_workout gw
                JOIN motiv_group g ON gw.group_id = g.group_id
                ORDER BY gw.group_workout_scheduled_date DESC, gw.group_workout_id DESC
                """
            )
            admin_sessions = cur.fetchall()
            ctx["admin_sessions"] = admin_sessions
            if admin_sessions:
                selected_workout_id = request.args.get("workout_id", type=int)
                valid_workout_ids = {s["group_workout_id"] for s in admin_sessions}
                if selected_workout_id not in valid_workout_ids:
                    selected_workout_id = admin_sessions[0]["group_workout_id"]
                ctx["selected_workout_id"] = selected_workout_id

                cur.execute(
                    """
                    SELECT gw.group_workout_id, gw.group_workout_title, gw.group_workout_scheduled_date,
                      gw.group_workout_start_date, gw.group_workout_end_date, gw.group_workout_location,
                      gw.group_id, g.group_name
                    FROM group_workout gw
                    JOIN motiv_group g ON g.group_id = gw.group_id
                    WHERE gw.group_workout_id = %s
                    LIMIT 1
                    """,
                    (selected_workout_id,),
                )
                selected_workout = cur.fetchone()
                if selected_workout:
                    ctx["selected_workout"] = selected_workout
                    cur.execute(
                        """
                        SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email,
                          CASE WHEN EXISTS (
                              SELECT 1 FROM workout w
                              WHERE w.group_workout_id = %s AND w.user_id = u.user_id
                          ) THEN 'Going' ELSE 'Pending' END AS attendance_status
                        FROM user_group ug
                        JOIN app_user u ON u.user_id = ug.user_id
                        WHERE ug.group_id = %s
                        ORDER BY u.user_first_name, u.user_last_name, u.user_id
                        """,
                        (selected_workout_id, selected_workout["group_id"]),
                    )
                    ctx["selected_workout_attendance"] = cur.fetchall()
        elif path == "Admin/ScheduleA.html":
            ctx["selected_challenge_id"] = None
            ctx["selected_challenge_name"] = None
            ctx["selected_challenge_participants"] = []
            cur.execute(
                """
                SELECT c.challenge_id, c.challenge_title, c.challenge_status,
                  c.challenge_start_date, c.challenge_end_date, c.challenge_goal,
                  g.group_id, g.group_name
                FROM challenge c
                JOIN motiv_group g ON c.group_id = g.group_id
                ORDER BY c.challenge_id
                """
            )
            admin_challenges = cur.fetchall()
            ctx["admin_challenges"] = admin_challenges
            if admin_challenges:
                selected_challenge_id = request.args.get("challenge_id", type=int)
                valid_challenge_ids = {c["challenge_id"] for c in admin_challenges}
                if selected_challenge_id not in valid_challenge_ids:
                    selected_challenge_id = admin_challenges[0]["challenge_id"]
                ctx["selected_challenge_id"] = selected_challenge_id

                selected_challenge = next(
                    (c for c in admin_challenges if c["challenge_id"] == selected_challenge_id),
                    None,
                )
                if selected_challenge:
                    ctx["selected_challenge_name"] = selected_challenge["challenge_title"]
                    cur.execute(
                        """
                        SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email
                        FROM user_group ug
                        JOIN app_user u ON u.user_id = ug.user_id
                        WHERE ug.group_id = %s
                        ORDER BY u.user_first_name, u.user_last_name, u.user_id
                        """,
                        (selected_challenge["group_id"],),
                    )
                    participants = []
                    for idx, u in enumerate(cur.fetchall(), start=1):
                        participants.append(
                            {
                                "member_id_label": f"#U{u['user_id']}",
                                "member_name": f"{u['user_first_name']} {u['user_last_name']}",
                                "rank": idx,
                                "goal_progress": "—",
                            }
                        )
                    ctx["selected_challenge_participants"] = participants
        elif path in (
            "GroupAdmin/challenge-creation-GA.html",
            "GroupAdmin/edit-challenge-GA.html",
        ):
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            if ga_id:
                cur.execute(
                    "SELECT group_id, group_name FROM motiv_group WHERE group_admin_id = %s",
                    (ga_id,),
                )
                ctx["groups"] = cur.fetchall()
            else:
                ctx["groups"] = []
            cid = request.args.get("id", type=int)
            ctx["edit_challenge"] = None
            if cid and path == "GroupAdmin/edit-challenge-GA.html":
                cur.execute(
                    "SELECT * FROM challenge WHERE challenge_id = %s AND group_admin_id = %s",
                    (cid, ga_id),
                )
                ctx["edit_challenge"] = cur.fetchone()
        elif path in (
            "GroupAdmin/create-schedule-GA.html",
            "GroupAdmin/edit-schedule-GA.html",
        ):
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            if ga_id:
                cur.execute(
                    "SELECT group_id, group_name FROM motiv_group WHERE group_admin_id = %s",
                    (ga_id,),
                )
                ctx["groups"] = cur.fetchall()
            else:
                ctx["groups"] = []
            wid = request.args.get("id", type=int)
            ctx["edit_workout"] = None
            if wid and path == "GroupAdmin/edit-schedule-GA.html":
                cur.execute(
                    """SELECT * FROM group_workout
                       WHERE group_workout_id = %s AND group_admin_id = %s""",
                    (wid, ga_id),
                )
                ctx["edit_workout"] = cur.fetchone()
        elif path == "GroupAdmin/scheduling-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["selected_workout_id"] = None
            ctx["selected_workout"] = None
            ctx["selected_workout_attendance"] = []
            if ga_id:
                cur.execute(
                    """
                    SELECT gw.group_workout_id, gw.group_workout_title, g.group_name,
                      gw.group_workout_scheduled_date, gw.group_workout_location
                    FROM group_workout gw
                    JOIN motiv_group g ON gw.group_id = g.group_id
                    WHERE gw.group_admin_id = %s
                    ORDER BY (gw.group_workout_scheduled_date IS NULL),
                             gw.group_workout_scheduled_date DESC,
                             gw.group_workout_id DESC
                    """,
                    (ga_id,),
                )
                ga_sessions = cur.fetchall()
                ctx["ga_schedule_sessions"] = ga_sessions
                if ga_sessions:
                    selected_workout_id = request.args.get("workout_id", type=int)
                    valid_workout_ids = {s["group_workout_id"] for s in ga_sessions}
                    if selected_workout_id not in valid_workout_ids:
                        selected_workout_id = ga_sessions[0]["group_workout_id"]
                    ctx["selected_workout_id"] = selected_workout_id

                    cur.execute(
                        """
                        SELECT gw.group_workout_id, gw.group_workout_title, gw.group_workout_scheduled_date,
                          gw.group_workout_start_date, gw.group_workout_end_date, gw.group_workout_location,
                          gw.group_id, g.group_name
                        FROM group_workout gw
                        JOIN motiv_group g ON g.group_id = gw.group_id
                        WHERE gw.group_workout_id = %s AND gw.group_admin_id = %s
                        """,
                        (selected_workout_id, ga_id),
                    )
                    selected_workout = cur.fetchone()
                    if selected_workout:
                        ctx["selected_workout"] = selected_workout
                        cur.execute(
                            """
                            SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email,
                              CASE WHEN EXISTS (
                                  SELECT 1 FROM workout w
                                  WHERE w.group_workout_id = %s AND w.user_id = u.user_id
                              ) THEN 'Going' ELSE 'Pending' END AS attendance_status
                            FROM user_group ug
                            JOIN app_user u ON u.user_id = ug.user_id
                            WHERE ug.group_id = %s
                            ORDER BY u.user_first_name, u.user_last_name, u.user_id
                            """,
                            (selected_workout_id, selected_workout["group_id"]),
                        )
                        ctx["selected_workout_attendance"] = cur.fetchall()
            else:
                ctx["ga_schedule_sessions"] = []
        elif path == "GroupAdmin/created-challenges-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["selected_challenge_id"] = None
            ctx["selected_challenge_name"] = None
            ctx["selected_challenge_participants"] = []
            if ga_id:
                cur.execute(
                    """
                    SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                      c.challenge_end_date, c.challenge_status, c.challenge_goal,
                      c.group_id, g.group_name
                    FROM challenge c
                    JOIN motiv_group g ON c.group_id = g.group_id
                    WHERE c.group_admin_id = %s
                    ORDER BY (c.challenge_start_date IS NULL),
                             c.challenge_start_date DESC,
                             c.challenge_id DESC
                    """,
                    (ga_id,),
                )
                ga_challenges = cur.fetchall()
                ctx["ga_created_challenges"] = ga_challenges
                if ga_challenges:
                    selected_challenge_id = request.args.get("challenge_id", type=int)
                    valid_challenge_ids = {c["challenge_id"] for c in ga_challenges}
                    if selected_challenge_id not in valid_challenge_ids:
                        selected_challenge_id = ga_challenges[0]["challenge_id"]
                    ctx["selected_challenge_id"] = selected_challenge_id
                    selected_challenge = next(
                        (c for c in ga_challenges if c["challenge_id"] == selected_challenge_id),
                        None,
                    )
                    if selected_challenge:
                        ctx["selected_challenge_name"] = selected_challenge["challenge_title"]
                        cur.execute(
                            """
                            SELECT u.user_first_name, u.user_last_name, u.user_email
                            FROM user_group ug
                            JOIN app_user u ON u.user_id = ug.user_id
                            WHERE ug.group_id = %s
                            ORDER BY u.user_first_name, u.user_last_name, u.user_id
                            """,
                            (selected_challenge["group_id"],),
                        )
                        participants = []
                        for idx, u in enumerate(cur.fetchall(), start=1):
                            participants.append(
                                {
                                    "member_name": f"{u['user_first_name']} {u['user_last_name']}",
                                    "member_email": u["user_email"],
                                    "rank": idx,
                                    "goal_progress": "—",
                                }
                            )
                        ctx["selected_challenge_participants"] = participants
            else:
                ctx["ga_created_challenges"] = []
        elif path == "GroupAdmin/created-groups-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["selected_group_id"] = None
            ctx["selected_group_name"] = None
            ctx["selected_group_members"] = []
            if ga_id:
                cur.execute(
                    """
                    SELECT g.group_id, g.group_name,
                      (SELECT COUNT(*) FROM user_group ug WHERE ug.group_id = g.group_id) AS member_count
                    FROM motiv_group g
                    WHERE g.group_admin_id = %s
                    ORDER BY g.group_name, g.group_id
                    """,
                    (ga_id,),
                )
                ga_groups = cur.fetchall()
                ctx["ga_created_groups"] = ga_groups

                if ga_groups:
                    selected_group_id = request.args.get("group_id", type=int)
                    valid_group_ids = {g["group_id"] for g in ga_groups}
                    if selected_group_id not in valid_group_ids:
                        selected_group_id = ga_groups[0]["group_id"]

                    ctx["selected_group_id"] = selected_group_id
                    cur.execute(
                        """
                        SELECT g.group_name, ga.group_admin_first_name, ga.group_admin_last_name, ga.group_admin_email
                        FROM motiv_group g
                        JOIN group_admin ga ON ga.group_admin_id = g.group_admin_id
                        WHERE g.group_id = %s AND g.group_admin_id = %s
                        """,
                        (selected_group_id, ga_id),
                    )
                    selected_group = cur.fetchone()
                    if selected_group:
                        ctx["selected_group_name"] = selected_group["group_name"]
                        selected_members = [
                            {
                                "member_kind": "group_admin",
                                "member_id_label": f"#GA{ga_id}",
                                "member_name": f"{selected_group['group_admin_first_name']} {selected_group['group_admin_last_name']}",
                                "member_role": "Group Admin",
                                "member_email": selected_group["group_admin_email"],
                            }
                        ]
                        cur.execute(
                            """
                            SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email
                            FROM user_group ug
                            JOIN app_user u ON u.user_id = ug.user_id
                            WHERE ug.group_id = %s
                            ORDER BY u.user_first_name, u.user_last_name, u.user_id
                            """,
                            (selected_group_id,),
                        )
                        for u in cur.fetchall():
                            selected_members.append(
                                {
                                    "member_kind": "app_user",
                                    "user_id": u["user_id"],
                                    "member_id_label": f"#U{u['user_id']}",
                                    "member_name": f"{u['user_first_name']} {u['user_last_name']}",
                                    "member_role": "Member",
                                    "member_email": u["user_email"],
                                }
                            )
                        ctx["selected_group_members"] = selected_members
            else:
                ctx["ga_created_groups"] = []
        elif path == "GroupAdmin/group-creation-GA.html":
            cur.execute(
                "SELECT admin_id, admin_first_name, admin_last_name, admin_email FROM admin"
            )
            ctx["admins"] = cur.fetchall()
        elif path in (
            "GroupAdmin/workout-logging-GA.html",
            "GroupAdmin/edit-workout-logging-GA.html",
        ):
            try:
                cur.execute(
                    """SELECT user_id, user_first_name, user_last_name, user_email
                       FROM app_user WHERE is_active = 1"""
                )
            except OperationalError as e:
                if e.args[0] != 1054:
                    raise
                cur.execute(
                    "SELECT user_id, user_first_name, user_last_name, user_email FROM app_user"
                )
            ctx["app_users"] = cur.fetchall()
        elif path == "User/WLEU.html":
            wid = request.args.get("id", type=int)
            ctx["edit_w"] = None
            ctx["edit_log"] = None
            ctx["edit_ex"] = None
            uid = session.get("id") if session.get("role") == "user" else None
            if wid and uid:
                cur.execute(
                    "SELECT * FROM workout WHERE workout_id = %s AND user_id = %s",
                    (wid, uid),
                )
                ctx["edit_w"] = cur.fetchone()
                if ctx["edit_w"]:
                    cur.execute(
                        "SELECT * FROM workout_log WHERE workout_id = %s LIMIT 1",
                        (wid,),
                    )
                    ctx["edit_log"] = cur.fetchone()
                    if ctx["edit_log"]:
                        eid = ctx["edit_log"]["exercise_id"]
                        cur.execute(
                            "SELECT * FROM exercise WHERE exercise_id = %s", (eid,)
                        )
                        ctx["edit_ex"] = cur.fetchone()
        elif path == "Admin/GroupAed.html":
            gid = request.args.get("id", type=int)
            ctx["edit_group"] = None
            if gid:
                cur.execute("SELECT * FROM motiv_group WHERE group_id = %s", (gid,))
                ctx["edit_group"] = cur.fetchone()
        elif path == "Admin/ChallengeAed.html":
            wid = request.args.get("id", type=int)
            ctx["edit_session"] = None
            if wid:
                cur.execute(
                    "SELECT * FROM group_workout WHERE group_workout_id = %s", (wid,)
                )
                ctx["edit_session"] = cur.fetchone()
        elif path == "Admin/ScheduleAed.html":
            cid = request.args.get("id", type=int)
            ctx["edit_challenge_admin"] = None
            if cid:
                cur.execute("SELECT * FROM challenge WHERE challenge_id = %s", (cid,))
                ctx["edit_challenge_admin"] = cur.fetchone()
        elif path == "Admin/AProfile.html":
            ctx["admin_me"] = None
            if session.get("role") == "admin":
                cur.execute(
                    "SELECT * FROM admin WHERE admin_id = %s", (session["id"],)
                )
                ctx["admin_me"] = cur.fetchone()
        elif path == "User/ProU.html":
            ctx["user_me"] = None
            if session.get("role") == "user":
                cur.execute(
                    "SELECT * FROM app_user WHERE user_id = %s", (session["id"],)
                )
                ctx["user_me"] = cur.fetchone()
        elif path == "GroupAdmin/profile-GA.html":
            ctx["ga_me"] = None
            if session.get("role") == "group_admin":
                cur.execute(
                    "SELECT * FROM group_admin WHERE group_admin_id = %s",
                    (session["id"],),
                )
                ctx["ga_me"] = cur.fetchone()
        elif path == "GroupAdmin/edit-group-GA.html":
            ctx["edit_ga_group"] = None
            gid = request.args.get("id", type=int)
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            if gid and ga_id:
                cur.execute(
                    """SELECT * FROM motiv_group
                       WHERE group_id = %s AND group_admin_id = %s""",
                    (gid, ga_id),
                )
                ctx["edit_ga_group"] = cur.fetchone()
    finally:
        cur.close()
    return ctx


@app.route("/")
def root():
    # Serve login page directly so hitting base URL never appears blank.
    return admin_page("index.html")


@app.route("/Admin/<path:filename>")
def admin_page(filename):
    if not allowed_page(filename):
        abort(404)
    if filename not in ADMIN_PUBLIC_PAGES and session.get("role") != "admin":
        denied = session.get("role") is not None
        return redirect_to_login_with_next(access_denied=denied)
    ctx = build_template_context("Admin", filename)
    if filename == "index.html":
        ctx["login_next"] = safe_next_url(request.args.get("next"))
        ctx["login_error"] = request.args.get("error") == "1"
        ctx["login_denied"] = request.args.get("error") == "denied"
    return render_template(f"Admin/{filename}", **ctx)


@app.route("/User/<path:filename>")
@require_roles("user")
def user_page(filename):
    if not allowed_page(filename):
        abort(404)
    ctx = build_template_context("User", filename)
    return render_template(f"User/{filename}", **ctx)


@app.route("/GroupAdmin/<path:filename>")
@require_roles("group_admin")
def groupadmin_page(filename):
    if not allowed_page(filename):
        abort(404)
    ctx = build_template_context("GroupAdmin", filename)
    return render_template(f"GroupAdmin/{filename}", **ctx)


# --- Auth (form POST) ---


@app.post("/auth/login")
def auth_login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = safe_next_url(request.form.get("next"))
    cur = dict_cursor()
    try:
        cur.execute("SELECT * FROM admin WHERE admin_email = %s", (email,))
        row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["role"] = "admin"
            session["id"] = row["admin_id"]
            session["email"] = email
            if next_url and not next_url_allowed_for_role(next_url, "admin"):
                return redirect("/Admin/index.html?error=denied")
            return redirect(next_url or default_dashboard_for_role("admin"))
        cur.execute(
            "SELECT * FROM group_admin WHERE group_admin_email = %s", (email,)
        )
        row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["role"] = "group_admin"
            session["id"] = row["group_admin_id"]
            session["email"] = email
            if next_url and not next_url_allowed_for_role(next_url, "group_admin"):
                return redirect("/Admin/index.html?error=denied")
            return redirect(next_url or default_dashboard_for_role("group_admin"))
        row = fetch_app_user_for_login(cur, email)
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["role"] = "user"
            session["id"] = row["user_id"]
            session["email"] = email
            if next_url and not next_url_allowed_for_role(next_url, "user"):
                return redirect("/Admin/index.html?error=denied")
            return redirect(next_url or default_dashboard_for_role("user"))
    finally:
        cur.close()
    loc = "/Admin/index.html?error=1"
    if next_url:
        loc = f"{loc}&next={quote(next_url, safe='/')}"
    return redirect(loc)


@app.post("/auth/register")
def auth_register():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    if not all([email, password, first, last]):
        return redirect("/Admin/CreateAccount.html?error=1")
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            """INSERT INTO app_user
               (user_name, user_first_name, user_last_name, user_email, password_hash)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                f"{first} {last}",
                first,
                last,
                email,
                generate_password_hash(password),
            ),
        )
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        return redirect("/Admin/CreateAccount.html?error=2")
    cur.close()
    return redirect("/Admin/index.html?registered=1")


@app.post("/auth/logout")
def auth_logout():
    session.clear()
    return redirect("/Admin/index.html")


# --- Group Admin actions ---


@app.post("/actions/group-admin/group")
def ga_create_group():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/group-creation-GA.html")
    name = request.form.get("group_name", "").strip()
    desc = request.form.get("group_description", "").strip()
    ga_id = session["id"]
    if not name:
        return redirect("/GroupAdmin/group-creation-GA.html?err=1")
    cur = mysql.connection.cursor()
    admin_id = parse_int(request.form.get("admin_id"))
    if not admin_id:
        # Group admins do not pick directors; infer one safely.
        cur.execute(
            "SELECT admin_id FROM motiv_group WHERE group_admin_id = %s LIMIT 1", (ga_id,)
        )
        row = cur.fetchone()
        admin_id = row[0] if row else None
    if not admin_id:
        cur.execute("SELECT admin_id FROM admin ORDER BY admin_id LIMIT 1")
        row = cur.fetchone()
        admin_id = row[0] if row else None
    if not admin_id:
        cur.close()
        return redirect("/GroupAdmin/group-creation-GA.html?err=admin")
    cur.execute(
        """INSERT INTO motiv_group
           (group_name, group_description, group_date_created, admin_id, group_admin_id)
           VALUES (%s, %s, CURDATE(), %s, %s)""",
        (name, desc, admin_id, ga_id),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/created-groups-GA.html")


@app.post("/actions/group-admin/group/<int:group_id>/edit")
def ga_edit_group(group_id):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-groups-GA.html")
    name = request.form.get("group_name", "").strip()
    desc = request.form.get("group_description", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE motiv_group SET group_name = %s, group_description = %s
           WHERE group_id = %s AND group_admin_id = %s""",
        (name, desc, group_id, session["id"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/created-groups-GA.html")


@app.post("/actions/group-admin/remove-group-member")
def ga_remove_group_member():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-groups-GA.html")
    gid = parse_int(request.form.get("group_id"))
    uid = parse_int(request.form.get("user_id"))
    if not gid or not uid:
        return redirect("/GroupAdmin/created-groups-GA.html")
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT 1 FROM motiv_group
           WHERE group_id = %s AND group_admin_id = %s LIMIT 1""",
        (gid, session["id"]),
    )
    if not cur.fetchone():
        cur.close()
        return redirect("/GroupAdmin/created-groups-GA.html?err=1")
    cur.execute(
        "DELETE FROM user_group WHERE user_id = %s AND group_id = %s",
        (uid, gid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect(f"/GroupAdmin/created-groups-GA.html?group_id={gid}")


@app.post("/actions/group-admin/challenge")
def ga_create_challenge():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/challenge-creation-GA.html")
    title = request.form.get("challenge_title", "").strip()
    goal = request.form.get("challenge_goal", "").strip()
    group_id = parse_int(request.form.get("group_id"))
    start = parse_date(request.form.get("start_date"))
    end = parse_date(request.form.get("end_date"))
    if not title or not group_id:
        return redirect("/GroupAdmin/challenge-creation-GA.html?err=1")
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO challenge
           (challenge_title, challenge_date, challenge_start_date, challenge_end_date,
            challenge_status, challenge_goal, group_admin_id, group_id)
           VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s)""",
        (title, start, end, "active", goal, session["id"], group_id),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/created-challenges-GA.html")


@app.post("/actions/group-admin/challenge/<int:cid>/edit")
def ga_edit_challenge(cid):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-challenges-GA.html")
    title = request.form.get("challenge_title", "").strip()
    goal = request.form.get("challenge_goal", "").strip()
    group_id = parse_int(request.form.get("group_id"))
    start = parse_date(request.form.get("start_date"))
    end = parse_date(request.form.get("end_date"))
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE challenge SET challenge_title = %s, challenge_goal = %s,
           challenge_start_date = %s, challenge_end_date = %s, group_id = %s
           WHERE challenge_id = %s AND group_admin_id = %s""",
        (title, goal, start, end, group_id, cid, session["id"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/created-challenges-GA.html")


@app.post("/actions/group-admin/schedule")
def ga_create_schedule():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/create-schedule-GA.html")
    title = request.form.get("title", "").strip()
    loc = request.form.get("location", "").strip()
    group_id = parse_int(request.form.get("group_id"))
    sched_date = parse_date(request.form.get("scheduled_date"))
    if not title or not group_id:
        return redirect("/GroupAdmin/create-schedule-GA.html?err=1")
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO group_workout
           (group_workout_title, group_workout_description, group_workout_scheduled_date,
            group_workout_start_date, group_workout_end_date, group_workout_location,
            group_id, group_admin_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            title,
            None,
            sched_date,
            sched_date,
            sched_date,
            loc,
            group_id,
            session["id"],
        ),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/scheduling-GA.html")


@app.post("/actions/group-admin/schedule/<int:wid>/edit")
def ga_edit_schedule(wid):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/scheduling-GA.html")
    title = request.form.get("title", "").strip()
    loc = request.form.get("location", "").strip()
    group_id = parse_int(request.form.get("group_id"))
    sched_date = parse_date(request.form.get("scheduled_date"))
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE group_workout SET
           group_workout_title = %s, group_workout_location = %s,
           group_workout_scheduled_date = %s, group_workout_start_date = %s,
           group_workout_end_date = %s, group_id = %s
           WHERE group_workout_id = %s AND group_admin_id = %s""",
        (
            title,
            loc,
            sched_date,
            sched_date,
            sched_date,
            group_id,
            wid,
            session["id"],
        ),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/scheduling-GA.html")


@app.post("/actions/group-admin/profile")
def ga_profile():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/profile-GA.html")
    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    cur = mysql.connection.cursor()
    if password:
        cur.execute(
            """UPDATE group_admin SET group_admin_first_name = %s, group_admin_last_name = %s,
               group_admin_email = %s, group_admin_name = %s, password_hash = %s
               WHERE group_admin_id = %s""",
            (
                first,
                last,
                email,
                f"{first} {last}",
                generate_password_hash(password),
                session["id"],
            ),
        )
    else:
        cur.execute(
            """UPDATE group_admin SET group_admin_first_name = %s, group_admin_last_name = %s,
               group_admin_email = %s, group_admin_name = %s
               WHERE group_admin_id = %s""",
            (first, last, email, f"{first} {last}", session["id"]),
        )
    mysql.connection.commit()
    cur.close()
    session["email"] = email
    return redirect("/GroupAdmin/profile-GA.html")


@app.post("/actions/group-admin/workout-log")
def ga_workout_log():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/workout-logging-GA.html")
    uid = parse_int(request.form.get("target_user_id"))
    if not uid:
        return redirect("/GroupAdmin/workout-logging-GA.html?err=1")
    wdate = parse_date(request.form.get("workout_date")) or date.today()
    duration = parse_int(request.form.get("duration_minutes"))
    sets = parse_int(request.form.get("num_sets"))
    reps = parse_int(request.form.get("num_reps"))
    weight = request.form.get("weight")
    try:
        wfloat = float(weight) if weight not in (None, "") else None
    except ValueError:
        wfloat = None
    ex_name = request.form.get("exercise_name", "").strip()
    muscle = request.form.get("muscle_group", "").strip()
    diff = request.form.get("difficulty", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id)
           VALUES (%s, %s, %s, NULL)""",
        (wdate, duration, uid),
    )
    wid = cur.lastrowid
    eid = get_or_create_exercise(cur, ex_name, muscle, diff)
    cur.execute(
        """INSERT INTO workout_log
           (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (sets, reps, wfloat, wid, eid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/workout-history-GA.html")


# --- User actions ---


@app.post("/actions/user/join-group")
def user_join_group():
    if session.get("role") != "user":
        return redirect("/User/GCU.html")
    group_id = parse_int(request.form.get("group_id"))
    if not group_id:
        return redirect("/User/GCU.html?err=1")
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT IGNORE INTO user_group (user_id, group_id) VALUES (%s, %s)",
        (session["id"], group_id),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/User/GJU.html")


@app.post("/actions/user/create-group-become-ga")
def user_create_group_become_ga():
    if session.get("role") != "user":
        return redirect("/User/GCU.html")
    user_id = session["id"]
    name = request.form.get("group_name", "").strip()
    desc = request.form.get("group_description", "").strip()
    if not name:
        return redirect("/User/GCU.html?err=1")

    admin_id = parse_int(request.form.get("admin_id"))
    if not admin_id:
        inf_cur = mysql.connection.cursor()
        inf_cur.execute("SELECT admin_id FROM admin ORDER BY admin_id LIMIT 1")
        row = inf_cur.fetchone()
        inf_cur.close()
        admin_id = row[0] if row else None
    if not admin_id:
        return redirect("/User/GCU.html?err=admin")

    cur = dict_cursor()
    try:
        try:
            cur.execute(
                "SELECT * FROM app_user WHERE user_id = %s AND is_active = 1",
                (user_id,),
            )
        except OperationalError as e:
            if e.args[0] != 1054:
                raise
            cur.execute("SELECT * FROM app_user WHERE user_id = %s", (user_id,))
        urow = cur.fetchone()
    finally:
        cur.close()
    if not urow:
        return redirect("/User/GCU.html?err=promote")

    conn = mysql.connection
    xcur = conn.cursor()
    try:
        xcur.execute(
            """INSERT INTO group_admin
               (group_admin_name, group_admin_first_name, group_admin_last_name,
                group_admin_email, password_hash)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                f"{urow['user_first_name']} {urow['user_last_name']}",
                urow["user_first_name"],
                urow["user_last_name"],
                urow["user_email"],
                urow["password_hash"],
            ),
        )
        ga_id = xcur.lastrowid
        xcur.execute(
            """INSERT INTO motiv_group
               (group_name, group_description, group_date_created, admin_id, group_admin_id)
               VALUES (%s, %s, CURDATE(), %s, %s)""",
            (name, desc, admin_id, ga_id),
        )
        try:
            xcur.execute(
                "UPDATE app_user SET is_active = 0 WHERE user_id = %s",
                (user_id,),
            )
        except OperationalError as e:
            if e.args[0] != 1054:
                raise
            conn.rollback()
            return redirect("/User/GCU.html?err=migrate")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        xcur.close()

    session["role"] = "group_admin"
    session["id"] = ga_id
    return redirect("/GroupAdmin/GADash.html")


@app.post("/actions/user/profile")
def user_profile():
    if session.get("role") != "user":
        return redirect("/User/ProU.html")
    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    cur = mysql.connection.cursor()
    if password:
        cur.execute(
            """UPDATE app_user SET user_first_name = %s, user_last_name = %s,
               user_email = %s, user_name = %s, password_hash = %s
               WHERE user_id = %s""",
            (
                first,
                last,
                email,
                f"{first} {last}",
                generate_password_hash(password),
                session["id"],
            ),
        )
    else:
        cur.execute(
            """UPDATE app_user SET user_first_name = %s, user_last_name = %s,
               user_email = %s, user_name = %s WHERE user_id = %s""",
            (first, last, email, f"{first} {last}", session["id"]),
        )
    mysql.connection.commit()
    cur.close()
    session["email"] = email
    return redirect("/User/ProU.html")


@app.post("/actions/user/workout")
def user_workout():
    if session.get("role") != "user":
        return redirect("/User/WLAU.html")
    uid = session["id"]
    wdate = parse_date(request.form.get("workout_date")) or date.today()
    duration = parse_int(request.form.get("duration_minutes"))
    sets = parse_int(request.form.get("num_sets"))
    reps = parse_int(request.form.get("num_reps"))
    weight = request.form.get("weight")
    try:
        wfloat = float(weight) if weight not in (None, "") else None
    except ValueError:
        wfloat = None
    ex_name = request.form.get("exercise_name", "").strip()
    muscle = request.form.get("muscle_group", "").strip()
    diff = request.form.get("difficulty", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        """INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id)
           VALUES (%s, %s, %s, NULL)""",
        (wdate, duration, uid),
    )
    wid = cur.lastrowid
    eid = get_or_create_exercise(cur, ex_name, muscle, diff)
    cur.execute(
        """INSERT INTO workout_log
           (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (sets, reps, wfloat, wid, eid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/User/WLU.html")


@app.post("/actions/user/workout/<int:wid>/edit")
def user_workout_edit(wid):
    if session.get("role") != "user":
        return redirect("/User/WLEU.html")
    uid = session["id"]
    wdate = parse_date(request.form.get("workout_date")) or date.today()
    duration = parse_int(request.form.get("duration_minutes"))
    sets = parse_int(request.form.get("num_sets"))
    reps = parse_int(request.form.get("num_reps"))
    weight = request.form.get("weight")
    try:
        wfloat = float(weight) if weight not in (None, "") else None
    except ValueError:
        wfloat = None
    ex_name = request.form.get("exercise_name", "").strip()
    muscle = request.form.get("muscle_group", "").strip()
    diff = request.form.get("difficulty", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE workout SET workout_date = %s, workout_duration_minutes = %s
           WHERE workout_id = %s AND user_id = %s""",
        (wdate, duration, wid, uid),
    )
    eid = get_or_create_exercise(cur, ex_name, muscle, diff)
    cur.execute("SELECT workout_log_id FROM workout_log WHERE workout_id = %s LIMIT 1", (wid,))
    lr = cur.fetchone()
    if lr:
        log_id = lr[0]
        cur.execute(
            """UPDATE workout_log SET workout_num_sets = %s, workout_num_reps = %s,
               workout_num_weight = %s, exercise_id = %s WHERE workout_log_id = %s""",
            (sets, reps, wfloat, eid, log_id),
        )
    else:
        cur.execute(
            """INSERT INTO workout_log
               (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (sets, reps, wfloat, wid, eid),
        )
    mysql.connection.commit()
    cur.close()
    return redirect("/User/WLU.html")


@app.post("/actions/user/workout/<int:wid>/delete")
def user_workout_delete(wid):
    if session.get("role") != "user":
        return redirect("/User/WLU.html")
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM workout WHERE workout_id = %s AND user_id = %s",
        (wid, session["id"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/User/WLU.html")


# --- Admin actions ---


@app.post("/actions/admin/profile")
def admin_profile():
    if session.get("role") != "admin":
        return redirect("/Admin/AProfile.html")
    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    cur = mysql.connection.cursor()
    if password:
        cur.execute(
            """UPDATE admin SET admin_first_name = %s, admin_last_name = %s,
               admin_email = %s, admin_name = %s, password_hash = %s
               WHERE admin_id = %s""",
            (
                first,
                last,
                email,
                f"{first} {last}",
                generate_password_hash(password),
                session["id"],
            ),
        )
    else:
        cur.execute(
            """UPDATE admin SET admin_first_name = %s, admin_last_name = %s,
               admin_email = %s, admin_name = %s WHERE admin_id = %s""",
            (first, last, email, f"{first} {last}", session["id"]),
        )
    mysql.connection.commit()
    cur.close()
    session["email"] = email
    return redirect("/Admin/AProfile.html")


@app.post("/actions/admin/group/<int:gid>/edit")
def admin_group_edit(gid):
    if session.get("role") != "admin":
        return redirect("/Admin/GroupAed.html")
    name = request.form.get("group_name", "").strip()
    desc = request.form.get("group_description", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE motiv_group SET group_name = %s, group_description = %s WHERE group_id = %s",
        (name, desc, gid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/Admin/GroupA.html")


@app.post("/actions/admin/remove-group-member")
def admin_remove_group_member():
    if session.get("role") != "admin":
        return redirect("/Admin/GroupA.html")
    gid = parse_int(request.form.get("group_id"))
    uid = parse_int(request.form.get("user_id"))
    if not gid or not uid:
        return redirect("/Admin/GroupA.html")
    cur = mysql.connection.cursor()
    cur.execute("SELECT 1 FROM motiv_group WHERE group_id = %s LIMIT 1", (gid,))
    if not cur.fetchone():
        cur.close()
        return redirect("/Admin/GroupA.html")
    cur.execute(
        "DELETE FROM user_group WHERE user_id = %s AND group_id = %s",
        (uid, gid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect(f"/Admin/GroupA.html?group_id={gid}")


@app.post("/actions/admin/challenge/<int:cid>/edit")
def admin_challenge_edit(cid):
    if session.get("role") != "admin":
        return redirect("/Admin/ScheduleAed.html")
    title = (
        request.form.get("challenge_title", "").strip()
        or request.form.get("challenge_name", "").strip()
    )
    start = parse_date(request.form.get("start_date"))
    end = parse_date(request.form.get("end_date"))
    goal = request.form.get("challenge_goal", "").strip()
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE challenge SET challenge_title = %s, challenge_start_date = %s,
           challenge_end_date = %s, challenge_goal = %s WHERE challenge_id = %s""",
        (title, start, end, goal, cid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/Admin/ScheduleA.html")


@app.post("/actions/admin/schedule/<int:wid>/edit")
def admin_schedule_edit(wid):
    if session.get("role") != "admin":
        return redirect("/Admin/ChallengeAed.html")
    title = (
        request.form.get("title", "").strip()
        or request.form.get("session_name", "").strip()
    )
    loc = (
        request.form.get("location", "").strip()
        or request.form.get("location_field", "").strip()
    )
    sched_date = parse_date(
        request.form.get("scheduled_date") or request.form.get("date_field")
    )
    cur = mysql.connection.cursor()
    cur.execute(
        """UPDATE group_workout SET group_workout_title = %s, group_workout_location = %s,
           group_workout_scheduled_date = %s, group_workout_start_date = %s,
           group_workout_end_date = %s WHERE group_workout_id = %s""",
        (title, loc, sched_date, sched_date, sched_date, wid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/Admin/ChallengeA.html")


# --- JSON API (BMGT407 style) ---


@app.get("/api/posts")
def api_posts_get():
    cur = dict_cursor()
    cur.execute(
        """
        SELECT p.post_id, p.post_content, p.post_created, p.user_id, u.user_email
        FROM post p
        JOIN app_user u ON p.user_id = u.user_id
        ORDER BY p.post_created DESC
        """
    )
    rows = [serialize_row(dict(r)) for r in cur.fetchall()]
    cur.close()
    return jsonify(rows)


@app.post("/api/posts")
def api_posts_post():
    if not request.is_json:
        return jsonify(error="Expected JSON"), 400
    role = session.get("role")
    if role not in ("user", "group_admin"):
        return jsonify(error="Login as app user or group admin required"), 401
    data = request.get_json() or {}
    content = (data.get("post_content") or "").strip()
    if not content:
        return jsonify(error="post_content required"), 400
    uid = session.get("id")
    cur = mysql.connection.cursor()
    if role == "group_admin":
        # Group admins post through an app_user identity with matching email.
        # If missing, create/sync one so GA posting works reliably.
        ga_email = session.get("email")
        cur.execute(
            """
            SELECT group_admin_first_name, group_admin_last_name, group_admin_email
            FROM group_admin
            WHERE group_admin_id = %s AND group_admin_email = %s
            LIMIT 1
            """,
            (session.get("id"), ga_email),
        )
        ga = cur.fetchone()
        if not ga:
            cur.close()
            return jsonify(error="Group admin session is not linked to a valid account"), 400
        first = ga[0] or ""
        last = ga[1] or ""
        email = ga[2]
        synthetic_pw_hash = generate_password_hash(os.urandom(16).hex())
        cur.execute(
            """
            INSERT INTO app_user (user_name, user_first_name, user_last_name, user_email, password_hash)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              user_name = VALUES(user_name),
              user_first_name = VALUES(user_first_name),
              user_last_name = VALUES(user_last_name),
              user_id = LAST_INSERT_ID(user_id)
            """,
            (f"{first} {last}".strip(), first, last, email, synthetic_pw_hash),
        )
        uid = cur.lastrowid
    cur.execute(
        """INSERT INTO post (post_content, user_id, post_date, post_time)
           VALUES (%s, %s, CURDATE(), CURTIME())""",
        (content, uid),
    )
    mysql.connection.commit()
    cur.close()
    return jsonify(message="Post added successfully"), 201


@app.delete("/api/posts/<int:post_id>")
def api_posts_delete(post_id):
    role = session.get("role")
    cur = mysql.connection.cursor()
    if role == "admin":
        cur.execute("DELETE FROM post WHERE post_id = %s", (post_id,))
    elif role == "user":
        cur.execute(
            "DELETE FROM post WHERE post_id = %s AND user_id = %s",
            (post_id, session["id"]),
        )
    elif role == "group_admin":
        # Group admin may only delete posts owned by matching email identity.
        cur.execute(
            """
            DELETE p FROM post p
            JOIN app_user u ON u.user_id = p.user_id
            WHERE p.post_id = %s AND u.user_email = %s
            """,
            (post_id, session.get("email")),
        )
    else:
        cur.close()
        return jsonify(error="Unauthorized"), 401
    mysql.connection.commit()
    deleted = cur.rowcount
    cur.close()
    if not deleted:
        return jsonify(error="Not found or forbidden"), 404
    return jsonify(message="Post deleted successfully")


@app.get("/api/workouts")
def api_workouts_get():
    uid = request.args.get("user_id", type=int)
    if not uid:
        if session.get("role") == "user":
            uid = session["id"]
        else:
            return jsonify(error="user_id query or user login required"), 400
    cur = dict_cursor()
    cur.execute(
        """
        SELECT workout_id, workout_date, workout_duration_minutes, user_id, group_workout_id
        FROM workout WHERE user_id = %s ORDER BY workout_date DESC
        """,
        (uid,),
    )
    rows = [serialize_row(dict(r)) for r in cur.fetchall()]
    cur.close()
    return jsonify(rows)


@app.delete("/api/workouts/<int:workout_id>")
def api_workouts_delete(workout_id):
    if session.get("role") != "user":
        return jsonify(error="Unauthorized"), 401
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM workout WHERE workout_id = %s AND user_id = %s",
        (workout_id, session["id"]),
    )
    mysql.connection.commit()
    deleted = cur.rowcount
    cur.close()
    if not deleted:
        return jsonify(error="Not found"), 404
    return jsonify(message="Workout deleted successfully")


@app.get("/api/exercises")
def api_exercises_get():
    cur = dict_cursor()
    cur.execute(
        "SELECT exercise_id, exercise_name, exercise_muscle_group, exercise_difficulty_level FROM exercise"
    )
    rows = [serialize_row(dict(r)) for r in cur.fetchall()]
    cur.close()
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True)
