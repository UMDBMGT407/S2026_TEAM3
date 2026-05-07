# Motiv Local Setup

This project runs locally as a Flask + MySQL app. Frontend pages are served by Flask templates/static files (no separate frontend server required).

## 1) Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `mysqlclient` fails on macOS:

```bash
brew install mysql pkg-config
pip install -r requirements.txt
```

## 2) Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
- `MYSQL_PASSWORD` (required for your local MySQL user)
- `SECRET_KEY` (recommended)

Defaults are already localhost-first:
- `MYSQL_HOST=localhost`
- `MYSQL_DB=motivdata`
- `PUBLIC_BASE_URL=http://localhost:5001`

## 3) Initialize local database

In MySQL Workbench (or mysql CLI), run:
1. `sql/motivdata_schema.sql`
2. `sql/motivdata_seed.sql`

Optional one-time migration for existing databases:
3. `sql/migration_app_user_is_active.sql`

## 4) Run locally

```bash
python app.py
```

App URL:
- `http://localhost:5001`

## Optional: run with Gunicorn locally

```bash
gunicorn -c gunicorn_conf.py wsgi:app
```

## Quick troubleshooting

- If login or data pages fail, confirm MySQL is running and `.env` credentials are correct.
- If port 5001 is in use, set `FLASK_RUN_PORT` (or `GUNICORN_BIND`) to another local port.
- Gemini coaching features require a valid `GEMINI_API_KEY` if you want those responses enabled.
