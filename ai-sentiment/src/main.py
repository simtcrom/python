from collections import Counter
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title="AI FastAPI Example")


@app.get("/")
async def root():
    return {
        "message": "AI FastAPI example. Use /analyze to run sentiment, emotion, keywords, and summary tasks."}


# Multi-task analysis using local Hugging Face models.
class AnalyzeRequest(BaseModel):
    text: str
    tasks: list[str] | None = None


PIPELINES: dict[str, object] = {}

TASK_CONFIG = {
    "sentiment": {"task": "sentiment-analysis", "model": "distilbert-base-uncased-finetuned-sst-2-english"},
    "emotion": {"task": "text-classification", "model": "j-hartmann/emotion-english-distilroberta-base"},
}


def get_pipeline(task_name: str):
    task_name = task_name.lower()
    if task_name not in TASK_CONFIG:
        raise ValueError(f"Unsupported task: {task_name}")

    if task_name not in PIPELINES:
        config = TASK_CONFIG[task_name]
        PIPELINES[task_name] = pipeline(
            config["task"],
            model=config["model"],
            truncation=True,
        )
    return PIPELINES[task_name]


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    tokens = re.findall(r"\b[a-zA-Z']+\b", text.lower())
    filtered = [t for t in tokens if len(t) > 2]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def extractive_summary(text: str, max_sentences: int = 2) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()

    keywords = set(extract_keywords(text, top_n=10))
    sentence_scores = []
    for sentence in sentences:
        score = 0
        for word in re.findall(r"\b[a-zA-Z']+\b", sentence.lower()):
            if word in keywords:
                score += 1
        sentence_scores.append((score, sentence))

    best_sentences = [sent for _, sent in sorted(sentence_scores, reverse=True)[:max_sentences]]
    return " ".join(best_sentences).strip()


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    txt = req.text or ""
    if not txt.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    if not req.tasks:
        raise HTTPException(status_code=400, detail="No tasks requested")

    supported_tasks = {"sentiment", "emotion", "summarize", "keywords"}
    invalid = [task for task in req.tasks if task.lower() not in supported_tasks]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported tasks: {', '.join(invalid)}. Supported tasks: sentiment, emotion, summarize, keywords.",
        )

    response: dict[str, object] = {}
    for task in req.tasks:
        normalized = task.lower()
        if normalized == "keywords":
            response["keywords"] = extract_keywords(txt, top_n=5)
            continue

        if normalized == "summarize":
            response["summary"] = extractive_summary(txt, max_sentences=1)
            continue

        try:
            model = get_pipeline(normalized)
            result = model(txt)
            if not result:
                raise ValueError("No model output returned")
            output = result[0]
            response[normalized] = {
                "label": output.get("label", "unknown").lower(),
                "confidence": float(output.get("score", 0.0)),
            }
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Task '{normalized}' failed: {exc}",
            )

    return response


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
