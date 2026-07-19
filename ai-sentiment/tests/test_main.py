import os
import sys
import json

import pytest
from fastapi.testclient import TestClient

# Add src directory to path and import main
HERE = os.path.dirname(__file__)
SRC = os.path.normpath(os.path.join(HERE, "..", "src"))
sys.path.insert(0, SRC)

import main

client = TestClient(main.app)


def test_extract_keywords_basic():
    text = "Python testing is fun. Testing tests code and finds bugs."
    keywords = main.extract_keywords(text, top_n=3)
    assert isinstance(keywords, list)
    assert "testing" in keywords or "python" in keywords


def test_extractive_summary_reduces_sentences():
    text = (
        "Python is a great language. "
        "Unit tests help ensure code quality. "
        "Writing tests can catch bugs early."
    )
    summary = main.extractive_summary(text, max_sentences=1)
    assert isinstance(summary, str)
    # summary should be shorter or equal to one sentence
    assert len(summary.split('.')) <= 2


def test_get_pipeline_unsupported():
    with pytest.raises(ValueError):
        main.get_pipeline("unsupported-task-name")


def test_analyze_keywords_endpoint():
    payload = {"text": "fast api fast tests test api", "tasks": ["keywords"]}
    res = client.post("/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "keywords" in data
    assert isinstance(data["keywords"], list)


def test_analyze_sentiment_endpoint_monkeypatched(monkeypatch):
    # Replace get_pipeline with a fake model provider
    def fake_get_pipeline(task_name: str):
        def model(text: str):
            return [{"label": "POSITIVE", "score": 0.95}]

        return model

    monkeypatch.setattr(main, "get_pipeline", fake_get_pipeline)

    payload = {"text": "I love writing tests.", "tasks": ["sentiment"]}
    res = client.post("/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "sentiment" in data
    assert data["sentiment"]["label"] == "positive"
    assert isinstance(data["sentiment"]["confidence"], float)


def test_analyze_bad_requests():
    # no text
    res = client.post("/analyze", json={"text": "", "tasks": ["keywords"]})
    assert res.status_code == 400

    # no tasks
    res = client.post("/analyze", json={"text": "hello", "tasks": []})
    assert res.status_code == 400

    # unsupported task
    res = client.post("/analyze", json={"text": "hello", "tasks": ["foo"]})
    assert res.status_code == 400
