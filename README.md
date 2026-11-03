# jibril-backend

Django + DRF API for searching the [Open American National Corpus (OANC)](https://anc.org/data/oanc/) with Elasticsearch.

## Setup

```sh
mise install && uv sync
cp .env.example .env   # set ELASTIC_PASSWORD
docker compose up -d

mkdir -p data && cd data
curl -LO https://github.com/nancyide/anc-website/releases/download/datasets-2026-09-25/OANC-1.0.1-UTF8.zip
unzip OANC-1.0.1-UTF8.zip && cd ..

uv run jibril-backend index_oanc --recreate
uv run jibril-backend runserver
```

### Kibana (local only)

```sh
docker compose --profile kibana up -d
```

Open http://localhost:5601 and log in as `elastic` with `ELASTIC_PASSWORD`. Kibana is behind a Compose profile so the VPS, which runs a plain `docker compose up -d`, never starts it.

## API

Interactive docs: http://localhost:8000/api/docs/ (Swagger UI), `/api/redoc/`, raw schema at `/api/schema/`.

`GET /api/oanc/sentences/search/`

| param | |
|---|---|
| `q` | required. Simple query string: `"exact phrase"`, `+must`, `-not`, `prefix*` |
| `stem` | `true` to match inflected forms (English analyzer) |
| `mode` | `written` / `spoken` |
| `genre` | e.g. `journal`, `fiction`, `telephone` |
| `subcorpus` | e.g. `slate`, `switchboard`, `911report` |
| `size`, `offset` | paging (max 100 per page) |

The response includes `total`, `results` (sentence, metadata, highlighted text) and `facets` (counts per mode/genre/source).
