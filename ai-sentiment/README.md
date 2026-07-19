# AI FastAPI Example

Simple FastAPI app demonstrating a local sentiment-analysis endpoint using Hugging Face `transformers`.

Quickstart

1. Create a virtual environment (or use `uv` to manage it):

```bash
uv venv
source .venv/bin/activate
```

2. Install dependencies

```bash
uv sync
```

3. Run the app:

```bash
uvicorn src.main:app --reload
```

Or with python3:

```bash
python src/main.py
```

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
- The project is intentionally local-only and no longer depends on OpenAI or translation APIs.
