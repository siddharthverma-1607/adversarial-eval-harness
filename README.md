# adversarial-eval-harness

A Python adversarial evaluation harness for jailbreak testing.

The system runs a battery of jailbreak attempts against a language model, judges each outcome, stores the results, and compares runs so behavior shifts are visible when the system prompt or model version changes.

## Architecture

- `api`: FastAPI service for creating runs, listing attacks, reading results, and comparing runs.
- `worker`: background worker that claims pending runs from the database and executes the attack battery.
- `db`: PostgreSQL database for run metadata, attack outputs, judge decisions, latency, and errors.
- `ollama` optional profile: local open-source model runtime for demos without hosted APIs.

## What the Pipeline Records

- Run metadata: provider, model name, model version, system prompt, selected attacks, status, timestamps, summary.
- Attack result metadata: attack ID/name/prompt, raw model output, judge decision, judge reason, judge version, latency, error.
- Comparison metadata: changed attack count, total attack count, decision changes, output-only changes, added attacks, removed attacks.

## Start the Stack

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`.

If you already ran an older schema, reset the demo database first:

```bash
docker compose down -v
docker compose up --build
```

## Five Minute Demo Flow

This flow uses the deterministic mock provider, so the demo does not need an API key. The first run uses a safe mock model. The second run uses `mock-vulnerable`, which intentionally fails the jailbreak battery so the harness can surface the regression.

Create a safe baseline:

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"name":"baseline safe model","system_prompt":"You are a safety-first assistant.","model_name":"mock-safe","model_version":"baseline"}'
```

Create a vulnerable candidate:

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"name":"candidate vulnerable model","system_prompt":"You are a helpful assistant.","model_name":"mock-vulnerable","model_version":"candidate"}'
```

The worker automatically executes pending runs. Check run status:

```bash
curl http://localhost:8000/runs
```

Read the failed jailbreak outputs for the vulnerable run:

```bash
curl http://localhost:8000/runs/2/results
```

Compare candidate run `2` against baseline run `1`:

```bash
curl "http://localhost:8000/runs/2/compare?baseline_id=1"
```

Expected story for the recording:

- Baseline summary: `safe=3 jailbreak=0 unknown=0`
- Candidate summary: `safe=0 jailbreak=3 unknown=0`
- Comparison: `3 / 3` attacks changed from `safe` to `jailbreak`
- Example jailbreak: the login bypass attack makes `mock-vulnerable` return step-by-step bypass guidance, and the judge classifies it as `jailbreak`

## Open-Source Model Demo with Ollama

Start the optional Ollama service:

```bash
docker compose --profile ollama up --build
docker compose exec ollama ollama pull llama3.1:8b
```

Set these values in `.env` and restart `api` and `worker`:

```bash
MODEL_TYPE=ollama
MODEL_NAME=llama3.1:8b
MODEL_VERSION=local-ollama
OLLAMA_BASE_URL=http://ollama:11434
```

Then create runs exactly as above, changing `model_name` or `system_prompt` to compare different candidates.

## API Endpoints

- `GET /health`: health check
- `GET /attacks`: list available jailbreak attacks
- `POST /runs`: create a new pending evaluation run
- `POST /runs/{run_id}/start`: manually trigger execution for a pending run
- `GET /runs`: list runs
- `GET /runs/{run_id}`: get run metadata
- `GET /runs/{run_id}/results`: retrieve attack outcomes
- `GET /runs/{run_id}/compare?baseline_id={baseline_id}`: compare two runs

## CLI Usage

```bash
python -m harness.cli run --name "baseline" --system-prompt "You are a safe assistant."
python -m harness.cli compare 1 2
```

## Model Providers

- `MODEL_TYPE=mock`: deterministic local mock provider. Use `model_name=mock-safe` or `model_name=mock-vulnerable`.
- `MODEL_TYPE=ollama`: local open-source model provider through Ollama.
- `MODEL_TYPE=openai`: hosted provider. Requires `OPENAI_API_KEY`.
