# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a `uv` project (`uv init --package`) using Django as the web framework with Django REST Framework (`rest_framework` in `INSTALLED_APPS`; typed via `djangorestframework-stubs`). Elasticsearch (run via `compose.yaml`) holds two corpora: [OANC](https://anc.org/data/oanc/) (index `oanc`, one document per sentence) and ConvoKit's `reddit-corpus-small` (index `reddit`, one document per post/comment). Ruff is the linter/formatter (configured under `[tool.ruff]` in `pyproject.toml`). mypy (strict) with the django-stubs plugin is the type checker (`[tool.mypy]` / `[tool.django-stubs]` in `pyproject.toml`); the plugin loads `jibril_backend.settings`, so settings must stay importable for type checking to work. No test runner has been chosen yet — check `pyproject.toml` before assuming any tooling exists, and update this file once those choices are made.

## Commands

The project is managed with [uv](https://docs.astral.sh/uv/) and targets Python 3.15.2, installed via [mise](https://mise.jdx.dev/) (`mise.toml`) and also pinned in `.python-version` for uv (`requires-python = ">=3.12"`). Run `mise install` first.

```sh
uv sync                      # create .venv and install the project + dependencies
uv run jibril-backend <cmd>  # Django management commands, same as manage.py (e.g. runserver, migrate)
uv run python manage.py <cmd>  # equivalent
uv add <pkg>                 # add a runtime dependency
uv add --dev <pkg>           # add a dev dependency (e.g. pytest)
uv run ruff check .          # lint (add --fix to auto-fix)
uv run ruff format .         # format
uv run mypy .                # type check (strict, django-stubs plugin)
cp .env.example .env         # then set ELASTIC_PASSWORD (Django and compose both read .env)
docker compose up -d         # Elasticsearch on 127.0.0.1:9200 (security on, no TLS)
docker compose --profile kibana up -d  # also Kibana on 127.0.0.1:5601 — local dev only, never on the VPS
uv run jibril-backend spectacular --validate --file openapi.yaml  # dump OpenAPI (not committed; served at /api/schema/)
uv run jibril-backend index_oanc [path] [--recreate] [--limit N]  # index OANC (default path data/OANC/data)
uv run jibril-backend index_reddit [path] [--recreate]  # index Reddit (default path data/reddit/reddit-corpus-small)
```

## Layout

- `src/` layout: the importable package is `jibril_backend` under `src/`, built with the `uv_build` backend.
- Django project config lives directly in the package: `src/jibril_backend/{settings,urls,asgi,wsgi}.py` (`DJANGO_SETTINGS_MODULE=jibril_backend.settings`). `BASE_DIR` in `settings.py` is the repo root (three `.parent`s up), so `db.sqlite3` is created there (gitignored).
- `jibril_backend:main` in `__init__.py` is Django's `execute_from_command_line`; both the `jibril-backend` console script (`[project.scripts]`) and the root `manage.py` call it. Keep that entry point valid (or update it) when restructuring.
- `src/jibril_backend/corpus/` is the only app (no models — everything lives in Elasticsearch): `oanc.py` / `reddit.py` read the corpora, `search.py` holds the index mappings and client, `management/commands/index_{oanc,reddit}.py` bulk-index, and `views.py` serves `GET /api/oanc/sentences/search/` and `GET /api/reddit/comments/search/` (both built on the shared `_search` helper). OpenAPI comes from drf-spectacular (`/api/schema/`, Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`): views must declare their query params and responses with `@extend_schema` using the serializers in `serializers.py`, and should render responses through those serializers so the schema can't drift. A serializer field named `source` can't be a class attribute (it shadows `Field.source`) — build such fields in `get_fields()`, or rename the query param (hence `subcorpus`). Changing a mapping in `search.py` requires re-running that corpus's index command with `--recreate`.
- OANC source: the `OANC-1.0.1-UTF8.zip` release linked from https://anc.org/data/oanc/download/, unpacked into `data/` (gitignored, ~3.3GB). Each document is `<name>.txt` plus stand-off annotations; sentence boundaries come from `<name>-s.xml` (character offsets into the `.txt`) and metadata from `<name>.anc`. The first path component gives `mode` (written/spoken), the next two `genre` and `source`.
- Reddit source: `reddit-corpus-small.corpus.zip` from https://zissou.infosci.cornell.edu/convokit/datasets/subreddit-corpus/ (100 subreddits, September 2018 only), unpacked into `data/reddit/`. Read the JSON files directly — the `convokit` package isn't a dependency. `reddit.py` skips `[deleted]`/`[removed]`/empty text and AutoModerator, and never indexes usernames. Adult subreddits are intentionally kept. The full per-subreddit corpus is ~680GB zipped (~2TB as an index), far beyond the target 8GB VPS — add subreddits selectively.
- Settings read `.env` at the repo root via python-dotenv.
- `settings.py` is still the `startproject` default (`DEBUG = True`, hardcoded insecure `SECRET_KEY`) — not production-ready.
