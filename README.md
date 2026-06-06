# adversarial-eval-harness

A Python-based adversarial evaluation harness for model jailbreak testing.

The system runs a battery of jailbreak attempts against a language model, judges each outcome, stores results in a database, and exposes comparisons between runs when the prompt or model version changes.

## Architecture

- `api` service: FastAPI app that creates runs, retrieves run history, and compares results.
- `worker` service: background process that polls the database for pending runs and executes them.
- `db` service: PostgreSQL database that stores run metadata and attack results.

## Features

- Attack battery with built-in jailbreak attempts
- Pluggable model client with `mock` default and optional OpenAI support
- Automatic run execution through a worker process
- Result classification and comparison between two runs
- Docker Compose pipeline for full-stack evaluation

## Getting started

1. Copy `.env.example` to `.env` and adjust values if needed.
2. Start the stack:

```bash
docker-compose up --build
```

3. The API is available at `http://localhost:8000`.

## API Endpoints

- `GET /health` — health check
- `GET /attacks` — list available jailbreak attacks
- `POST /runs` — create a new evaluation run
- `POST /runs/{run_id}/start` — trigger execution for a run
- `GET /runs` — list past runs
- `GET /runs/{run_id}` — get details for a single run
- `GET /runs/{run_id}/results` — retrieve attack outcomes
- `GET /runs/{run_id}/compare?baseline_id={baseline_id}` — compare two runs

## CLI Usage

Use the bundled CLI for local execution:

```bash
python -m harness.cli run --name "baseline" --system-prompt "You are a safe assistant."
python -m harness.cli compare 1 2
```

## Model configuration

By default, the harness uses a `mock` model client and safe heuristics.
To enable OpenAI, set `MODEL_TYPE=openai` and `OPENAI_API_KEY` in `.env`.

## Notes

- `docker-compose.yml` starts three services: `db`, `api`, and `worker`.
- The worker monitors the database for pending runs and executes them.
- Comparison surfaces how classification changed between two completed runs.
