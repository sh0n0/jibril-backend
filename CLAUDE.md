# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a `uv` project (`uv init --package`) using Django as the web framework with Django REST Framework (`rest_framework` in `INSTALLED_APPS`; typed via `djangorestframework-stubs`), with no Django apps yet — only the project-level config from `startproject`. Ruff is the linter/formatter (configured under `[tool.ruff]` in `pyproject.toml`). mypy (strict) with the django-stubs plugin is the type checker (`[tool.mypy]` / `[tool.django-stubs]` in `pyproject.toml`); the plugin loads `jibril_backend.settings`, so settings must stay importable for type checking to work. No test runner has been chosen yet — check `pyproject.toml` before assuming any tooling exists, and update this file once those choices are made.

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
```

## Layout

- `src/` layout: the importable package is `jibril_backend` under `src/`, built with the `uv_build` backend.
- Django project config lives directly in the package: `src/jibril_backend/{settings,urls,asgi,wsgi}.py` (`DJANGO_SETTINGS_MODULE=jibril_backend.settings`). `BASE_DIR` in `settings.py` is the repo root (three `.parent`s up), so `db.sqlite3` is created there (gitignored).
- `jibril_backend:main` in `__init__.py` is Django's `execute_from_command_line`; both the `jibril-backend` console script (`[project.scripts]`) and the root `manage.py` call it. Keep that entry point valid (or update it) when restructuring.
- `settings.py` is still the `startproject` default (`DEBUG = True`, hardcoded insecure `SECRET_KEY`) — not production-ready.
