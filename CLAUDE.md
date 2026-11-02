# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This is a freshly scaffolded `uv` project (`uv init --package`) with no application code yet. The only module is `src/jibril_backend/__init__.py`, which defines a placeholder `main()`. Ruff is the linter/formatter (configured under `[tool.ruff]` in `pyproject.toml`). No web framework or test runner has been chosen yet — check `pyproject.toml` before assuming any tooling exists, and update this file once those choices are made.

## Commands

The project is managed with [uv](https://docs.astral.sh/uv/) and targets Python 3.15.2, installed via [mise](https://mise.jdx.dev/) (`mise.toml`) and also pinned in `.python-version` for uv (`requires-python = ">=3.10"`). Run `mise install` first.

```sh
uv sync                      # create .venv and install the project + dependencies
uv run jibril-backend        # run the console script (jibril_backend:main)
uv add <pkg>                 # add a runtime dependency
uv add --dev <pkg>           # add a dev dependency (e.g. pytest)
uv run ruff check .          # lint (add --fix to auto-fix)
uv run ruff format .         # format
```

## Layout

- `src/` layout: the importable package is `jibril_backend` under `src/`, built with the `uv_build` backend.
- The `jibril-backend` console script in `[project.scripts]` points at `jibril_backend:main`; keep that entry point valid (or update it) when restructuring.
