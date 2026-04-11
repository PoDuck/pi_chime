# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Chime is a Raspberry Pi-based door chime system. When a magnetic door sensor triggers a GPIO pin, it plays a rotating audio clip through the Pi's audio output. The web UI (Django) manages clips, triggers playback manually, and shows analytics.

## Development Commands

```bash
# Activate virtualenv
source venv/bin/activate            # local dev
source ~/.virtualenvs/chime/bin/activate  # on the Pi (chime.local)

python manage.py runserver 0.0.0.0:8000
python manage.py migrate
python manage.py makemigrations
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py test               # tests exist but are currently empty
```

## Deploying to chime.local

The production server is `poduck@chime.local`. The web app is served by **Apache + mod_wsgi** — not by any `chime` systemctl service.

```bash
# Full deploy sequence
ssh poduck@chime.local "source ~/.virtualenvs/chime/bin/activate && cd ~/chime && git pull && python manage.py collectstatic --noinput && sudo systemctl restart apache2"
```

- `collectstatic` is required after any change to files under `clips/static/`
- Template changes (`.html`) only need `sudo systemctl restart apache2`
- The `chime.service` and `chime-trigger.service` are unrelated to the web app — they run the GPIO trigger script (`trigger/chime.py`)

## Architecture

Three Django apps plus a standalone trigger script:

**`clips`** — Core app. Manages `Clip` model (audio file, thumbnail, order, volume, start/end trim). Handles upload, update, delete, list/playback, and the web-based manual trigger (`TriggerChime` view). Clips rotate via a `last_played` boolean — next clip after the last-played one is selected each trigger.

**`tracking`** — Analytics. Logs each trigger event as a `Track` record (timestamp + location). Views compute day-of-week and hour-of-day distributions using `LOCAL_TIMEZONE` from `.env`.

**`trigger/chime.py`** — Standalone script (not a Django app). Runs as `chime-trigger.service` on the Pi. Polls GPIO pin 21 (BCM) every 50ms; on HIGH, plays the next clip via `mpg123` in a background thread and creates a `Track` record. Has a 3-second cooldown. Also optionally sends a Gotify push notification.

**Frontend** — Bootstrap 5 via crispy-forms. Single CSS file at `clips/static/clips/style.css` using CSS custom properties for dark/light theming (`data-theme` attribute on `<html>`). Theme persisted in `localStorage`.

## Key Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `DEBUG` | `on` for dev, `off` for production |
| `LOCAL_DOMAINS` | Comma-separated values for `ALLOWED_HOSTS` |
| `ON_PI` | `True` enables GPIO; `False` skips hardware init |
| `LOCAL_TIMEZONE` | Used for analytics (e.g. `America/Indiana/Indianapolis`) |
| `GOTIFY_URL` / `GOTIFY_KEY` | Optional push notifications on door trigger |

## Static Files & CSS Notes

- All custom styles are in `clips/static/clips/style.css`
- Bootstrap 5 is loaded from CDN before `style.css`, so custom selectors must match or exceed Bootstrap's specificity to override (e.g. `.form-select` not just `select`)
- After editing static files, `collectstatic` must be run on the server — Apache serves from `~/chime/static/`, not the source tree
