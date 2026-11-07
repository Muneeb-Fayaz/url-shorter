# URL Shortener

A small URL shortener built with Flask and SQLite.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000 for the web form.

## API

Shorten a URL:

```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Optionally pass `"code": "my-link"` for a custom short code.

Get click stats:

```bash
curl http://127.0.0.1:5000/api/stats/<code>
```

Visiting `/<code>` redirects (302) to the original URL and counts the click.

## Test

```bash
pytest
```

## How it works

- Each link is stored in SQLite. The auto-increment row id (plus an offset) is
  encoded in base62 (`0-9a-zA-Z`) to produce the short code, so codes are
  unique without collision checks.
- Custom codes are validated (3-32 chars of letters, digits, `_`, `-`) and
  protected by a UNIQUE constraint.
- Only `http`/`https` URLs are accepted.

## Ideas to extend

- Link expiry dates
- Rate limiting per IP
- Click analytics by day / referrer
- Swap SQLite for Postgres, add a Dockerfile
- Auth + per-user link dashboards
