"""
Unit Tests for Evaluation Benchmarks API & Results
--------------------------------------------------
Validates that eval/results.json exists, conforms to BenchmarksResponse schema,
and is served properly via GET /api/benchmarks.
"""

import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import BenchmarksResponse

client = TestClient(app)


def test_eval_results_json_exists_and_valid():
    results_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "eval", "results.json")
    )
    assert os.path.exists(results_path), "eval/results.json must exist after running evaluation"

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "accuracy" in data
    assert "precision" in data
    assert "recall" in data
    assert "f1_score" in data
    assert "confusion_matrix" in data
    assert data["accuracy"] >= 0.90
    assert data["f1_score"] >= 0.90


def test_get_benchmarks_endpoint():
    resp = client.get("/api/benchmarks")
    assert resp.status_code == 200
    data = resp.json()

    # Validate against Pydantic schema
    validated = BenchmarksResponse(**data)
    assert validated.accuracy >= 0.90
    assert validated.f1_score >= 0.90
    assert validated.rule_packs_loaded >= 9
    assert validated.total_eval_samples >= 12
