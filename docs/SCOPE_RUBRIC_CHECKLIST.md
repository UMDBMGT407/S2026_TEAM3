# Scope and rubric cross-walk checklist

Use this with your **submitted project scope** document. Tick each item after you verify it in the running app (logged in as the right role).

## User portal (`/User/`)

- [ ] Dashboard (`UDash.html`) — stats and leaderboard load; podium matches table metric.
- [ ] Groups: join / leave / create (`GJU.html`, `GCU.html`).
- [ ] Scheduling (`SU.html`) — RSVP or equivalent flows in scope.
- [ ] Challenges (`CHU.html`) — join/leave as in scope.
- [ ] Posts (`PU.html`) — create with text or photo; delete if in scope.
- [ ] Workout log: list (`WLU.html`), multi-exercise create/edit (`WLAU.html`), legacy single edit (`WLEU.html` with `?id=` or `?workout_id=`).
- [ ] Notifications (`NU.html`) if in scope.
- [ ] Profile (`ProU.html`) — name, email, optional password; cannot save completely empty required fields.

## Group Admin portal (`/GroupAdmin/`)

- [ ] Dashboard (`GADash.html`).
- [ ] Groups: create, edit, invites, created list (`group-creation-GA.html`, `created-groups-GA.html`, etc.).
- [ ] Scheduling and challenges as in scope.
- [ ] Workout log: history (`workout-history-GA.html`), multi-exercise log (`workout-logging-GA.html`), delete workout.
- [ ] Profile (`profile-GA.html`).
- [ ] Notifications if in scope.

## Admin portal (`/Admin/`)

- [ ] Login and registration (`index.html`, `CreateAccount.html`).
- [ ] Dashboard and any admin-only CRUD in your scope (groups, challenges, schedules, posts).

## Rubric quick checks (all roles)

- [ ] Numeric fields reject non-numeric input where `type="number"` is used (browser validation).
- [ ] Required fields on forms match what the server enforces (try empty submit).
- [ ] No **page-level** horizontal scroll at 375px / 768px / 1280px on main dashboards (`body` uses `overflow-x: hidden` under portal layouts; wide tables may still scroll **inside** `.table-responsive` / card wrappers).
- [ ] Success and error messages name the feature (e.g. workout, invite), not generic “record” wording.
