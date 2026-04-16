# Leaderboard change — rollback

This documents how to undo the **site-wide weekly leaderboard** work (GA + User dashboards) if something goes wrong.

## Option A: Git (recommended)

If you committed before the change or have a clean history:

```bash
cd /path/to/S2026_TEAM3
git log --oneline -5
git revert <commit_sha_of_leaderboard_change>
```

Or restore specific paths from a known good revision:

```bash
git checkout <good_commit> -- app.py Templates/GroupAdmin/GADash.html Templates/User/UDash.html Static/JS/dashboard-leaderboard.js
```

Remove `Static/JS/dashboard-leaderboard.js` if that file did not exist in the old revision:

```bash
git rm --cached Static/JS/dashboard-leaderboard.js 2>/dev/null || true
rm -f Static/JS/dashboard-leaderboard.js
```

## Option B: Snapshot copies (no git)

Before deploying risky edits, copy the current files into a dated folder, for example:

```bash
mkdir -p revert/leaderboard-snapshot-YYYYMMDD
cp app.py revert/leaderboard-snapshot-YYYYMMDD/
cp Templates/GroupAdmin/GADash.html revert/leaderboard-snapshot-YYYYMMDD/
cp Templates/User/UDash.html revert/leaderboard-snapshot-YYYYMMDD/
```

To restore:

```bash
cp revert/leaderboard-snapshot-YYYYMMDD/app.py .
cp revert/leaderboard-snapshot-YYYYMMDD/GADash.html Templates/GroupAdmin/GADash.html
cp revert/leaderboard-snapshot-YYYYMMDD/UDash.html Templates/User/UDash.html
rm -f Static/JS/dashboard-leaderboard.js
```

Then remove the `<script src="../../Static/JS/dashboard-leaderboard.js" defer></script>` lines from both dashboard templates if you restored an older template that did not include them.

## Files touched by the leaderboard feature

- `app.py` — `build_site_wide_weekly_leaderboards`, `_site_wide_weekly_leaderboard_raw_rows`, `_dense_rank_leaderboard_sorted`; GA/UDash context wiring; `_offline_page_context` defaults.
- `Templates/GroupAdmin/GADash.html` — three `<tbody>` sections, metric `<th>` id, script tag.
- `Templates/User/UDash.html` — same.
- `Static/JS/dashboard-leaderboard.js` — Rank by dropdown toggle.
