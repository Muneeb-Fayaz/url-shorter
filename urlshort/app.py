"""A small URL shortener built with Flask and SQLite."""

import os
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Flask, abort, g, jsonify, redirect, render_template_string, request

from shortener import encode

# Offset keeps generated codes from being a single character for early ids.
ID_OFFSET = 10_000
CUSTOM_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
RESERVED_CODES = {"api", "static", "health"}
MAX_URL_LENGTH = 2048

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT UNIQUE,
    url          TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    clicks       INTEGER NOT NULL DEFAULT 0,
    last_clicked TEXT
);
"""

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Shorten a URL</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 560px; margin: 4rem auto; padding: 0 1rem; }
    input { width: 100%; padding: .6rem; margin: .3rem 0 .8rem; box-sizing: border-box; }
    button { padding: .6rem 1.2rem; cursor: pointer; }
    #result { margin-top: 1.2rem; word-break: break-all; }
    .error { color: #b00020; }
  </style>
</head>
<body>
  <h1>URL Shortener</h1>
  <form id="form">
    <label>Long URL
      <input id="url" type="url" placeholder="https://example.com/some/long/path" required>
    </label>
    <label>Custom code (optional)
      <input id="code" type="text" placeholder="my-link" pattern="[A-Za-z0-9_-]{3,32}">
    </label>
    <button type="submit">Shorten</button>
  </form>
  <div id="result"></div>
  <script>
    document.getElementById("form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const out = document.getElementById("result");
      const body = { url: document.getElementById("url").value };
      const code = document.getElementById("code").value.trim();
      if (code) body.code = code;
      const res = await fetch("/api/shorten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (res.ok) {
        out.className = "";
        out.innerHTML = 'Short URL: <a href="' + data.short_url + '">' + data.short_url + "</a>";
      } else {
        out.className = "error";
        out.textContent = data.error;
      }
    });
  </script>
</body>
</html>
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_valid_url(value: str) -> bool:
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH:
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("URLSHORT_DB", "urlshort.db")

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with sqlite3.connect(app.config["DB_PATH"]) as conn:
        conn.executescript(SCHEMA)

    @app.get("/")
    def index():
        return render_template_string(INDEX_HTML)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/api/shorten")
    def shorten():
        payload = request.get_json(silent=True) or {}
        url = (payload.get("url") or "").strip()
        custom = (payload.get("code") or "").strip()

        if not is_valid_url(url):
            return jsonify(error="Provide a valid http(s) URL."), 400

        if custom:
            if not CUSTOM_CODE_RE.match(custom):
                return jsonify(error="Custom code must be 3-32 chars: letters, digits, _ or -."), 400
            if custom.lower() in RESERVED_CODES:
                return jsonify(error="That code is reserved."), 400

        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                (custom or None, url, utc_now()),
            )
            code = custom
            if not code:
                code = encode(cur.lastrowid + ID_OFFSET)
                db.execute("UPDATE links SET code = ? WHERE id = ?", (code, cur.lastrowid))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return jsonify(error="That code is already taken."), 409

        short_url = request.host_url + code
        return jsonify(code=code, short_url=short_url, url=url), 201

    @app.get("/api/stats/<code>")
    def stats(code):
        row = get_db().execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            return jsonify(error="Not found."), 404
        return jsonify(
            code=row["code"],
            url=row["url"],
            created_at=row["created_at"],
            clicks=row["clicks"],
            last_clicked=row["last_clicked"],
        )

    @app.get("/<code>")
    def follow(code):
        db = get_db()
        row = db.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
        if row is None:
            abort(404)
        db.execute(
            "UPDATE links SET clicks = clicks + 1, last_clicked = ? WHERE code = ?",
            (utc_now(), code),
        )
        db.commit()
        return redirect(row["url"], code=302)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
