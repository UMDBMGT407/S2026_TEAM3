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
import re
from decimal import Decimal
from io import BytesIO
from datetime import date, datetime, time, timedelta
from functools import wraps
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

try:
    from dotenv import load_dotenv

    # Load from project root (folder containing app.py), not only the shell cwd.
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
)
from flask_mysqldb import MySQL
from MySQLdb import OperationalError, ProgrammingError
from MySQLdb.cursors import DictCursor
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

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
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_BYTES", 8 * 1024 * 1024))

mysql = MySQL(app)

POST_UPLOAD_SUBDIR = Path("uploads") / "posts"
POST_UPLOAD_DIR = Path(app.static_folder) / POST_UPLOAD_SUBDIR
ALLOWED_POST_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}

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


@app.errorhandler(413)
def file_too_large(_e):
    if request.path.startswith("/api/"):
        return jsonify(error="Uploaded file is too large"), 413
    return "Uploaded file is too large", 413


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


def parse_time(s: Any):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def format_time_for_html_input(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%H:%M")
    if isinstance(val, time):
        return val.strftime("%H:%M")
    if isinstance(val, timedelta):
        secs = int(val.total_seconds()) % 86400
        h, m = secs // 3600, (secs % 3600) // 60
        return f"{h:02d}:{m:02d}"
    s = str(val).strip()
    if len(s) >= 5 and s[2] == ":":
        return s[:5]
    return ""


def parse_int(s: Any, default: int | None = None):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def parse_workout_goal_count(s: Any, default: int | None = None) -> int | None:
    if s is None:
        return default
    raw = str(s).strip()
    if not raw:
        return default
    if raw.isdigit():
        n = int(raw)
    else:
        m = re.search(r"\d+", raw)
        if not m:
            return default
        n = int(m.group(0))
    if n <= 0:
        return default
    return n


def format_workout_goal_display(s: Any) -> str:
    n = parse_workout_goal_count(s)
    if n is None:
        return "—"
    suffix = "workout" if n == 1 else "workouts"
    return f"{n} {suffix}"


def format_challenge_date_range(start: Any, end: Any) -> str:
    """Human-readable date span for challenge banners (e.g. Apr 01 – Apr 30)."""
    d_start = start.date() if isinstance(start, datetime) else start
    d_end = end.date() if isinstance(end, datetime) else end

    def one(d: Any) -> str:
        if d is None:
            return ""
        if isinstance(d, datetime):
            d = d.date()
        if hasattr(d, "strftime"):
            return d.strftime("%b %d, %Y")
        return str(d)[:10]

    a, b = one(d_start), one(d_end)
    if a and b:
        return f"{a} – {b}" if a != b else a
    if a:
        return f"Starts {a}"
    if b:
        return f"Ends {b}"
    return "—"


def ensure_group_invite_table(cur) -> None:
    """Create group_invite when missing (avoids 1146); same DDL as sql/migration_group_invite.sql."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS group_invite (
          invite_id INT AUTO_INCREMENT PRIMARY KEY,
          group_id INT NOT NULL,
          invited_user_id INT NOT NULL,
          invited_by_group_admin_id INT NOT NULL,
          invite_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          invite_status VARCHAR(32) NOT NULL DEFAULT 'pending',
          CONSTRAINT fk_gi_group FOREIGN KEY (group_id)
            REFERENCES motiv_group (group_id) ON DELETE CASCADE,
          CONSTRAINT fk_gi_user FOREIGN KEY (invited_user_id)
            REFERENCES app_user (user_id) ON DELETE CASCADE,
          CONSTRAINT fk_gi_ga FOREIGN KEY (invited_by_group_admin_id)
            REFERENCES group_admin (group_admin_id),
          UNIQUE KEY uq_group_invite_user (group_id, invited_user_id)
        )
        """
    )


def ensure_group_workout_scheduled_time_column(cur) -> None:
    """Add group_workout_scheduled_time when missing; matches sql/migration_group_workout_scheduled_time.sql."""
    try:
        cur.execute(
            """
            ALTER TABLE group_workout
            ADD COLUMN group_workout_scheduled_time TIME NULL
            AFTER group_workout_scheduled_date
            """
        )
        mysql.connection.commit()
    except (OperationalError, ProgrammingError) as e:
        mysql.connection.rollback()
        if e.args[0] == 1060:
            return
        raise


def ensure_group_workout_attendance_table(cur) -> None:
    """Create RSVP table when missing; same DDL as sql/migration_group_workout_attendance.sql."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS group_workout_attendance (
          attendance_id INT AUTO_INCREMENT PRIMARY KEY,
          group_workout_id INT NOT NULL,
          user_id INT NOT NULL,
          attendance_status VARCHAR(16) NOT NULL DEFAULT 'pending',
          attendance_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          CONSTRAINT fk_gwa_workout FOREIGN KEY (group_workout_id)
            REFERENCES group_workout (group_workout_id) ON DELETE CASCADE,
          CONSTRAINT fk_gwa_user FOREIGN KEY (user_id)
            REFERENCES app_user (user_id) ON DELETE CASCADE,
          UNIQUE KEY uq_gwa_workout_user (group_workout_id, user_id)
        )
        """
    )


def ensure_user_challenge_leave_table(cur) -> None:
    """Create user_challenge_leave when missing; user self-opt-out from a challenge."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_challenge_leave (
          leave_id INT AUTO_INCREMENT PRIMARY KEY,
          user_id INT NOT NULL,
          challenge_id INT NOT NULL,
          left_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_ucl_user FOREIGN KEY (user_id)
            REFERENCES app_user (user_id) ON DELETE CASCADE,
          CONSTRAINT fk_ucl_challenge FOREIGN KEY (challenge_id)
            REFERENCES challenge (challenge_id) ON DELETE CASCADE,
          UNIQUE KEY uq_ucl_user_challenge (user_id, challenge_id)
        )
        """
    )


def ensure_challenge_participant_exclusion_table(cur) -> None:
    """Create challenge_participant_exclusion when missing; challenge-scoped member removal."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS challenge_participant_exclusion (
          exclusion_id INT AUTO_INCREMENT PRIMARY KEY,
          challenge_id INT NOT NULL,
          user_id INT NOT NULL,
          removed_by_admin_id INT NOT NULL,
          removed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CONSTRAINT fk_cpe_challenge FOREIGN KEY (challenge_id)
            REFERENCES challenge (challenge_id) ON DELETE CASCADE,
          CONSTRAINT fk_cpe_user FOREIGN KEY (user_id)
            REFERENCES app_user (user_id) ON DELETE CASCADE,
          CONSTRAINT fk_cpe_admin FOREIGN KEY (removed_by_admin_id)
            REFERENCES admin (admin_id),
          UNIQUE KEY uq_cpe_challenge_user (challenge_id, user_id)
        )
        """
    )


def fetch_workout_attendance_rows(cur, workout_id: int, group_id: int) -> list[dict[str, Any]]:
    """Fetch group member attendance for a workout using RSVP table, with safe fallback."""
    try:
        ensure_group_workout_attendance_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
    try:
        cur.execute(
            """
            SELECT u.user_id, u.user_first_name, u.user_last_name, u.user_email,
              CASE COALESCE(gwa.attendance_status, 'pending')
                WHEN 'going' THEN 'Going'
                WHEN 'not_going' THEN 'Not Going'
                ELSE 'Pending'
              END AS attendance_status
            FROM user_group ug
            JOIN app_user u ON u.user_id = ug.user_id
            LEFT JOIN group_workout_attendance gwa
              ON gwa.group_workout_id = %s AND gwa.user_id = u.user_id
            WHERE ug.group_id = %s
            ORDER BY u.user_first_name, u.user_last_name, u.user_id
            """,
            (workout_id, group_id),
        )
        return cur.fetchall()
    except OperationalError as e:
        if e.args[0] != 1146:
            raise
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
            (workout_id, group_id),
        )
        return cur.fetchall()


def ensure_post_photo_path_column(cur) -> None:
    """Add post.post_photo_path when missing for photo uploads."""
    try:
        cur.execute(
            """
            ALTER TABLE post
            ADD COLUMN post_photo_path VARCHAR(255) NULL
            AFTER post_content
            """
        )
        mysql.connection.commit()
    except (OperationalError, ProgrammingError) as e:
        mysql.connection.rollback()
        if e.args[0] == 1060:
            return
        raise


def fetch_posts_rows(cur) -> list[dict[str, Any]]:
    """
    Read posts with photo column when available, but gracefully
    fallback on older DBs where post_photo_path does not exist yet.
    """
    try:
        ensure_post_photo_path_column(cur)
    except (OperationalError, ProgrammingError):
        # If schema change isn't possible right now, we still render posts.
        mysql.connection.rollback()
    try:
        cur.execute(
            """
            SELECT p.post_id, p.post_content, p.post_photo_path, p.post_created, u.user_email, p.user_id
            FROM post p
            JOIN app_user u ON p.user_id = u.user_id
            ORDER BY p.post_created DESC
            """
        )
        return list(cur.fetchall())
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cur.execute(
            """
            SELECT p.post_id, p.post_content, p.post_created, u.user_email, p.user_id
            FROM post p
            JOIN app_user u ON p.user_id = u.user_id
            ORDER BY p.post_created DESC
            """
        )
        rows = list(cur.fetchall())
        for row in rows:
            row["post_photo_path"] = None
        return rows


def save_post_photo(file_obj) -> tuple[str | None, str | None]:
    """Save uploaded post image and return (web_path, error)."""
    if not file_obj or not getattr(file_obj, "filename", ""):
        return None, None
    filename = secure_filename(file_obj.filename or "")
    if not filename or "." not in filename:
        return None, "Invalid file name"
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_POST_IMAGE_EXTS:
        return None, "Unsupported image type"
    mimetype = (getattr(file_obj, "mimetype", "") or "").lower()
    if mimetype and not mimetype.startswith("image/"):
        return None, "File must be an image"
    POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}.{ext}"
    out_path = POST_UPLOAD_DIR / saved_name
    file_obj.save(out_path)
    return f"/Static/{POST_UPLOAD_SUBDIR.as_posix()}/{saved_name}", None


def collect_workout_exercises_from_request() -> list[dict[str, Any]]:
    """Parse multi-row exercise fields from request.form (same shape as GA workout log)."""
    exercise_names = request.form.getlist("exercise_name[]")
    sets_values = request.form.getlist("num_sets[]")
    reps_values = request.form.getlist("num_reps[]")
    weight_values = request.form.getlist("weight[]")
    muscle_values = request.form.getlist("muscle_group[]")
    if not exercise_names and request.form.get("exercise_name"):
        exercise_names = [request.form.get("exercise_name", "")]
        sets_values = [request.form.get("num_sets", "")]
        reps_values = [request.form.get("num_reps", "")]
        weight_values = [request.form.get("weight", "")]
        muscle_values = [request.form.get("muscle_group", "")]

    exercises: list[dict[str, Any]] = []
    for idx, exercise_name_raw in enumerate(exercise_names):
        ex_name = (exercise_name_raw or "").strip()
        sets_raw = sets_values[idx] if idx < len(sets_values) else ""
        reps_raw = reps_values[idx] if idx < len(reps_values) else ""
        weight_raw = weight_values[idx] if idx < len(weight_values) else ""
        muscle_raw = muscle_values[idx] if idx < len(muscle_values) else ""
        if not any(
            [
                ex_name,
                str(sets_raw).strip(),
                str(reps_raw).strip(),
                str(weight_raw).strip(),
                str(muscle_raw).strip(),
            ]
        ):
            continue
        sets = parse_int(sets_raw)
        reps = parse_int(reps_raw)
        try:
            wfloat = (
                float(weight_raw) if str(weight_raw).strip() not in ("", "None") else None
            )
        except ValueError:
            wfloat = None
        exercises.append(
            {
                "exercise_name": ex_name or "Custom",
                "num_sets": sets,
                "num_reps": reps,
                "weight": wfloat,
                "muscle_group": str(muscle_raw).strip(),
            }
        )
    return exercises


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
            "edit_workout_time": "",
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
            "selected_workout_time_display": "",
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
            "wldu_workouts": [],
            "ga_workout_history": [],
            "ga_workouts_this_week": 0,
            "ga_current_streak_days": 0,
            "ga_total_minutes_this_week": 0,
            "ga_workout_leaderboard": [],
            "ga_leaderboard_sets": [],
            "ga_leaderboard_reps": [],
            "user_workout_leaderboard": [],
            "user_leaderboard_sets": [],
            "user_leaderboard_reps": [],
            "dash_challenges": [],
            "dash_selected_challenge": None,
            "user_invites": [],
            "nu_invite_err": None,
            "ga_group_invites": [],
            "ga_invite_err": None,
            "chu_joined_challenges": [],
            "user_workout_editor_err": None,
            "user_editor_workout_id": None,
            "user_editor_workout_date": "",
            "user_editor_duration_minutes": "",
            "user_editor_exercises": [],
            "user_editor_mode": "create",
        }
    )
    return base


def _lb_int(val: Any) -> int:
    """Coerce MySQL driver values (Decimal, str, etc.) to int for leaderboard math."""
    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        try:
            return int(float(val))
        except (TypeError, ValueError):
            try:
                return int(float(str(val).strip()))
            except (TypeError, ValueError):
                return 0


def _site_wide_weekly_leaderboard_raw_rows(
    cur: Any, week_start_sql: str, next_week_start_sql: str
) -> list[dict[str, Any]]:
    """Weekly workout/set/rep totals per user for the site-wide leaderboard.

    Rows are keyed by every ``app_user`` plus any ``user_id`` that appears in
    ``workout`` this week (covers empty/misaligned ``app_user`` or orphan ids).
    """
    sql = f"""
        SELECT
          ids.user_id AS user_id,
          COALESCE(NULLIF(TRIM(u.user_first_name), ''), 'User') AS user_first_name,
          COALESCE(NULLIF(TRIM(u.user_last_name), ''), CAST(ids.user_id AS CHAR)) AS user_last_name,
          COALESCE(wc.cnt, 0) AS weekly_workouts,
          COALESCE(wc.mins, 0) AS weekly_minutes,
          COALESCE(st.sets_total, 0) AS weekly_sets,
          COALESCE(st.reps_total, 0) AS weekly_reps
        FROM (
          SELECT user_id FROM app_user
          UNION
          SELECT DISTINCT user_id
          FROM workout
          WHERE workout_date >= {week_start_sql}
            AND workout_date < {next_week_start_sql}
        ) ids
        LEFT JOIN app_user u ON u.user_id = ids.user_id
        LEFT JOIN (
          SELECT user_id,
            COUNT(workout_id) AS cnt,
            COALESCE(SUM(workout_duration_minutes), 0) AS mins
          FROM workout
          WHERE workout_date >= {week_start_sql}
            AND workout_date < {next_week_start_sql}
          GROUP BY user_id
        ) wc ON wc.user_id = ids.user_id
        LEFT JOIN (
          SELECT w.user_id,
            COALESCE(SUM(wl.workout_num_sets), 0) AS sets_total,
            COALESCE(SUM(wl.workout_num_reps), 0) AS reps_total
          FROM workout w
          INNER JOIN workout_log wl ON wl.workout_id = w.workout_id
          WHERE w.workout_date >= {week_start_sql}
            AND w.workout_date < {next_week_start_sql}
          GROUP BY w.user_id
        ) st ON st.user_id = ids.user_id
        ORDER BY user_first_name, user_last_name, ids.user_id
    """
    cur.execute(sql)
    return list(cur.fetchall() or [])


def _dense_rank_leaderboard_sorted(
    sorted_rows: list[dict[str, Any]],
    score_tuple_fn: Any,
    metric_value_fn: Any,
) -> list[dict[str, Any]]:
    """Dense rank: tied scores share rank; next rank is position index (same as prior GA/UDash logic)."""
    out: list[dict[str, Any]] = []
    previous: tuple[int, ...] | None = None
    current_rank = 0
    for idx, row in enumerate(sorted_rows, start=1):
        sc = score_tuple_fn(row)
        if sc != previous:
            current_rank = idx
            previous = sc
        uname = (
            f"{row.get('user_first_name', '')} {row.get('user_last_name', '')}"
        ).strip()
        out.append(
            {
                "rank": current_rank,
                "user_name": uname,
                "metric_value": _lb_int(metric_value_fn(row)),
            }
        )
    return out


def build_site_wide_weekly_leaderboards(
    cur: Any, week_start_sql: str, next_week_start_sql: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Site-wide this-week leaderboards: workouts, sets, reps (includes users with zeros)."""
    try:
        raw = _site_wide_weekly_leaderboard_raw_rows(cur, week_start_sql, next_week_start_sql)
        if not raw:
            return [], [], []

        def _nm(r: dict[str, Any]) -> str:
            return (
                f"{r.get('user_first_name', '')} {r.get('user_last_name', '')}"
            ).strip().lower()

        w_sorted = sorted(
            raw,
            key=lambda r: (
                -_lb_int(r.get("weekly_workouts")),
                -_lb_int(r.get("weekly_minutes")),
                _nm(r),
            ),
        )
        s_sorted = sorted(
            raw,
            key=lambda r: (
                -_lb_int(r.get("weekly_sets")),
                -_lb_int(r.get("weekly_reps")),
                _nm(r),
            ),
        )
        r_sorted = sorted(
            raw,
            key=lambda r: (
                -_lb_int(r.get("weekly_reps")),
                -_lb_int(r.get("weekly_sets")),
                _nm(r),
            ),
        )

        lb_w = _dense_rank_leaderboard_sorted(
            w_sorted,
            lambda r: (_lb_int(r.get("weekly_workouts")), _lb_int(r.get("weekly_minutes"))),
            lambda r: r.get("weekly_workouts"),
        )
        lb_s = _dense_rank_leaderboard_sorted(
            s_sorted,
            lambda r: (_lb_int(r.get("weekly_sets")), _lb_int(r.get("weekly_reps"))),
            lambda r: r.get("weekly_sets"),
        )
        lb_r = _dense_rank_leaderboard_sorted(
            r_sorted,
            lambda r: (_lb_int(r.get("weekly_reps")), _lb_int(r.get("weekly_sets"))),
            lambda r: r.get("weekly_reps"),
        )
        return lb_w, lb_s, lb_r
    except Exception:
        app.logger.exception("build_site_wide_weekly_leaderboards failed")
        return [], [], []


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
            rows = fetch_posts_rows(cur)
            # Show full shared post feed for all role-specific post pages.
            ctx["posts"] = rows
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
        elif path == "User/WLDU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            if uid:
                cur.execute(
                    """
                    SELECT w.workout_id, w.workout_date, w.workout_duration_minutes,
                           wl.workout_num_sets, wl.workout_num_reps, wl.workout_num_weight,
                           e.exercise_name, e.exercise_difficulty_level, e.exercise_muscle_group
                    FROM workout w
                    LEFT JOIN workout_log wl ON wl.workout_id = w.workout_id
                      AND wl.workout_log_id = (
                        SELECT MIN(wl2.workout_log_id) FROM workout_log wl2
                        WHERE wl2.workout_id = w.workout_id
                      )
                    LEFT JOIN exercise e ON e.exercise_id = wl.exercise_id
                    WHERE w.user_id = %s
                    ORDER BY w.workout_date DESC, w.workout_id DESC
                    """,
                    (uid,),
                )
                ctx["wldu_workouts"] = cur.fetchall()
            else:
                ctx["wldu_workouts"] = []
        elif path == "User/SU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            ctx["selected_workout_id"] = None
            ctx["selected_workout"] = None
            ctx["selected_workout_attendance"] = []
            if uid:
                cur.execute(
                    """
                    SELECT gw.group_workout_id, gw.group_workout_title,
                           gw.group_workout_scheduled_date, gw.group_workout_location,
                           g.group_id, g.group_name
                    FROM group_workout gw
                    JOIN motiv_group g ON gw.group_id = g.group_id
                    JOIN user_group ug ON ug.group_id = g.group_id
                    WHERE ug.user_id = %s
                    ORDER BY gw.group_workout_scheduled_date DESC
                    """,
                    (uid,),
                )
                schedules = cur.fetchall()
                ctx["schedules"] = schedules
                if schedules:
                    selected_workout_id = request.args.get("workout_id", type=int)
                    valid_workout_ids = {s["group_workout_id"] for s in schedules}
                    if selected_workout_id not in valid_workout_ids:
                        selected_workout_id = schedules[0]["group_workout_id"]
                    ctx["selected_workout_id"] = selected_workout_id

                    selected_workout = next(
                        (s for s in schedules if s["group_workout_id"] == selected_workout_id),
                        None,
                    )
                    if selected_workout:
                        ctx["selected_workout"] = selected_workout
                        ctx["selected_workout_attendance"] = fetch_workout_attendance_rows(
                            cur, selected_workout_id, selected_workout["group_id"]
                        )
            else:
                ctx["schedules"] = []
        elif path == "Admin/ADash.html":
            ctx["admin_user_count"] = 0
            ctx["admin_group_count"] = 0
            ctx["admin_post_count"] = 0
            ctx["admin_workouts_logged_count"] = 0
            ctx["admin_busiest_workout_day"] = "—"
            ctx["admin_avg_workout_duration_minutes"] = 0
            ctx["admin_sets_done_count"] = 0
            ctx["admin_exercises_done_count"] = 0
            ctx["admin_reps_done_count"] = 0
            ctx["admin_challenge_count"] = 0
            ctx["admin_avg_challenge_days"] = 0
            ctx["admin_active_challenge_count"] = 0
            ctx["admin_avg_users_per_challenge"] = 0
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
                cur.execute(
                    """
                    SELECT
                      WEEKDAY(w.workout_date) AS weekday_idx,
                      DAYNAME(w.workout_date) AS busiest_workout_day,
                      COUNT(w.workout_id) AS workout_count
                    FROM workout w
                    WHERE w.workout_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
                      AND w.workout_date < DATE_ADD(
                        DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY),
                        INTERVAL 7 DAY
                      )
                    GROUP BY WEEKDAY(w.workout_date), DAYNAME(w.workout_date)
                    ORDER BY workout_count DESC, weekday_idx ASC
                    LIMIT 1
                    """
                )
                row = cur.fetchone() or {}
                day_name = (row.get("busiest_workout_day") or "").strip()
                if day_name:
                    ctx["admin_busiest_workout_day"] = day_name
            except Exception:
                pass
            try:
                cur.execute(
                    """
                    SELECT COALESCE(ROUND(AVG(w.workout_duration_minutes), 0), 0) AS c
                    FROM workout w
                    """
                )
                row = cur.fetchone()
                ctx["admin_avg_workout_duration_minutes"] = int((row or {}).get("c", 0) or 0)
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
            try:
                cur.execute("SELECT COUNT(*) AS c FROM challenge")
                row = cur.fetchone()
                ctx["admin_challenge_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute(
                    """
                    SELECT COUNT(*) AS c
                    FROM challenge c
                    WHERE c.challenge_start_date IS NOT NULL
                      AND c.challenge_start_date <= CURDATE()
                      AND (c.challenge_end_date IS NULL OR c.challenge_end_date >= CURDATE())
                    """
                )
                row = cur.fetchone()
                ctx["admin_active_challenge_count"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute(
                    """
                    SELECT COALESCE(ROUND(AVG(per_challenge.user_count), 2), 0) AS c
                    FROM (
                      SELECT c.challenge_id, COUNT(DISTINCT ug.user_id) AS user_count
                      FROM challenge c
                      LEFT JOIN user_group ug ON ug.group_id = c.group_id
                      GROUP BY c.challenge_id
                    ) AS per_challenge
                    """
                )
                row = cur.fetchone()
                ctx["admin_avg_users_per_challenge"] = (row or {}).get("c", 0)
            except Exception:
                pass
            try:
                cur.execute(
                    """
                    SELECT COALESCE(
                      ROUND(
                        AVG(
                          CASE
                            WHEN c.challenge_start_date IS NOT NULL
                             AND c.challenge_end_date IS NOT NULL
                             AND c.challenge_end_date >= c.challenge_start_date
                            THEN DATEDIFF(c.challenge_end_date, c.challenge_start_date) + 1
                          END
                        ),
                        2
                      ),
                      0
                    ) AS c
                    FROM challenge c
                    """
                )
                row = cur.fetchone()
                ctx["admin_avg_challenge_days"] = (row or {}).get("c", 0)
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
            ctx["selected_workout_time_display"] = ""
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
                      gw.group_workout_scheduled_time, gw.group_workout_start_date,
                      gw.group_workout_end_date, gw.group_workout_location,
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
                    ctx["selected_workout_time_display"] = format_time_for_html_input(
                        selected_workout.get("group_workout_scheduled_time")
                    )
                    ctx["selected_workout_attendance"] = fetch_workout_attendance_rows(
                        cur, selected_workout_id, selected_workout["group_id"]
                    )
        elif path == "Admin/ScheduleA.html":
            ctx["selected_challenge_id"] = None
            ctx["selected_challenge_name"] = None
            ctx["selected_challenge_participants"] = []
            try:
                ensure_challenge_participant_exclusion_table(cur)
                mysql.connection.commit()
            except (OperationalError, ProgrammingError):
                mysql.connection.rollback()
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
            for c in admin_challenges:
                c["challenge_goal_display"] = format_workout_goal_display(
                    c.get("challenge_goal")
                )
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
                        LEFT JOIN challenge_participant_exclusion cpe
                          ON cpe.challenge_id = %s AND cpe.user_id = u.user_id
                        WHERE ug.group_id = %s
                          AND cpe.exclusion_id IS NULL
                        ORDER BY u.user_first_name, u.user_last_name, u.user_id
                        """,
                        (selected_challenge_id, selected_challenge["group_id"]),
                    )
                    participants = []
                    for idx, u in enumerate(cur.fetchall(), start=1):
                        participants.append(
                            {
                                "user_id": u["user_id"],
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
            ctx["edit_workout_time"] = ""
            if wid and path == "GroupAdmin/edit-schedule-GA.html":
                cur.execute(
                    """SELECT * FROM group_workout
                       WHERE group_workout_id = %s AND group_admin_id = %s""",
                    (wid, ga_id),
                )
                ctx["edit_workout"] = cur.fetchone()
                if ctx["edit_workout"]:
                    ctx["edit_workout_time"] = format_time_for_html_input(
                        ctx["edit_workout"].get("group_workout_scheduled_time")
                    )
        elif path == "GroupAdmin/scheduling-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["selected_workout_id"] = None
            ctx["selected_workout"] = None
            ctx["selected_workout_attendance"] = []
            ctx["selected_workout_time_display"] = ""
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
                        SELECT gw.*, g.group_name
                        FROM group_workout gw
                        JOIN motiv_group g ON g.group_id = gw.group_id
                        WHERE gw.group_workout_id = %s AND gw.group_admin_id = %s
                        """,
                        (selected_workout_id, ga_id),
                    )
                    selected_workout = cur.fetchone()
                    if selected_workout:
                        ctx["selected_workout"] = selected_workout
                        ctx["selected_workout_time_display"] = (
                            format_time_for_html_input(
                                selected_workout.get("group_workout_scheduled_time")
                            )
                        )
                        ctx["selected_workout_attendance"] = fetch_workout_attendance_rows(
                            cur, selected_workout_id, selected_workout["group_id"]
                        )
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
        elif path == "GroupAdmin/schedule-joined-workouts-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ga_email = (session.get("email") or "").strip()
            ctx["ga_joined_schedule_sessions"] = []
            ctx["selected_workout_id"] = None
            ctx["selected_workout"] = None
            ctx["selected_workout_time_display"] = ""
            ctx["selected_workout_attendance"] = []
            if ga_id and ga_email:
                cur.execute(
                    "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                    (ga_email,),
                )
                ga_user = cur.fetchone() or {}
                ga_user_id = ga_user.get("user_id")
                if ga_user_id:
                    cur.execute(
                        """
                        SELECT gw.group_workout_id, gw.group_workout_title, gw.group_workout_scheduled_date,
                          gw.group_workout_scheduled_time, gw.group_workout_location, gw.group_id, g.group_name
                        FROM group_workout gw
                        JOIN user_group ug ON ug.group_id = gw.group_id
                        JOIN motiv_group g ON g.group_id = gw.group_id
                        WHERE ug.user_id = %s AND gw.group_admin_id <> %s
                        ORDER BY (gw.group_workout_scheduled_date IS NULL),
                                 gw.group_workout_scheduled_date DESC,
                                 gw.group_workout_id DESC
                        """,
                        (ga_user_id, ga_id),
                    )
                    sessions = cur.fetchall() or []
                    for s in sessions:
                        s["scheduled_time_display"] = format_time_for_html_input(
                            s.get("group_workout_scheduled_time")
                        )
                    ctx["ga_joined_schedule_sessions"] = sessions
                    if sessions:
                        selected_workout_id = request.args.get("workout_id", type=int)
                        valid_workout_ids = {s["group_workout_id"] for s in sessions}
                        if selected_workout_id not in valid_workout_ids:
                            selected_workout_id = sessions[0]["group_workout_id"]
                        ctx["selected_workout_id"] = selected_workout_id
                        selected_workout = next(
                            (
                                s
                                for s in sessions
                                if s["group_workout_id"] == selected_workout_id
                            ),
                            None,
                        )
                        if selected_workout:
                            ctx["selected_workout"] = selected_workout
                            ctx["selected_workout_time_display"] = (
                                selected_workout.get("scheduled_time_display") or ""
                            )
                            ctx["selected_workout_attendance"] = (
                                fetch_workout_attendance_rows(
                                    cur,
                                    selected_workout_id,
                                    selected_workout["group_id"],
                                )
                            )
        elif path == "GroupAdmin/joined-challenges-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ga_email = (session.get("email") or "").strip()
            ctx["ga_joined_challenges"] = []
            ctx["selected_challenge_id"] = None
            ctx["selected_challenge_name"] = None
            ctx["selected_challenge_participants"] = []
            if ga_id and ga_email:
                cur.execute(
                    "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                    (ga_email,),
                )
                ga_user = cur.fetchone() or {}
                ga_user_id = ga_user.get("user_id")
                if ga_user_id:
                    cur.execute(
                        """
                        SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                          c.challenge_end_date, c.challenge_status, c.challenge_goal,
                          c.group_id, g.group_name
                        FROM challenge c
                        JOIN user_group ug ON ug.group_id = c.group_id
                        JOIN motiv_group g ON g.group_id = c.group_id
                        WHERE ug.user_id = %s AND c.group_admin_id <> %s
                        ORDER BY (c.challenge_start_date IS NULL),
                                 c.challenge_start_date DESC,
                                 c.challenge_id DESC
                        """,
                        (ga_user_id, ga_id),
                    )
                    joined_challenges = cur.fetchall() or []
                    for ch in joined_challenges:
                        ch["challenge_goal_display"] = format_workout_goal_display(
                            ch.get("challenge_goal")
                        )
                    ctx["ga_joined_challenges"] = joined_challenges
                    if joined_challenges:
                        selected_challenge_id = request.args.get("challenge_id", type=int)
                        valid_challenge_ids = {
                            c["challenge_id"] for c in joined_challenges
                        }
                        if selected_challenge_id not in valid_challenge_ids:
                            selected_challenge_id = joined_challenges[0]["challenge_id"]
                        ctx["selected_challenge_id"] = selected_challenge_id
                        selected_challenge = next(
                            (
                                c
                                for c in joined_challenges
                                if c["challenge_id"] == selected_challenge_id
                            ),
                            None,
                        )
                        if selected_challenge:
                            ctx["selected_challenge_name"] = selected_challenge[
                                "challenge_title"
                            ]
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
                                        "member_name": (
                                            f"{u['user_first_name']} {u['user_last_name']}"
                                        ),
                                        "rank": idx,
                                        "goal_progress": "—",
                                    }
                                )
                            ctx["selected_challenge_participants"] = participants
        elif path == "GroupAdmin/GADash.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["ga_workouts_this_week"] = 0
            ctx["ga_current_streak_days"] = 0
            ctx["ga_total_minutes_this_week"] = 0
            ctx["ga_workout_leaderboard"] = []
            ctx["ga_leaderboard_sets"] = []
            ctx["ga_leaderboard_reps"] = []
            ctx["dash_challenges"] = []
            ctx["dash_selected_challenge"] = None
            if ga_id:
                week_start_sql = "DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)"
                next_week_start_sql = (
                    "DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)"
                )
                ga_app_uid: int | None = None
                try:
                    cur.execute(
                        """
                        SELECT user_id
                        FROM app_user
                        WHERE user_email = (
                          SELECT group_admin_email
                          FROM group_admin
                          WHERE group_admin_id = %s
                          LIMIT 1
                        )
                        LIMIT 1
                        """,
                        (ga_id,),
                    )
                    ga_user = cur.fetchone()
                    ga_app_uid = (ga_user or {}).get("user_id")
                except Exception:
                    ga_app_uid = None
                if ga_app_uid is None:
                    try:
                        ga_email_fb = (session.get("email") or "").strip()
                        if ga_email_fb:
                            cur.execute(
                                "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                                (ga_email_fb,),
                            )
                            ur = cur.fetchone()
                            if ur:
                                ga_app_uid = ur.get("user_id")
                    except Exception:
                        pass
                if ga_app_uid:
                    try:
                        cur.execute(
                            f"""
                            SELECT
                              COUNT(w.workout_id) AS workouts_this_week,
                              COALESCE(SUM(w.workout_duration_minutes), 0) AS total_minutes_this_week
                            FROM workout w
                            WHERE w.user_id = %s
                              AND w.workout_date >= {week_start_sql}
                              AND w.workout_date < {next_week_start_sql}
                            """,
                            (ga_app_uid,),
                        )
                        summary = cur.fetchone() or {}
                        ctx["ga_workouts_this_week"] = summary.get("workouts_this_week", 0) or 0
                        ctx["ga_total_minutes_this_week"] = (
                            summary.get("total_minutes_this_week", 0) or 0
                        )
                    except Exception:
                        pass
                    try:
                        cur.execute(
                            """
                            SELECT DISTINCT workout_date
                            FROM workout
                            WHERE user_id = %s
                            ORDER BY workout_date DESC
                            """,
                            (ga_app_uid,),
                        )
                        workout_dates = [r.get("workout_date") for r in (cur.fetchall() or [])]
                        workout_date_set = {d for d in workout_dates if d}
                        streak = 0
                        day_cursor = date.today()
                        while day_cursor in workout_date_set:
                            streak += 1
                            day_cursor -= timedelta(days=1)
                        ctx["ga_current_streak_days"] = streak
                    except Exception:
                        pass
                try:
                    lb_w, lb_s, lb_r = build_site_wide_weekly_leaderboards(
                        cur, week_start_sql, next_week_start_sql
                    )
                    ctx["ga_workout_leaderboard"] = lb_w
                    ctx["ga_leaderboard_sets"] = lb_s
                    ctx["ga_leaderboard_reps"] = lb_r
                except Exception:
                    app.logger.exception(
                        "GADash: build_site_wide_weekly_leaderboards failed"
                    )
                try:
                    ga_email = (session.get("email") or "").strip()
                    ga_uid: int | None = None
                    if ga_email:
                        cur.execute(
                            "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                            (ga_email,),
                        )
                        ur = cur.fetchone()
                        if ur:
                            ga_uid = ur.get("user_id")
                    uid_param = ga_uid if ga_uid is not None else -1
                    cur.execute(
                        """
                        SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                          c.challenge_end_date, c.challenge_status, c.challenge_goal,
                          c.group_id, c.group_admin_id, g.group_name,
                          (SELECT COUNT(*) FROM workout w
                           WHERE w.user_id = %s
                             AND (c.challenge_start_date IS NULL
                                  OR w.workout_date >= c.challenge_start_date)
                             AND (c.challenge_end_date IS NULL
                                  OR w.workout_date <= c.challenge_end_date)
                          ) AS my_workout_count
                        FROM challenge c
                        JOIN motiv_group g ON g.group_id = c.group_id
                        WHERE c.group_admin_id = %s
                        ORDER BY (c.challenge_start_date IS NULL),
                                 c.challenge_start_date DESC,
                                 c.challenge_id DESC
                        """,
                        (uid_param, ga_id),
                    )
                    created = cur.fetchall() or []
                    joined_rows: list[dict[str, Any]] = []
                    if ga_uid:
                        cur.execute(
                            """
                            SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                              c.challenge_end_date, c.challenge_status, c.challenge_goal,
                              c.group_id, c.group_admin_id, g.group_name,
                              (SELECT COUNT(*) FROM workout w
                               WHERE w.user_id = %s
                                 AND (c.challenge_start_date IS NULL
                                      OR w.workout_date >= c.challenge_start_date)
                                 AND (c.challenge_end_date IS NULL
                                      OR w.workout_date <= c.challenge_end_date)
                              ) AS my_workout_count
                            FROM challenge c
                            JOIN user_group ug ON ug.group_id = c.group_id
                            JOIN motiv_group g ON g.group_id = c.group_id
                            WHERE ug.user_id = %s AND c.group_admin_id <> %s
                            ORDER BY (c.challenge_start_date IS NULL),
                                     c.challenge_start_date DESC,
                                     c.challenge_id DESC
                            """,
                            (uid_param, ga_uid, ga_id),
                        )
                        joined_rows = cur.fetchall() or []
                    by_id: dict[int, dict[str, Any]] = {}
                    for row in created:
                        by_id[row["challenge_id"]] = dict(row)
                    for row in joined_rows:
                        cid = row["challenge_id"]
                        if cid not in by_id:
                            by_id[cid] = dict(row)
                    merged = list(by_id.values())

                    def _ga_dash_challenge_sort_key(r: dict[str, Any]) -> tuple[Any, ...]:
                        sd = r.get("challenge_start_date")
                        if isinstance(sd, datetime):
                            sd = sd.date()
                        if sd is None:
                            return (1, 0, -(r.get("challenge_id") or 0))
                        if not isinstance(sd, date):
                            return (1, 0, -(r.get("challenge_id") or 0))
                        return (0, -sd.toordinal(), -(r.get("challenge_id") or 0))

                    merged.sort(key=_ga_dash_challenge_sort_key)
                    for ch in merged:
                        ch["challenge_goal_display"] = format_workout_goal_display(
                            ch.get("challenge_goal")
                        )
                        goal_n = parse_workout_goal_count(ch.get("challenge_goal"))
                        cnt = int(ch.get("my_workout_count") or 0)
                        if goal_n:
                            ch["my_progress_display"] = f"{cnt}/{goal_n}"
                        else:
                            ch["my_progress_display"] = "—" if cnt == 0 else str(cnt)
                        ch["dash_is_organizer"] = int(
                            ch.get("group_admin_id") or 0
                        ) == int(ga_id)
                    ctx["dash_challenges"] = merged
                    if merged:
                        selected_id = request.args.get("challenge_id", type=int)
                        valid_ids = {c["challenge_id"] for c in merged}
                        if selected_id not in valid_ids:
                            selected_id = merged[0]["challenge_id"]
                        sel = next(
                            (c for c in merged if c["challenge_id"] == selected_id), None
                        )
                        if sel:
                            dr = format_challenge_date_range(
                                sel.get("challenge_start_date"),
                                sel.get("challenge_end_date"),
                            )
                            bits: list[str] = [dr]
                            gn = (sel.get("group_name") or "").strip()
                            if gn:
                                bits.append(gn)
                            bits.append(
                                "Organizing"
                                if sel.get("dash_is_organizer")
                                else "Participating"
                            )
                            prog = sel.get("my_progress_display")
                            if prog and prog != "—":
                                bits.append(f"Progress: {prog}")
                            st = (sel.get("challenge_status") or "").strip()
                            if st:
                                bits.append(st)
                            ctx["dash_selected_challenge"] = {
                                "challenge_id": sel["challenge_id"],
                                "challenge_title": sel.get("challenge_title") or "Challenge",
                                "detail_line": " • ".join(bits),
                            }
                except Exception:
                    pass
        elif path == "GroupAdmin/created-groups-GA.html":
            ga_id = session.get("id") if session.get("role") == "group_admin" else None
            ctx["selected_group_id"] = None
            ctx["selected_group_name"] = None
            ctx["selected_group_members"] = []
            ctx["invite_err"] = request.args.get("invite_err")
            ctx["invite_ok"] = request.args.get("invite_ok") == "1"
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
        elif path == "GroupAdmin/groups-joined-GA.html":
            ga_email = (session.get("email") or "").strip()
            ctx["ga_joined_groups"] = []
            ctx["selected_group_id"] = None
            ctx["selected_group_name"] = None
            ctx["selected_group_members"] = []
            if ga_email:
                cur.execute(
                    "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                    (ga_email,),
                )
                ga_user = cur.fetchone() or {}
                ga_user_id = ga_user.get("user_id")
                if ga_user_id:
                    cur.execute(
                        """
                        SELECT g.group_id, g.group_name,
                          (SELECT COUNT(*) FROM user_group ug2 WHERE ug2.group_id = g.group_id) AS member_count
                        FROM user_group ug
                        JOIN motiv_group g ON g.group_id = ug.group_id
                        WHERE ug.user_id = %s
                        ORDER BY g.group_name, g.group_id
                        """,
                        (ga_user_id,),
                    )
                    joined_groups = cur.fetchall()
                    ctx["ga_joined_groups"] = joined_groups
                    if joined_groups:
                        selected_group_id = request.args.get("group_id", type=int)
                        valid_group_ids = {g["group_id"] for g in joined_groups}
                        if selected_group_id not in valid_group_ids:
                            selected_group_id = joined_groups[0]["group_id"]
                        ctx["selected_group_id"] = selected_group_id
                        cur.execute(
                            """
                            SELECT g.group_name, ga.group_admin_id,
                              ga.group_admin_first_name, ga.group_admin_last_name, ga.group_admin_email
                            FROM motiv_group g
                            JOIN group_admin ga ON ga.group_admin_id = g.group_admin_id
                            JOIN user_group ug ON ug.group_id = g.group_id
                            WHERE g.group_id = %s AND ug.user_id = %s
                            LIMIT 1
                            """,
                            (selected_group_id, ga_user_id),
                        )
                        selected_group = cur.fetchone()
                        if selected_group:
                            ctx["selected_group_name"] = selected_group["group_name"]
                            selected_members = [
                                {
                                    "member_kind": "group_admin",
                                    "member_name": (
                                        f"{selected_group['group_admin_first_name']} "
                                        f"{selected_group['group_admin_last_name']}"
                                    ),
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
                                        "member_name": (
                                            f"{u['user_first_name']} {u['user_last_name']}"
                                        ),
                                        "member_role": "Member",
                                        "member_email": u["user_email"],
                                    }
                                )
                            ctx["selected_group_members"] = selected_members
        elif path == "User/GJU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            ctx["user_joined_groups"] = []
            ctx["selected_group_id"] = None
            ctx["selected_group_name"] = None
            ctx["selected_group_members"] = []
            if uid:
                cur.execute(
                    """
                    SELECT g.group_id, g.group_name,
                      (SELECT COUNT(*) FROM user_group ug2 WHERE ug2.group_id = g.group_id) AS member_count
                    FROM user_group ug
                    JOIN motiv_group g ON g.group_id = ug.group_id
                    WHERE ug.user_id = %s
                    ORDER BY g.group_name, g.group_id
                    """,
                    (uid,),
                )
                user_groups = cur.fetchall()
                ctx["user_joined_groups"] = user_groups
                if user_groups:
                    selected_group_id = request.args.get("group_id", type=int)
                    valid_group_ids = {g["group_id"] for g in user_groups}
                    if selected_group_id not in valid_group_ids:
                        selected_group_id = user_groups[0]["group_id"]
                    ctx["selected_group_id"] = selected_group_id
                    cur.execute(
                        """
                        SELECT g.group_name, ga.group_admin_id,
                          ga.group_admin_first_name, ga.group_admin_last_name, ga.group_admin_email
                        FROM motiv_group g
                        JOIN group_admin ga ON ga.group_admin_id = g.group_admin_id
                        JOIN user_group ug ON ug.group_id = g.group_id
                        WHERE g.group_id = %s AND ug.user_id = %s
                        LIMIT 1
                        """,
                        (selected_group_id, uid),
                    )
                    selected_group = cur.fetchone()
                    if selected_group:
                        ctx["selected_group_name"] = selected_group["group_name"]
                        selected_members = [
                            {
                                "member_kind": "group_admin",
                                "member_id_label": (
                                    f"#GA{selected_group['group_admin_id']}"
                                ),
                                "member_name": (
                                    f"{selected_group['group_admin_first_name']} "
                                    f"{selected_group['group_admin_last_name']}"
                                ),
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
                                    "member_name": (
                                        f"{u['user_first_name']} {u['user_last_name']}"
                                    ),
                                    "member_role": "Member",
                                    "member_email": u["user_email"],
                                }
                            )
                        ctx["selected_group_members"] = selected_members
        elif path == "User/CHU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            ctx["chu_joined_challenges"] = []
            ctx["selected_challenge_id"] = None
            ctx["selected_challenge_name"] = None
            ctx["selected_challenge_participants"] = []
            if uid:
                try:
                    ensure_user_challenge_leave_table(cur)
                    ensure_challenge_participant_exclusion_table(cur)
                    mysql.connection.commit()
                except (OperationalError, ProgrammingError):
                    mysql.connection.rollback()
                cur.execute(
                    """
                    SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                           c.challenge_end_date, c.challenge_status, c.challenge_goal,
                           c.group_id, g.group_name,
                           (SELECT COUNT(*) FROM workout w
                            WHERE w.user_id = %s
                              AND (c.challenge_start_date IS NULL
                                   OR w.workout_date >= c.challenge_start_date)
                              AND (c.challenge_end_date IS NULL
                                   OR w.workout_date <= c.challenge_end_date)
                           ) AS my_workout_count
                    FROM challenge c
                    JOIN user_group ug ON ug.group_id = c.group_id AND ug.user_id = %s
                    JOIN motiv_group g ON g.group_id = c.group_id
                    WHERE NOT EXISTS (
                      SELECT 1 FROM user_challenge_leave ucl
                      WHERE ucl.user_id = %s AND ucl.challenge_id = c.challenge_id
                    )
                    ORDER BY (c.challenge_start_date IS NULL),
                             c.challenge_start_date DESC,
                             c.challenge_id DESC
                    """,
                    (uid, uid, uid),
                )
                joined = cur.fetchall() or []
                for ch in joined:
                    ch["challenge_goal_display"] = format_workout_goal_display(
                        ch.get("challenge_goal")
                    )
                    goal_n = parse_workout_goal_count(ch.get("challenge_goal"))
                    cnt = int(ch.get("my_workout_count") or 0)
                    if goal_n:
                        ch["my_progress_display"] = f"{cnt}/{goal_n}"
                    else:
                        ch["my_progress_display"] = "—" if cnt == 0 else str(cnt)
                ctx["chu_joined_challenges"] = joined
                if joined:
                    selected_id = request.args.get("challenge_id", type=int)
                    valid_ids = {c["challenge_id"] for c in joined}
                    if selected_id not in valid_ids:
                        selected_id = joined[0]["challenge_id"]
                    ctx["selected_challenge_id"] = selected_id
                    sel = next(
                        (c for c in joined if c["challenge_id"] == selected_id), None
                    )
                    if sel:
                        ctx["selected_challenge_name"] = sel["challenge_title"]
                        start_d = sel.get("challenge_start_date")
                        end_d = sel.get("challenge_end_date")
                        goal_sel = parse_workout_goal_count(sel.get("challenge_goal"))
                        cur.execute(
                            """
                            SELECT u.user_id, u.user_first_name, u.user_last_name
                            FROM user_group ug
                            JOIN app_user u ON u.user_id = ug.user_id
                            LEFT JOIN challenge_participant_exclusion cpe
                              ON cpe.challenge_id = %s AND cpe.user_id = u.user_id
                            WHERE ug.group_id = %s
                              AND cpe.exclusion_id IS NULL
                              AND NOT EXISTS (
                                SELECT 1 FROM user_challenge_leave ucl
                                WHERE ucl.challenge_id = %s
                                  AND ucl.user_id = u.user_id
                              )
                            ORDER BY u.user_first_name, u.user_last_name, u.user_id
                            """,
                            (selected_id, sel["group_id"], selected_id),
                        )
                        prows = cur.fetchall() or []
                        uids_m = [r["user_id"] for r in prows]
                        counts: dict[int, int] = {}
                        if uids_m:
                            placeholders = ",".join(["%s"] * len(uids_m))
                            date_parts: list[str] = []
                            qparams: list[Any] = list(uids_m)
                            if start_d:
                                date_parts.append("w.workout_date >= %s")
                                qparams.append(start_d)
                            if end_d:
                                date_parts.append("w.workout_date <= %s")
                                qparams.append(end_d)
                            date_sql = " AND ".join(date_parts) if date_parts else "1"
                            cur.execute(
                                f"""
                                SELECT w.user_id, COUNT(*) AS cnt
                                FROM workout w
                                WHERE w.user_id IN ({placeholders})
                                  AND ({date_sql})
                                GROUP BY w.user_id
                                """,
                                tuple(qparams),
                            )
                            for rr in cur.fetchall() or []:
                                counts[rr["user_id"]] = int(rr.get("cnt") or 0)
                        ranked: list[dict[str, Any]] = []
                        for r in prows:
                            cct = counts.get(r["user_id"], 0)
                            if goal_sel:
                                gp = f"{cct}/{goal_sel}"
                            else:
                                gp = "—" if cct == 0 else str(cct)
                            ranked.append(
                                {
                                    "member_name": (
                                        f"{r['user_first_name']} {r['user_last_name']}"
                                    ),
                                    "workout_count": cct,
                                    "goal_progress": gp,
                                }
                            )
                        ranked.sort(
                            key=lambda x: (-x["workout_count"], x["member_name"].lower())
                        )
                        participants: list[dict[str, Any]] = []
                        for idx, p in enumerate(ranked, start=1):
                            participants.append(
                                {
                                    "rank": idx,
                                    "member_name": p["member_name"],
                                    "goal_progress": p["goal_progress"],
                                }
                            )
                        ctx["selected_challenge_participants"] = participants
        elif path == "User/UDash.html":
            uid = session.get("id") if session.get("role") == "user" else None
            ctx["user_workouts_this_week"] = 0
            ctx["user_current_streak_days"] = 0
            ctx["user_total_minutes_this_week"] = 0
            ctx["user_workout_leaderboard"] = []
            ctx["user_leaderboard_sets"] = []
            ctx["user_leaderboard_reps"] = []
            ctx["dash_challenges"] = []
            ctx["dash_selected_challenge"] = None
            if uid:
                week_start_sql = "DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)"
                next_week_start_sql = (
                    "DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)"
                )
                try:
                    cur.execute(
                        f"""
                        SELECT
                          COUNT(w.workout_id) AS workouts_this_week,
                          COALESCE(SUM(w.workout_duration_minutes), 0) AS total_minutes_this_week
                        FROM workout w
                        WHERE w.user_id = %s
                          AND w.workout_date >= {week_start_sql}
                          AND w.workout_date < {next_week_start_sql}
                        """,
                        (uid,),
                    )
                    summary = cur.fetchone() or {}
                    ctx["user_workouts_this_week"] = summary.get("workouts_this_week", 0) or 0
                    ctx["user_total_minutes_this_week"] = (
                        summary.get("total_minutes_this_week", 0) or 0
                    )
                except Exception:
                    pass
                try:
                    cur.execute(
                        """
                        SELECT DISTINCT workout_date
                        FROM workout
                        WHERE user_id = %s
                        ORDER BY workout_date DESC
                        """,
                        (uid,),
                    )
                    workout_dates = [r.get("workout_date") for r in (cur.fetchall() or [])]
                    workout_date_set = {d for d in workout_dates if d}
                    streak = 0
                    day_cursor = date.today()
                    while day_cursor in workout_date_set:
                        streak += 1
                        day_cursor -= timedelta(days=1)
                    ctx["user_current_streak_days"] = streak
                except Exception:
                    pass
                try:
                    lb_w, lb_s, lb_r = build_site_wide_weekly_leaderboards(
                        cur, week_start_sql, next_week_start_sql
                    )
                    ctx["user_workout_leaderboard"] = lb_w
                    ctx["user_leaderboard_sets"] = lb_s
                    ctx["user_leaderboard_reps"] = lb_r
                except Exception:
                    app.logger.exception(
                        "UDash: build_site_wide_weekly_leaderboards failed"
                    )
                try:
                    ensure_user_challenge_leave_table(cur)
                    ensure_challenge_participant_exclusion_table(cur)
                    mysql.connection.commit()
                except (OperationalError, ProgrammingError):
                    mysql.connection.rollback()
                try:
                    cur.execute(
                        """
                        SELECT c.challenge_id, c.challenge_title, c.challenge_start_date,
                               c.challenge_end_date, c.challenge_status, c.challenge_goal,
                               c.group_id, g.group_name,
                               (SELECT COUNT(*) FROM workout w
                                WHERE w.user_id = %s
                                  AND (c.challenge_start_date IS NULL
                                       OR w.workout_date >= c.challenge_start_date)
                                  AND (c.challenge_end_date IS NULL
                                       OR w.workout_date <= c.challenge_end_date)
                               ) AS my_workout_count
                        FROM challenge c
                        JOIN user_group ug ON ug.group_id = c.group_id AND ug.user_id = %s
                        JOIN motiv_group g ON g.group_id = c.group_id
                        WHERE NOT EXISTS (
                          SELECT 1 FROM user_challenge_leave ucl
                          WHERE ucl.user_id = %s AND ucl.challenge_id = c.challenge_id
                        )
                        ORDER BY (c.challenge_start_date IS NULL),
                                 c.challenge_start_date DESC,
                                 c.challenge_id DESC
                        """,
                        (uid, uid, uid),
                    )
                    joined = cur.fetchall() or []
                    for ch in joined:
                        ch["challenge_goal_display"] = format_workout_goal_display(
                            ch.get("challenge_goal")
                        )
                        goal_n = parse_workout_goal_count(ch.get("challenge_goal"))
                        cnt = int(ch.get("my_workout_count") or 0)
                        if goal_n:
                            ch["my_progress_display"] = f"{cnt}/{goal_n}"
                        else:
                            ch["my_progress_display"] = "—" if cnt == 0 else str(cnt)
                    ctx["dash_challenges"] = joined
                    if joined:
                        selected_id = request.args.get("challenge_id", type=int)
                        valid_ids = {c["challenge_id"] for c in joined}
                        if selected_id not in valid_ids:
                            selected_id = joined[0]["challenge_id"]
                        sel = next(
                            (c for c in joined if c["challenge_id"] == selected_id), None
                        )
                        if sel:
                            dr = format_challenge_date_range(
                                sel.get("challenge_start_date"),
                                sel.get("challenge_end_date"),
                            )
                            bits: list[str] = [dr]
                            gn = (sel.get("group_name") or "").strip()
                            if gn:
                                bits.append(gn)
                            prog = sel.get("my_progress_display")
                            if prog and prog != "—":
                                bits.append(f"Progress: {prog}")
                            st = (sel.get("challenge_status") or "").strip()
                            if st:
                                bits.append(st)
                            ctx["dash_selected_challenge"] = {
                                "challenge_id": sel["challenge_id"],
                                "challenge_title": sel.get("challenge_title") or "Challenge",
                                "detail_line": " • ".join(bits),
                            }
                except (OperationalError, ProgrammingError) as e:
                    if e.args[0] != 1146:
                        raise
                except Exception:
                    pass
        elif path == "User/NU.html":
            ctx["user_invites"] = []
            ctx["nu_invite_err"] = request.args.get("invite_err")
            uid = session.get("id") if session.get("role") == "user" else None
            if uid:
                try:
                    cur.execute(
                        """
                        SELECT i.invite_id, i.group_id, g.group_name,
                          CONCAT(ga.group_admin_first_name, ' ',
                            ga.group_admin_last_name) AS inviter_name,
                          ga.group_admin_email AS inviter_email
                        FROM group_invite i
                        JOIN motiv_group g ON g.group_id = i.group_id
                        JOIN group_admin ga
                          ON ga.group_admin_id = i.invited_by_group_admin_id
                        WHERE i.invited_user_id = %s AND i.invite_status = 'pending'
                        ORDER BY i.invite_created DESC, i.invite_id DESC
                        """,
                        (uid,),
                    )
                    ctx["user_invites"] = cur.fetchall()
                except (OperationalError, ProgrammingError) as e:
                    if e.args[0] != 1146:
                        raise
        elif path == "GroupAdmin/notifications-GA.html":
            ctx["ga_group_invites"] = []
            ctx["ga_invite_err"] = request.args.get("invite_err")
            if session.get("role") == "group_admin" and session.get("email"):
                try:
                    cur.execute(
                        "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                        (session["email"],),
                    )
                    urow = cur.fetchone()
                    if urow:
                        uid = urow["user_id"]
                        cur.execute(
                            """
                            SELECT i.invite_id, i.group_id, g.group_name,
                              CONCAT(ga.group_admin_first_name, ' ',
                                ga.group_admin_last_name) AS inviter_name,
                              ga.group_admin_email AS inviter_email
                            FROM group_invite i
                            JOIN motiv_group g ON g.group_id = i.group_id
                            JOIN group_admin ga
                              ON ga.group_admin_id = i.invited_by_group_admin_id
                            WHERE i.invited_user_id = %s AND i.invite_status = 'pending'
                            ORDER BY i.invite_created DESC, i.invite_id DESC
                            """,
                            (uid,),
                        )
                        ctx["ga_group_invites"] = cur.fetchall()
                except (OperationalError, ProgrammingError) as e:
                    if e.args[0] != 1146:
                        raise
        elif path == "GroupAdmin/group-creation-GA.html":
            cur.execute(
                "SELECT admin_id, admin_first_name, admin_last_name, admin_email FROM admin"
            )
            ctx["admins"] = cur.fetchall()
        elif path == "GroupAdmin/workout-logging-GA.html":
            ga_email = (session.get("email") or "").strip()
            wid = request.args.get("workout_id", type=int)
            ctx["ga_workout_editor_err"] = request.args.get("err")
            ctx["ga_editor_workout_id"] = None
            ctx["ga_editor_workout_date"] = ""
            ctx["ga_editor_duration_minutes"] = ""
            ctx["ga_editor_exercises"] = []
            ctx["ga_editor_mode"] = "create"
            if ga_email:
                cur.execute(
                    "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
                    (ga_email,),
                )
                ga_user = cur.fetchone() or {}
                ga_user_id = ga_user.get("user_id")
                if ga_user_id and wid:
                    cur.execute(
                        """
                        SELECT workout_id, workout_date, workout_duration_minutes
                        FROM workout
                        WHERE workout_id = %s AND user_id = %s
                        LIMIT 1
                        """,
                        (wid, ga_user_id),
                    )
                    edit_workout = cur.fetchone()
                    if edit_workout:
                        ctx["ga_editor_workout_id"] = wid
                        ctx["ga_editor_mode"] = "edit"
                        ctx["ga_editor_workout_date"] = str(
                            edit_workout.get("workout_date") or ""
                        )
                        ctx["ga_editor_duration_minutes"] = str(
                            edit_workout.get("workout_duration_minutes") or ""
                        )
                        cur.execute(
                            """
                            SELECT wl.workout_log_id, wl.workout_num_sets, wl.workout_num_reps,
                                   wl.workout_num_weight, e.exercise_name,
                                   e.exercise_muscle_group
                            FROM workout_log wl
                            JOIN exercise e ON e.exercise_id = wl.exercise_id
                            WHERE wl.workout_id = %s
                            ORDER BY wl.workout_log_id
                            """,
                            (wid,),
                        )
                        rows = cur.fetchall() or []
                        exercises = []
                        for r in rows:
                            exercises.append(
                                {
                                    "exercise_name": r.get("exercise_name") or "",
                                    "num_sets": r.get("workout_num_sets"),
                                    "num_reps": r.get("workout_num_reps"),
                                    "weight": r.get("workout_num_weight"),
                                    "muscle_group": r.get("exercise_muscle_group") or "",
                                }
                            )
                        ctx["ga_editor_exercises"] = exercises
        elif path == "User/WLAU.html":
            uid = session.get("id") if session.get("role") == "user" else None
            wid = request.args.get("workout_id", type=int)
            ctx["user_workout_editor_err"] = request.args.get("err")
            ctx["user_editor_workout_id"] = None
            ctx["user_editor_workout_date"] = ""
            ctx["user_editor_duration_minutes"] = ""
            ctx["user_editor_exercises"] = []
            ctx["user_editor_mode"] = "create"
            if uid:
                if wid:
                    cur.execute(
                        """
                        SELECT workout_id, workout_date, workout_duration_minutes
                        FROM workout
                        WHERE workout_id = %s AND user_id = %s
                        LIMIT 1
                        """,
                        (wid, uid),
                    )
                    edit_workout = cur.fetchone()
                    if edit_workout:
                        ctx["user_editor_workout_id"] = wid
                        ctx["user_editor_mode"] = "edit"
                        ctx["user_editor_workout_date"] = str(
                            edit_workout.get("workout_date") or ""
                        )
                        ctx["user_editor_duration_minutes"] = str(
                            edit_workout.get("workout_duration_minutes") or ""
                        )
                        cur.execute(
                            """
                            SELECT wl.workout_log_id, wl.workout_num_sets, wl.workout_num_reps,
                                   wl.workout_num_weight, e.exercise_name,
                                   e.exercise_muscle_group
                            FROM workout_log wl
                            JOIN exercise e ON e.exercise_id = wl.exercise_id
                            WHERE wl.workout_id = %s
                            ORDER BY wl.workout_log_id
                            """,
                            (wid,),
                        )
                        rows = cur.fetchall() or []
                        exercises = []
                        for r in rows:
                            exercises.append(
                                {
                                    "exercise_name": r.get("exercise_name") or "",
                                    "num_sets": r.get("workout_num_sets"),
                                    "num_reps": r.get("workout_num_reps"),
                                    "weight": r.get("workout_num_weight"),
                                    "muscle_group": r.get("exercise_muscle_group") or "",
                                }
                            )
                        ctx["user_editor_exercises"] = exercises
        elif path == "GroupAdmin/edit-workout-logging-GA.html":
            ctx["app_users"] = []
        elif path == "User/WLEU.html":
            wid = request.args.get("id", type=int)
            ctx["edit_w"] = None
            ctx["edit_log"] = None
            ctx["edit_ex"] = None
            role = session.get("role")
            if wid and role == "user":
                uid = session["id"]
                cur.execute(
                    "SELECT * FROM workout WHERE workout_id = %s AND user_id = %s",
                    (wid, uid),
                )
                ctx["edit_w"] = cur.fetchone()
            elif wid and role == "group_admin":
                ga_id = session["id"]
                cur.execute(
                    """
                    SELECT w.* FROM workout w
                    WHERE w.workout_id = %s
                    AND EXISTS (
                      SELECT 1 FROM user_group ug
                      JOIN motiv_group g ON g.group_id = ug.group_id
                      WHERE ug.user_id = w.user_id AND g.group_admin_id = %s
                    )
                    """,
                    (wid, ga_id),
                )
                ctx["edit_w"] = cur.fetchone()
            if ctx["edit_w"]:
                cur.execute(
                    "SELECT * FROM workout_log WHERE workout_id = %s LIMIT 1",
                    (wid,),
                )
                ctx["edit_log"] = cur.fetchone()
                if ctx["edit_log"] and ctx["edit_log"].get("exercise_id"):
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
            ctx["groups"] = []
            ctx["edit_workout_time"] = ""
            cur.execute(
                "SELECT group_id, group_name FROM motiv_group ORDER BY group_name"
            )
            ctx["groups"] = cur.fetchall()
            if wid:
                cur.execute(
                    "SELECT * FROM group_workout WHERE group_workout_id = %s", (wid,)
                )
                ctx["edit_session"] = cur.fetchone()
                if ctx["edit_session"]:
                    ctx["edit_workout_time"] = format_time_for_html_input(
                        ctx["edit_session"].get("group_workout_scheduled_time")
                    )
        elif path == "Admin/ScheduleAed.html":
            cid = request.args.get("id", type=int)
            ctx["edit_challenge_admin"] = None
            ctx["edit_challenge_goal_count"] = ""
            if cid:
                cur.execute("SELECT * FROM challenge WHERE challenge_id = %s", (cid,))
                ctx["edit_challenge_admin"] = cur.fetchone()
                if ctx["edit_challenge_admin"]:
                    goal_count = parse_workout_goal_count(
                        ctx["edit_challenge_admin"].get("challenge_goal")
                    )
                    ctx["edit_challenge_goal_count"] = (
                        str(goal_count) if goal_count is not None else ""
                    )
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
        elif path == "GroupAdmin/workout-history-GA.html":
            ga_email = (session.get("email") or "").strip()
            ctx["ga_workout_history"] = []
            if ga_email:
                cur.execute(
                    "SELECT user_id, user_first_name, user_last_name FROM app_user WHERE user_email = %s LIMIT 1",
                    (ga_email,),
                )
                ga_user = cur.fetchone() or {}
                ga_user_id = ga_user.get("user_id")
                if ga_user_id:
                    cur.execute(
                        """
                        SELECT w.workout_id, w.workout_date, w.workout_duration_minutes
                        FROM workout w
                        WHERE w.user_id = %s
                        ORDER BY w.workout_date DESC, w.workout_id DESC
                        """,
                        (ga_user_id,),
                    )
                    ctx["ga_workout_history"] = cur.fetchall()
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


@app.route("/User/WLEU.html")
@require_roles("user", "group_admin")
def user_workout_edit_page():
    if not allowed_page("WLEU.html"):
        abort(404)
    if session.get("role") == "user":
        wid = request.args.get("id", type=int)
        if wid:
            return redirect(f"/User/WLAU.html?workout_id={wid}")
    ctx = build_template_context("User", "WLEU.html")
    return render_template("User/WLEU.html", **ctx)


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


def _delete_motiv_group_cascade(cur: Any, group_id: int, group_admin_id: int | None) -> None:
    """Unlink workouts, remove group_workouts/challenges, then motiv_group.

    When ``group_admin_id`` is set, only rows owned by that GA are touched (GA self-service).
    When ``group_admin_id`` is None, the group is deleted by platform admin (any group).
    """
    if group_admin_id is None:
        cur.execute(
            """
            UPDATE workout w
            INNER JOIN group_workout gw ON w.group_workout_id = gw.group_workout_id
            INNER JOIN motiv_group g ON gw.group_id = g.group_id
            SET w.group_workout_id = NULL
            WHERE g.group_id = %s
            """,
            (group_id,),
        )
        cur.execute(
            """
            DELETE gw FROM group_workout gw
            INNER JOIN motiv_group g ON gw.group_id = g.group_id
            WHERE g.group_id = %s
            """,
            (group_id,),
        )
        cur.execute("DELETE FROM challenge WHERE group_id = %s", (group_id,))
        cur.execute("DELETE FROM motiv_group WHERE group_id = %s", (group_id,))
    else:
        cur.execute(
            """
            UPDATE workout w
            INNER JOIN group_workout gw ON w.group_workout_id = gw.group_workout_id
            INNER JOIN motiv_group g ON gw.group_id = g.group_id
            SET w.group_workout_id = NULL
            WHERE g.group_id = %s AND g.group_admin_id = %s
            """,
            (group_id, group_admin_id),
        )
        cur.execute(
            """
            DELETE gw FROM group_workout gw
            INNER JOIN motiv_group g ON gw.group_id = g.group_id
            WHERE g.group_id = %s AND g.group_admin_id = %s
            """,
            (group_id, group_admin_id),
        )
        cur.execute(
            "DELETE FROM challenge WHERE group_id = %s AND group_admin_id = %s",
            (group_id, group_admin_id),
        )
        cur.execute(
            "DELETE FROM motiv_group WHERE group_id = %s AND group_admin_id = %s",
            (group_id, group_admin_id),
        )


@app.post("/actions/group-admin/delete-group")
def ga_delete_group():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-groups-GA.html")
    gid = parse_int(request.form.get("group_id"))
    if not gid:
        return redirect("/GroupAdmin/created-groups-GA.html")
    ga_id = session["id"]
    cur = mysql.connection.cursor()
    cur.execute(
        """SELECT 1 FROM motiv_group
           WHERE group_id = %s AND group_admin_id = %s LIMIT 1""",
        (gid, ga_id),
    )
    if not cur.fetchone():
        cur.close()
        return redirect("/GroupAdmin/created-groups-GA.html?err=1")
    try:
        _delete_motiv_group_cascade(cur, gid, ga_id)
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
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


@app.post("/actions/group-admin/invite-group-member")
def ga_invite_group_member():
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-groups-GA.html")
    gid = parse_int(request.form.get("group_id"))
    uid = parse_int(request.form.get("user_id"))
    if not gid:
        return redirect("/GroupAdmin/created-groups-GA.html?invite_err=invalid")
    if not uid:
        return redirect(
            f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=invalid"
        )
    ga_id = session["id"]
    cur = dict_cursor()
    cur.execute(
        """SELECT 1 FROM motiv_group
           WHERE group_id = %s AND group_admin_id = %s LIMIT 1""",
        (gid, ga_id),
    )
    if not cur.fetchone():
        cur.close()
        return redirect("/GroupAdmin/created-groups-GA.html?invite_err=invalid")
    row = None
    try:
        cur.execute(
            "SELECT user_id FROM app_user WHERE user_id = %s AND is_active = 1 LIMIT 1",
            (uid,),
        )
        row = cur.fetchone()
        if not row:
            # Older datasets may not have is_active populated yet.
            cur.execute("SELECT user_id FROM app_user WHERE user_id = %s LIMIT 1", (uid,))
            row = cur.fetchone()
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cur.execute(
            "SELECT user_id FROM app_user WHERE user_id = %s LIMIT 1",
            (uid,),
        )
        row = cur.fetchone()
    if not row:
        cur.close()
        return redirect(
            f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=invalid"
        )
    cur.execute(
        "SELECT 1 FROM user_group WHERE user_id = %s AND group_id = %s LIMIT 1",
        (uid, gid),
    )
    if cur.fetchone():
        cur.close()
        return redirect(
            f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=member"
        )
    try:
        ensure_group_invite_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
        cur.close()
        return redirect(
            f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=schema"
        )
    try:
        cur.execute(
            """
            SELECT invite_id, invite_status FROM group_invite
            WHERE group_id = %s AND invited_user_id = %s LIMIT 1
            """,
            (gid, uid),
        )
        inv = cur.fetchone()
        if inv:
            st = (inv.get("invite_status") or "").lower()
            if st == "pending":
                cur.close()
                return redirect(
                    f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=duplicate"
                )
            if st == "accepted":
                cur.close()
                return redirect(
                    f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=member"
                )
            if st == "rejected":
                cur.execute(
                    """
                    UPDATE group_invite SET invite_status = 'pending',
                      invited_by_group_admin_id = %s,
                      invite_created = CURRENT_TIMESTAMP
                    WHERE invite_id = %s
                    """,
                    (ga_id, inv["invite_id"]),
                )
        else:
            cur.execute(
                """
                INSERT INTO group_invite
                  (group_id, invited_user_id, invited_by_group_admin_id, invite_status)
                VALUES (%s, %s, %s, 'pending')
                """,
                (gid, uid, ga_id),
            )
        mysql.connection.commit()
    except (OperationalError, ProgrammingError) as e:
        mysql.connection.rollback()
        cur.close()
        if e.args[0] == 1146:
            return redirect(
                f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_err=schema"
            )
        raise
    cur.close()
    return redirect(
        f"/GroupAdmin/created-groups-GA.html?group_id={gid}&invite_ok=1"
    )


def group_invite_notifications_url() -> str:
    if session.get("role") == "group_admin":
        return "/GroupAdmin/notifications-GA.html"
    return "/User/NU.html"


def invite_recipient_app_user_id(cur) -> int | None:
    role = session.get("role")
    if role == "user":
        uid = session.get("id")
        return uid if isinstance(uid, int) else None
    if role == "group_admin":
        email = (session.get("email") or "").strip()
        if not email:
            return None
        cur.execute(
            "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
            (email,),
        )
        row = cur.fetchone()
        return int(row["user_id"]) if row else None
    return None


@app.post("/actions/user/group-invite/respond")
@require_roles("user", "group_admin")
def user_group_invite_respond():
    notif_url = group_invite_notifications_url()
    invite_id = parse_int(request.form.get("invite_id"))
    action = (request.form.get("action") or "").strip().lower()
    if not invite_id or action not in ("accept", "reject"):
        return redirect(f"{notif_url}?invite_err=invalid")
    cur = dict_cursor()
    recipient_uid = invite_recipient_app_user_id(cur)
    if recipient_uid is None:
        cur.close()
        return redirect(f"{notif_url}?invite_err=invalid")
    try:
        ensure_group_invite_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
        cur.close()
        return redirect(f"{notif_url}?invite_err=schema")
    try:
        cur.execute(
            """
            SELECT invite_id, group_id, invited_user_id, invite_status
            FROM group_invite WHERE invite_id = %s
            """,
            (invite_id,),
        )
    except (OperationalError, ProgrammingError) as e:
        cur.close()
        if e.args[0] == 1146:
            return redirect(f"{notif_url}?invite_err=schema")
        raise
    row = cur.fetchone()
    if not row or row["invited_user_id"] != recipient_uid:
        cur.close()
        return redirect(f"{notif_url}?invite_err=invalid")
    if (row.get("invite_status") or "").lower() != "pending":
        cur.close()
        return redirect(f"{notif_url}?invite_err=invalid")
    gid = row["group_id"]
    if action == "reject":
        cur.execute(
            "UPDATE group_invite SET invite_status = 'rejected' WHERE invite_id = %s",
            (invite_id,),
        )
        mysql.connection.commit()
        cur.close()
        return redirect(notif_url)
    cur.execute(
        "INSERT IGNORE INTO user_group (user_id, group_id) VALUES (%s, %s)",
        (recipient_uid, gid),
    )
    cur.execute(
        "UPDATE group_invite SET invite_status = 'accepted' WHERE invite_id = %s",
        (invite_id,),
    )
    mysql.connection.commit()
    cur.close()
    return redirect(notif_url)


@app.post("/actions/user/schedule/<int:wid>/rsvp")
@require_roles("user")
def user_schedule_rsvp(wid):
    status = (request.form.get("status") or "").strip().lower()
    if status not in ("going", "not_going"):
        return redirect(f"/User/SU.html?workout_id={wid}&rsvp_err=invalid")
    uid = session.get("id")
    cur = dict_cursor()
    cur.execute(
        """
        SELECT gw.group_workout_id
        FROM group_workout gw
        JOIN user_group ug ON ug.group_id = gw.group_id
        WHERE gw.group_workout_id = %s AND ug.user_id = %s
        LIMIT 1
        """,
        (wid, uid),
    )
    if not cur.fetchone():
        cur.close()
        return redirect("/User/SU.html?rsvp_err=invalid")
    try:
        ensure_group_workout_attendance_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
        cur.close()
        return redirect(f"/User/SU.html?workout_id={wid}&rsvp_err=schema")
    cur.execute(
        """
        INSERT INTO group_workout_attendance
          (group_workout_id, user_id, attendance_status)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
          attendance_status = VALUES(attendance_status),
          attendance_updated = CURRENT_TIMESTAMP
        """,
        (wid, uid, status),
    )
    mysql.connection.commit()
    cur.close()
    return redirect(f"/User/SU.html?workout_id={wid}")


@app.post("/actions/user/challenge/<int:cid>/leave")
@require_roles("user")
def user_challenge_leave(cid):
    uid = session.get("id")
    cur = dict_cursor()
    try:
        ensure_user_challenge_leave_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
        cur.close()
        return redirect("/User/CHU.html?leave_err=schema")
    cur.execute(
        """
        SELECT c.group_id
        FROM challenge c
        JOIN user_group ug ON ug.group_id = c.group_id AND ug.user_id = %s
        WHERE c.challenge_id = %s
        LIMIT 1
        """,
        (uid, cid),
    )
    if not cur.fetchone():
        cur.close()
        return redirect("/User/CHU.html?leave_err=forbidden")
    cur.execute(
        """
        SELECT 1 FROM user_challenge_leave
        WHERE user_id = %s AND challenge_id = %s
        LIMIT 1
        """,
        (uid, cid),
    )
    if cur.fetchone():
        cur.close()
        return redirect("/User/CHU.html")
    cur.execute(
        "INSERT IGNORE INTO user_challenge_leave (user_id, challenge_id) VALUES (%s, %s)",
        (uid, cid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/User/CHU.html")


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


@app.post("/actions/group-admin/challenge/<int:cid>/delete")
def ga_delete_challenge(cid):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/created-challenges-GA.html")
    ga_id = session["id"]
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "DELETE FROM challenge WHERE challenge_id = %s AND group_admin_id = %s",
            (cid, ga_id),
        )
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
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
    sched_time = parse_time(request.form.get("scheduled_time"))
    if not title or not group_id:
        return redirect("/GroupAdmin/create-schedule-GA.html?err=1")
    cur = mysql.connection.cursor()
    ensure_group_workout_scheduled_time_column(cur)
    cur.execute(
        """INSERT INTO group_workout
           (group_workout_title, group_workout_description, group_workout_scheduled_date,
            group_workout_scheduled_time,
            group_workout_start_date, group_workout_end_date, group_workout_location,
            group_id, group_admin_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            title,
            None,
            sched_date,
            sched_time,
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
    sched_time = parse_time(request.form.get("scheduled_time"))
    cur = mysql.connection.cursor()
    ensure_group_workout_scheduled_time_column(cur)
    cur.execute(
        """UPDATE group_workout SET
           group_workout_title = %s, group_workout_location = %s,
           group_workout_scheduled_date = %s, group_workout_scheduled_time = %s,
           group_workout_start_date = %s, group_workout_end_date = %s, group_id = %s
           WHERE group_workout_id = %s AND group_admin_id = %s""",
        (
            title,
            loc,
            sched_date,
            sched_time,
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


@app.post("/actions/group-admin/schedule/<int:wid>/delete")
def ga_delete_schedule(wid):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/scheduling-GA.html")
    ga_id = session["id"]
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "UPDATE workout SET group_workout_id = NULL WHERE group_workout_id = %s",
            (wid,),
        )
        cur.execute(
            """DELETE FROM group_workout
               WHERE group_workout_id = %s AND group_admin_id = %s""",
            (wid, ga_id),
        )
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
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
    ga_email = (session.get("email") or "").strip()
    if not ga_email:
        return redirect("/GroupAdmin/workout-history-GA.html?err=user")
    workout_id = parse_int(request.form.get("workout_id"))
    wdate = parse_date(request.form.get("workout_date")) or date.today()
    duration = parse_int(request.form.get("duration_minutes"))
    exercises = collect_workout_exercises_from_request()

    if not exercises:
        target = (
            f"/GroupAdmin/workout-logging-GA.html?workout_id={workout_id}&err=exercise"
            if workout_id
            else "/GroupAdmin/workout-logging-GA.html?err=exercise"
        )
        return redirect(target)

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id FROM app_user WHERE user_email = %s LIMIT 1",
            (ga_email,),
        )
        ga_user = cur.fetchone()
        ga_user_id = (
            ga_user.get("user_id")
            if isinstance(ga_user, dict)
            else (ga_user[0] if ga_user else None)
        )
        if not ga_user_id:
            cur.close()
            return redirect("/GroupAdmin/workout-history-GA.html?err=user")

        if workout_id:
            cur.execute(
                "SELECT 1 FROM workout WHERE workout_id = %s AND user_id = %s LIMIT 1",
                (workout_id, ga_user_id),
            )
            if not cur.fetchone():
                cur.close()
                return redirect("/GroupAdmin/workout-history-GA.html?err=forbidden")
            cur.execute(
                """
                UPDATE workout
                SET workout_date = %s, workout_duration_minutes = %s
                WHERE workout_id = %s AND user_id = %s
                """,
                (wdate, duration, workout_id, ga_user_id),
            )
            cur.execute("DELETE FROM workout_log WHERE workout_id = %s", (workout_id,))
            wid = workout_id
        else:
            cur.execute(
                """
                INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id)
                VALUES (%s, %s, %s, NULL)
                """,
                (wdate, duration, ga_user_id),
            )
            wid = cur.lastrowid

        for ex in exercises:
            eid = get_or_create_exercise(
                cur,
                ex["exercise_name"],
                ex["muscle_group"],
                None,
            )
            cur.execute(
                """
                INSERT INTO workout_log
                    (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (ex["num_sets"], ex["num_reps"], ex["weight"], wid, eid),
            )

        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
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
@require_roles("user")
def user_workout():
    """Legacy single-row create; forwards to multi-exercise save pipeline."""
    return _user_workout_log_save(workout_id_from_form=None)


@app.post("/actions/user/workout-log")
@require_roles("user")
def user_workout_log():
    """Create or update the logged-in user's workout with multiple exercises."""
    return _user_workout_log_save(workout_id_from_form=parse_int(request.form.get("workout_id")))


def _user_workout_log_save(workout_id_from_form: int | None):
    uid = session["id"]
    wdate = parse_date(request.form.get("workout_date")) or date.today()
    duration = parse_int(request.form.get("duration_minutes"))
    exercises = collect_workout_exercises_from_request()
    if not exercises:
        target = (
            f"/User/WLAU.html?workout_id={workout_id_from_form}&err=exercise"
            if workout_id_from_form
            else "/User/WLAU.html?err=exercise"
        )
        return redirect(target)

    cur = mysql.connection.cursor()
    try:
        wid_use = workout_id_from_form
        if wid_use:
            cur.execute(
                "SELECT 1 FROM workout WHERE workout_id = %s AND user_id = %s LIMIT 1",
                (wid_use, uid),
            )
            if not cur.fetchone():
                cur.close()
                return redirect("/User/WLU.html")
            cur.execute(
                """
                UPDATE workout
                SET workout_date = %s, workout_duration_minutes = %s
                WHERE workout_id = %s AND user_id = %s
                """,
                (wdate, duration, wid_use, uid),
            )
            cur.execute("DELETE FROM workout_log WHERE workout_id = %s", (wid_use,))
        else:
            cur.execute(
                """
                INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id)
                VALUES (%s, %s, %s, NULL)
                """,
                (wdate, duration, uid),
            )
            wid_use = cur.lastrowid

        for ex in exercises:
            eid = get_or_create_exercise(
                cur,
                ex["exercise_name"],
                ex["muscle_group"],
                None,
            )
            cur.execute(
                """
                INSERT INTO workout_log
                    (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (ex["num_sets"], ex["num_reps"], ex["weight"], wid_use, eid),
            )

        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
    cur.close()
    return redirect("/User/WLU.html")


@app.post("/actions/user/workout/<int:wid>/edit")
@require_roles("user")
def user_workout_edit(wid):
    """Update workout `wid` for the logged-in user (multi-exercise body)."""
    return _user_workout_log_save(workout_id_from_form=wid)


def _ga_can_edit_workout(cur, wid: int, ga_email: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM workout w
        JOIN app_user u ON u.user_id = w.user_id
        WHERE w.workout_id = %s AND u.user_email = %s
        LIMIT 1
        """,
        (wid, ga_email),
    )
    return cur.fetchone() is not None


@app.post("/actions/group-admin/workout/<int:wid>/edit")
def ga_workout_edit(wid):
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/workout-history-GA.html")
    ga_email = (session.get("email") or "").strip()
    if not ga_email:
        return redirect("/GroupAdmin/workout-history-GA.html")
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
    if not _ga_can_edit_workout(cur, wid, ga_email):
        cur.close()
        return redirect("/GroupAdmin/workout-history-GA.html")
    cur.execute(
        """UPDATE workout SET workout_date = %s, workout_duration_minutes = %s
           WHERE workout_id = %s""",
        (wdate, duration, wid),
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
    return redirect("/GroupAdmin/workout-history-GA.html")


@app.post("/actions/group-admin/workout/<int:wid>/delete")
def ga_workout_delete(wid):
    """Delete a personal workout log for the logged-in group admin (same app_user row as edit)."""
    if session.get("role") != "group_admin":
        return redirect("/GroupAdmin/workout-history-GA.html")
    ga_email = (session.get("email") or "").strip()
    if not ga_email:
        return redirect("/GroupAdmin/workout-history-GA.html")
    cur = mysql.connection.cursor()
    cur.execute(
        """
        DELETE w FROM workout w
        INNER JOIN app_user u ON u.user_id = w.user_id
        WHERE w.workout_id = %s AND u.user_email = %s
        """,
        (wid, ga_email),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/GroupAdmin/workout-history-GA.html")


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


def _admin_export_cell_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, Decimal):
        f = float(val)
        if f.is_integer():
            return int(f)
        return f
    return val


def _admin_build_xlsx_bytes(rows: list[dict[str, Any]], columns: list[str]) -> BytesIO:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(columns)
    for row in rows:
        ws.append([_admin_export_cell_value(row.get(c)) for c in columns])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _admin_fetch_app_user_export(cur) -> tuple[list[dict[str, Any]], list[str]]:
    cols_with = [
        "user_id",
        "user_name",
        "user_first_name",
        "user_last_name",
        "user_email",
        "is_active",
    ]
    try:
        cur.execute(
            """
            SELECT user_id, user_name, user_first_name, user_last_name, user_email, is_active
            FROM app_user ORDER BY user_id
            """
        )
        return cur.fetchall(), cols_with
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cols = [
            "user_id",
            "user_name",
            "user_first_name",
            "user_last_name",
            "user_email",
        ]
        cur.execute(
            """
            SELECT user_id, user_name, user_first_name, user_last_name, user_email
            FROM app_user ORDER BY user_id
            """
        )
        return cur.fetchall(), cols


# Whitelisted admin SQL exports (never include password_hash).
_ADMIN_EXPORT_SPECS: dict[str, tuple[str, list[str]]] = {
    "admins": (
        """
        SELECT admin_id, admin_name, admin_first_name, admin_last_name, admin_email
        FROM admin ORDER BY admin_id
        """,
        [
            "admin_id",
            "admin_name",
            "admin_first_name",
            "admin_last_name",
            "admin_email",
        ],
    ),
    "group_admins": (
        """
        SELECT group_admin_id, group_admin_name, group_admin_first_name, group_admin_last_name,
          group_admin_email
        FROM group_admin ORDER BY group_admin_id
        """,
        [
            "group_admin_id",
            "group_admin_name",
            "group_admin_first_name",
            "group_admin_last_name",
            "group_admin_email",
        ],
    ),
    "posts": (
        """
        SELECT post_id, post_content, post_photo_path, post_created, post_time, post_date, admin_id, user_id
        FROM post ORDER BY post_id
        """,
        [
            "post_id",
            "post_content",
            "post_photo_path",
            "post_created",
            "post_time",
            "post_date",
            "admin_id",
            "user_id",
        ],
    ),
    "groups": (
        """
        SELECT group_id, group_name, group_description, group_date_created, admin_id, group_admin_id
        FROM motiv_group ORDER BY group_id
        """,
        [
            "group_id",
            "group_name",
            "group_description",
            "group_date_created",
            "admin_id",
            "group_admin_id",
        ],
    ),
    "workouts": (
        """
        SELECT workout_id, workout_date, workout_duration_minutes, user_id, group_workout_id
        FROM workout ORDER BY workout_id
        """,
        [
            "workout_id",
            "workout_date",
            "workout_duration_minutes",
            "user_id",
            "group_workout_id",
        ],
    ),
    "exercises": (
        """
        SELECT exercise_id, exercise_name, exercise_muscle_group, exercise_difficulty_level
        FROM exercise ORDER BY exercise_id
        """,
        [
            "exercise_id",
            "exercise_name",
            "exercise_muscle_group",
            "exercise_difficulty_level",
        ],
    ),
    "workout_logs": (
        """
        SELECT workout_log_id, workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id
        FROM workout_log ORDER BY workout_log_id
        """,
        [
            "workout_log_id",
            "workout_num_sets",
            "workout_num_reps",
            "workout_num_weight",
            "workout_id",
            "exercise_id",
        ],
    ),
    "challenges": (
        """
        SELECT challenge_id, challenge_title, challenge_date, challenge_start_date, challenge_end_date,
          challenge_status, challenge_goal, group_admin_id, group_id
        FROM challenge ORDER BY challenge_id
        """,
        [
            "challenge_id",
            "challenge_title",
            "challenge_date",
            "challenge_start_date",
            "challenge_end_date",
            "challenge_status",
            "challenge_goal",
            "group_admin_id",
            "group_id",
        ],
    ),
}

_ADMIN_EXPORT_KINDS = frozenset(_ADMIN_EXPORT_SPECS) | {"users"}


@app.get("/actions/admin/export-data/<string:kind>")
@require_roles("admin")
def admin_export_data(kind: str):
    if kind not in _ADMIN_EXPORT_KINDS:
        abort(404)
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        return (
            "Excel export requires the openpyxl package. From the project root run:\n"
            "  python3 -m pip install -r requirements.txt\n"
            "or:\n"
            "  python3 -m pip install 'openpyxl>=3.1.0,<4'\n"
            "Then restart the Flask server.",
            503,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    if kind == "users":
        cur = dict_cursor()
        try:
            rows, columns = _admin_fetch_app_user_export(cur)
        except Exception:
            app.logger.exception("admin export users failed")
            cur.close()
            return "Export failed", 500
        cur.close()
    else:
        sql, columns = _ADMIN_EXPORT_SPECS[kind]
        cur = dict_cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
        except Exception:
            app.logger.exception("admin export %s failed", kind)
            cur.close()
            return "Export failed", 500
        cur.close()

    buf = _admin_build_xlsx_bytes(rows, columns)
    fname = f"motiv_{kind}_{date.today().isoformat()}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=fname,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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


@app.post("/actions/admin/delete-group")
def admin_delete_group():
    if session.get("role") != "admin":
        return redirect("/Admin/GroupA.html")
    gid = parse_int(request.form.get("group_id"))
    if not gid:
        return redirect("/Admin/GroupA.html?err=1")
    cur = mysql.connection.cursor()
    cur.execute("SELECT 1 FROM motiv_group WHERE group_id = %s LIMIT 1", (gid,))
    if not cur.fetchone():
        cur.close()
        return redirect("/Admin/GroupA.html?err=1")
    try:
        _delete_motiv_group_cascade(cur, gid, None)
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
    cur.close()
    return redirect("/Admin/GroupA.html")


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
    goal = parse_workout_goal_count(request.form.get("challenge_goal"))
    cur = mysql.connection.cursor()
    cur.execute("SELECT challenge_goal FROM challenge WHERE challenge_id = %s", (cid,))
    existing_row = cur.fetchone()
    if not existing_row:
        cur.close()
        return redirect("/Admin/ScheduleA.html")
    existing_goal = (
        existing_row[0]
        if isinstance(existing_row, tuple)
        else existing_row.get("challenge_goal")
    )
    if goal is None:
        goal = parse_workout_goal_count(existing_goal)
    goal_to_store = str(goal) if goal is not None else None
    cur.execute(
        """UPDATE challenge SET challenge_title = %s, challenge_start_date = %s,
           challenge_end_date = %s, challenge_goal = %s WHERE challenge_id = %s""",
        (title, start, end, goal_to_store, cid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/Admin/ScheduleA.html")


@app.post("/actions/admin/challenge/<int:cid>/delete")
def admin_challenge_delete(cid):
    if session.get("role") != "admin":
        return redirect("/Admin/ScheduleA.html")
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM challenge WHERE challenge_id = %s", (cid,))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
    cur.close()
    return redirect("/Admin/ScheduleA.html")


@app.post("/actions/admin/challenge/remove-participant")
def admin_remove_challenge_participant():
    if session.get("role") != "admin":
        return redirect("/Admin/ScheduleA.html")
    cid = parse_int(request.form.get("challenge_id"))
    uid = parse_int(request.form.get("user_id"))
    if not cid or not uid:
        return redirect("/Admin/ScheduleA.html")
    cur = dict_cursor()
    try:
        ensure_challenge_participant_exclusion_table(cur)
        mysql.connection.commit()
    except (OperationalError, ProgrammingError):
        mysql.connection.rollback()
    cur.execute("SELECT group_id FROM challenge WHERE challenge_id = %s LIMIT 1", (cid,))
    challenge = cur.fetchone()
    if not challenge:
        cur.close()
        return redirect("/Admin/ScheduleA.html")
    gid = challenge["group_id"]
    cur.execute(
        "SELECT 1 FROM user_group WHERE group_id = %s AND user_id = %s LIMIT 1",
        (gid, uid),
    )
    if not cur.fetchone():
        cur.close()
        return redirect(f"/Admin/ScheduleA.html?challenge_id={cid}")
    cur.execute(
        """
        INSERT INTO challenge_participant_exclusion
            (challenge_id, user_id, removed_by_admin_id, removed_at)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            removed_by_admin_id = VALUES(removed_by_admin_id),
            removed_at = NOW()
        """,
        (cid, uid, session["id"]),
    )
    mysql.connection.commit()
    cur.close()
    return redirect(f"/Admin/ScheduleA.html?challenge_id={cid}")


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
    group_id = parse_int(request.form.get("group_id"))
    sched_time_raw = request.form.get("scheduled_time")
    sched_time = parse_time(sched_time_raw)
    cur = mysql.connection.cursor()
    ensure_group_workout_scheduled_time_column(cur)
    cur.execute("SELECT * FROM group_workout WHERE group_workout_id = %s", (wid,))
    existing = cur.fetchone()
    if not existing:
        cur.close()
        return redirect("/Admin/ChallengeA.html")
    if not title:
        title = (existing.get("group_workout_title") or "").strip()
    if group_id is None:
        group_id = existing.get("group_id")
    else:
        cur.execute("SELECT 1 FROM motiv_group WHERE group_id = %s LIMIT 1", (group_id,))
        if not cur.fetchone():
            group_id = existing.get("group_id")
    if not (sched_time_raw or "").strip():
        sched_time = existing.get("group_workout_scheduled_time")
    cur.execute(
        """UPDATE group_workout SET group_workout_title = %s, group_workout_location = %s,
           group_workout_scheduled_date = %s, group_workout_start_date = %s,
           group_workout_end_date = %s, group_workout_scheduled_time = %s,
           group_id = %s WHERE group_workout_id = %s""",
        (title, loc, sched_date, sched_date, sched_date, sched_time, group_id, wid),
    )
    mysql.connection.commit()
    cur.close()
    return redirect("/Admin/ChallengeA.html")


@app.post("/actions/admin/schedule/<int:wid>/delete")
def admin_schedule_delete(wid):
    if session.get("role") != "admin":
        return redirect("/Admin/ChallengeA.html")
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "UPDATE workout SET group_workout_id = NULL WHERE group_workout_id = %s",
            (wid,),
        )
        cur.execute("DELETE FROM group_workout WHERE group_workout_id = %s", (wid,))
        mysql.connection.commit()
    except Exception:
        mysql.connection.rollback()
        cur.close()
        raise
    cur.close()
    return redirect("/Admin/ChallengeA.html")


# --- JSON API (BMGT407 style) ---


@app.get("/api/group-admin/user-email-search")
@require_roles("group_admin")
def api_ga_user_email_search():
    q = (request.args.get("q") or "").strip()[:80]
    group_id = request.args.get("group_id", type=int)
    if not group_id or len(q) < 1:
        return jsonify(error="group_id and q (at least 1 character) required"), 400
    cur = dict_cursor()
    cur.execute(
        """SELECT 1 FROM motiv_group
           WHERE group_id = %s AND group_admin_id = %s LIMIT 1""",
        (group_id, session["id"]),
    )
    if not cur.fetchone():
        cur.close()
        return jsonify(error="Group not found or forbidden"), 404
    like = f"%{q}%"
    name_match_sql = """
              ( u.user_email LIKE %s
                OR u.user_first_name LIKE %s
                OR u.user_last_name LIKE %s
                OR CONCAT(TRIM(u.user_first_name), ' ', TRIM(u.user_last_name)) LIKE %s
                OR COALESCE(u.user_name, '') LIKE %s )
    """
    like5 = (like, like, like, like, like)
    try:
        cur.execute(
            f"""
            SELECT u.user_id, u.user_email, u.user_first_name, u.user_last_name
            FROM app_user u
            WHERE u.is_active = 1 AND {name_match_sql}
              AND NOT EXISTS (
                SELECT 1 FROM user_group ug
                WHERE ug.user_id = u.user_id AND ug.group_id = %s
              )
            ORDER BY u.user_email
            LIMIT 15
            """,
            (*like5, group_id),
        )
        rows = cur.fetchall()
        if not rows:
            # Fallback for older data where is_active isn't maintained.
            cur.execute(
                f"""
                SELECT u.user_id, u.user_email, u.user_first_name, u.user_last_name
                FROM app_user u
                WHERE {name_match_sql}
                  AND NOT EXISTS (
                    SELECT 1 FROM user_group ug
                    WHERE ug.user_id = u.user_id AND ug.group_id = %s
                  )
                ORDER BY u.user_email
                LIMIT 15
                """,
                (*like5, group_id),
            )
            rows = cur.fetchall()
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cur.execute(
            f"""
            SELECT u.user_id, u.user_email, u.user_first_name, u.user_last_name
            FROM app_user u
            WHERE {name_match_sql}
              AND NOT EXISTS (
                SELECT 1 FROM user_group ug
                WHERE ug.user_id = u.user_id AND ug.group_id = %s
              )
            ORDER BY u.user_email
            LIMIT 15
            """,
            (*like5, group_id),
        )
        rows = cur.fetchall()
    rows = [
        {
            "user_id": r["user_id"],
            "user_email": r["user_email"],
            "user_name": f"{r['user_first_name']} {r['user_last_name']}".strip(),
        }
        for r in rows
    ]
    cur.close()
    return jsonify(rows)


@app.get("/api/group-admin/group-invite-candidates")
@require_roles("group_admin")
def api_ga_group_invite_candidates():
    """All active app users not in the given group (cap 500) for invite dropdown."""
    group_id = request.args.get("group_id", type=int)
    if not group_id:
        return jsonify(error="group_id required"), 400
    cur = dict_cursor()
    cur.execute(
        """SELECT 1 FROM motiv_group
           WHERE group_id = %s AND group_admin_id = %s LIMIT 1""",
        (group_id, session["id"]),
    )
    if not cur.fetchone():
        cur.close()
        return jsonify(error="Group not found or forbidden"), 404
    invite_limit = 500
    sql = f"""
            SELECT u.user_id, u.user_email, u.user_first_name, u.user_last_name
            FROM app_user u
            WHERE {{active_clause}}
              AND NOT EXISTS (
                SELECT 1 FROM user_group ug
                WHERE ug.user_id = u.user_id AND ug.group_id = %s
              )
            ORDER BY u.user_last_name, u.user_first_name, u.user_email
            LIMIT {invite_limit}
            """
    rows: list[Any] = []
    try:
        cur.execute(
            sql.format(active_clause="u.is_active = 1"),
            (group_id,),
        )
        rows = list(cur.fetchall() or [])
    except OperationalError as e:
        if e.args[0] != 1054:
            raise
        cur.execute(
            sql.format(active_clause="1"),
            (group_id,),
        )
        rows = list(cur.fetchall() or [])
    else:
        if not rows:
            cur.execute(
                sql.format(active_clause="1"),
                (group_id,),
            )
            rows = list(cur.fetchall() or [])
    out = [
        {
            "user_id": r["user_id"],
            "user_email": r["user_email"],
            "user_name": f"{r['user_first_name']} {r['user_last_name']}".strip(),
        }
        for r in rows
    ]
    cur.close()
    return jsonify(out)


@app.get("/api/posts")
def api_posts_get():
    cur = dict_cursor()
    rows = [serialize_row(dict(r)) for r in fetch_posts_rows(cur)]
    cur.close()
    return jsonify(rows)


@app.post("/api/posts")
def api_posts_post():
    role = session.get("role")
    if role not in ("user", "group_admin"):
        return jsonify(error="Login as app user or group admin required"), 401
    uid = session.get("id")
    content = ""
    photo_path = None
    is_multipart = request.mimetype == "multipart/form-data"
    if request.is_json:
        data = request.get_json(silent=True) or {}
        content = (data.get("post_content") or "").strip()
    elif is_multipart:
        content = (request.form.get("post_content") or "").strip()
    else:
        return jsonify(error="Expected JSON or multipart form data"), 400

    cur = mysql.connection.cursor()
    try:
        ensure_post_photo_path_column(cur)
    except (OperationalError, ProgrammingError):
        cur.close()
        return jsonify(error="Post photo schema is unavailable"), 500

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

    if is_multipart:
        photo_path, upload_err = save_post_photo(request.files.get("photo"))
        if upload_err:
            mysql.connection.rollback()
            cur.close()
            return jsonify(error=upload_err), 400
    if not content and not photo_path:
        mysql.connection.rollback()
        cur.close()
        return jsonify(error="Provide post_content or a photo"), 400

    cur.execute(
        """INSERT INTO post (post_content, post_photo_path, user_id, post_date, post_time)
           VALUES (%s, %s, %s, CURDATE(), CURTIME())""",
        (content or None, photo_path, uid),
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
