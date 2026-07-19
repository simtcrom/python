# AI FastAPI Example

Simple FastAPI app demonstrating a local sentiment-analysis endpoint using Hugging Face `transformers`.

Quickstart

1. Create a virtual environment (or use `uv` to manage it):

```bash
python -m venv .venv
source .venv/bin/activate
# or with uv: uv venv && source .venv/bin/activate
```

2. Install dependencies

With `uv` (preferred):

```bash
uv sync
```

Or with pip:

```bash
pip install fastapi uvicorn transformers torch
```

3. Run the app:

```bash
uvicorn src.main:app --reload
```

The app entrypoint now lives in the src folder, and the project root includes a small compatibility wrapper so this command still works.

4. Quick test once server is running:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I will never work with him again.","tasks":["sentiment","emotion","summarize","keywords"]}'
```

5. Unit test:

```bash
pytest
```

Notes

- The `/analyze` endpoint supports multi-task analysis: `sentiment`, `emotion`, `summarize`, and `keywords`.
- The `/sentiment` endpoint is still available for single-task sentiment-only requests.
- The project is intentionally local-only and no longer depends on OpenAI or translation APIs.
- If the model fails to load, ensure `transformers` and `torch` are installed via `uv sync`.
