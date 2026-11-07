<div align="center">

# 🔗 Snip

### A tiny, fast URL shortener built with Flask and SQLite

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-embedded-003B57?logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/tests-7%20passing-2EA44F)
![License](https://img.shields.io/badge/license-MIT-blue)

Paste a long link, get a short one. Track every click. No accounts, no setup, no external services.

[Quick start](#-quick-start) · [API](#-api-reference) · [How it works](#-how-it-works) · [Roadmap](#-roadmap)

</div>

---

## ✨ Features

- **Instant short links** with auto-generated base62 codes like `2Bi`
- **Custom aliases** such as `/my-portfolio`, with conflict detection
- **Click analytics** tracking total clicks and last visited time
- **Clean web UI** with a single page form, no JavaScript framework needed
- **JSON API** that is easy to script against with `curl` or any HTTP client
- **Input validation** accepts only `http` and `https` URLs, blocking `javascript:` and similar schemes
- **Zero config** with a single SQLite file and no database server
- **Tested** with a pytest suite covering encoding, validation, redirects, stats, and error paths

## 🚀 Quick start

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open **http://127.0.0.1:5000** and start shortening.

> The database file `urlshort.db` is created automatically on first run.
> Set the `URLSHORT_DB` environment variable to store it somewhere else.

## 📡 API reference

| Method | Endpoint             | Description                              | Success |
| ------ | -------------------- | ---------------------------------------- | ------- |
| `POST` | `/api/shorten`       | Create a short link                      | `201`   |
| `GET`  | `/<code>`            | Redirect to the original URL, count click | `302`   |
| `GET`  | `/api/stats/<code>`  | Get click statistics for a link          | `200`   |
| `GET`  | `/health`            | Health check                             | `200`   |

### Create a short link

```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/some/very/long/path?with=params"}'
```

```json
{
  "code": "2Bi",
  "short_url": "http://127.0.0.1:5000/2Bi",
  "url": "https://example.com/some/very/long/path?with=params"
}
```

### Use a custom alias

```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "code": "my-link"}'
```

Custom codes must be **3 to 32 characters** using letters, digits, `_` or `-`.

### Get click stats

```bash
curl http://127.0.0.1:5000/api/stats/2Bi
```

```json
{
  "code": "2Bi",
  "url": "https://example.com/some/very/long/path?with=params",
  "created_at": "2026-11-07T15:15:00+00:00",
  "clicks": 42,
  "last_clicked": "2026-11-07T18:02:11+00:00"
}
```

### Error responses

| Status | Meaning                                                    |
| ------ | ---------------------------------------------------------- |
| `400`  | Invalid URL, malformed custom code, or reserved code       |
| `404`  | Short code does not exist                                  |
| `409`  | Custom code is already taken                               |

## 🧠 How it works

```
  POST /api/shorten                         GET /2Bi
        │                                       │
        ▼                                       ▼
  ┌───────────┐   insert row    ┌────────┐   lookup   ┌───────────┐
  │ Validate  │ ──────────────▶ │ SQLite │ ◀───────── │  Resolve  │
  │ URL/alias │  (get row id)   │ links  │            │   code    │
  └───────────┘                 └────────┘            └───────────┘
        │                            ▲                      │
        ▼                            │ clicks += 1          ▼
  base62(id + 10000) ────────────────┘               302 redirect
        │
        ▼
     "2Bi"
```

**Code generation.** Each link gets an auto-incrementing database id. That id, plus an offset of 10,000, is encoded in base62 (`0-9a-zA-Z`). Because every id is unique, every code is unique, so there are no collision checks and no retry loops. The offset keeps early codes from being a single character.

**Custom aliases.** Alias uniqueness is enforced by a `UNIQUE` constraint in SQLite, so two simultaneous requests cannot claim the same code. The loser gets a clean `409`.

**Safety.** Only `http` and `https` URLs with a host are accepted, URLs are capped at 2048 characters, and codes like `api` and `health` are reserved so they can never shadow real routes.

**Redirects.** Links use `302` rather than `301` so browsers do not cache them, which keeps click counts accurate.

## 🗂 Project structure

```
urlshort/
├── app.py            # Flask app, routes, DB layer, web UI
├── shortener.py      # base62 encode/decode helpers
├── test_app.py       # pytest suite
├── requirements.txt  # Flask, pytest
└── README.md
```

## 🧪 Running the tests

```bash
pytest -v
```

The suite covers base62 round trips, URL validation, redirects, click counting, custom code conflicts, bad input, and unknown codes. Each test runs against a fresh temporary database.

## 🗺 Roadmap

- [ ] Link expiry dates
- [ ] Per IP rate limiting
- [ ] Click analytics by day and referrer
- [ ] QR code generation for each link
- [ ] Dockerfile and Postgres support
- [ ] User accounts with a personal dashboard

## 🤝 Contributing

Ideas and pull requests are welcome. Please run `pytest` before opening a PR and add tests for new behavior.

## 📄 License

Released under the MIT License.
