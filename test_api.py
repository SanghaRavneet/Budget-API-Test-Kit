"""
Regression tests for the Mock Budget API.

These tests call the API over HTTP, so the server must be running first:
    Terminal 1:  uvicorn main:app --reload
    Terminal 2:  pytest -v

All data is synthetic. AI-assisted: drafted with Claude and reviewed by the author.
"""

import time

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 5  # seconds

REQUIRED_FIELDS = {
    "id": int,
    "entity": str,
    "account": str,
    "period": str,
    "scenario": str,
    "amount": (int, float),
}


def valid_payload(**overrides):
    """A valid budget line. Override any field to build a variation."""
    payload = {
        "entity": "TestEntity",
        "account": "Revenue",
        "period": "Mar-2027",
        "scenario": "Budget",
        "amount": 1000.0,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def created_budget():
    """Create a budget line for a test, then delete it afterwards."""
    response = requests.post(f"{BASE_URL}/budgets", json=valid_payload(), timeout=TIMEOUT)
    assert response.status_code == 201, "Setup failed: could not create a budget line"
    budget = response.json()
    yield budget
    requests.delete(f"{BASE_URL}/budgets/{budget['id']}", timeout=TIMEOUT)


# ---------- Health ----------

def test_health_returns_ok():
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- GET /budgets ----------

def test_list_budgets_returns_200_and_a_list():
    response = requests.get(f"{BASE_URL}/budgets", timeout=TIMEOUT)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_budgets_items_match_schema():
    items = requests.get(f"{BASE_URL}/budgets", timeout=TIMEOUT).json()
    assert len(items) > 0, "Expected at least one budget line (seed data)"
    for item in items:
        for field, expected_type in REQUIRED_FIELDS.items():
            assert field in item, f"Missing field '{field}' in {item}"
            assert isinstance(item[field], expected_type), (
                f"Field '{field}' has wrong type in {item}"
            )


def test_filter_by_entity_returns_only_that_entity():
    response = requests.get(f"{BASE_URL}/budgets", params={"entity": "Canada"}, timeout=TIMEOUT)
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert all(item["entity"] == "Canada" for item in items)


def test_filter_by_scenario_returns_only_that_scenario():
    response = requests.get(f"{BASE_URL}/budgets", params={"scenario": "Forecast"}, timeout=TIMEOUT)
    assert response.status_code == 200
    items = response.json()
    assert len(items) > 0
    assert all(item["scenario"] == "Forecast" for item in items)


def test_filter_with_no_matches_returns_empty_list():
    response = requests.get(f"{BASE_URL}/budgets", params={"entity": "Atlantis"}, timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json() == []


def test_list_budgets_responds_quickly():
    start = time.perf_counter()
    requests.get(f"{BASE_URL}/budgets", timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"Response took {elapsed:.2f}s (limit 1.0s)"


# ---------- GET /budgets/{id} ----------

def test_get_budget_by_id_returns_matching_record(created_budget):
    response = requests.get(f"{BASE_URL}/budgets/{created_budget['id']}", timeout=TIMEOUT)
    assert response.status_code == 200
    assert response.json() == created_budget


def test_get_nonexistent_budget_returns_404():
    response = requests.get(f"{BASE_URL}/budgets/999999", timeout=TIMEOUT)
    assert response.status_code == 404


def test_get_budget_with_non_numeric_id_returns_422():
    response = requests.get(f"{BASE_URL}/budgets/abc", timeout=TIMEOUT)
    assert response.status_code == 422


# ---------- POST /budgets ----------

def test_create_budget_returns_201_and_echoes_fields(created_budget):
    expected = valid_payload()
    for field, value in expected.items():
        assert created_budget[field] == value
    assert isinstance(created_budget["id"], int)


def test_created_budget_can_be_retrieved(created_budget):
    listing = requests.get(f"{BASE_URL}/budgets", timeout=TIMEOUT).json()
    assert created_budget["id"] in [item["id"] for item in listing]


def test_create_budget_missing_field_returns_422():
    payload = valid_payload()
    del payload["account"]
    response = requests.post(f"{BASE_URL}/budgets", json=payload, timeout=TIMEOUT)
    assert response.status_code == 422


def test_create_budget_with_text_amount_returns_422():
    response = requests.post(
        f"{BASE_URL}/budgets", json=valid_payload(amount="not a number"), timeout=TIMEOUT
    )
    assert response.status_code == 422


# ---------- POST /budgets: validation checks ----------
# The API does little validation yet. These tests assert what a finance
# system SHOULD do, so some are expected to fail. Each failure is a bug
# to report.

def test_create_budget_rejects_negative_amount():
    response = requests.post(
        f"{BASE_URL}/budgets", json=valid_payload(amount=-500.0), timeout=TIMEOUT
    )
    assert response.status_code == 422, (
        f"Negative amount was accepted with status {response.status_code}"
    )


def test_create_budget_rejects_empty_entity():
    response = requests.post(
        f"{BASE_URL}/budgets", json=valid_payload(entity=""), timeout=TIMEOUT
    )
    assert response.status_code == 422, (
        f"Empty entity was accepted with status {response.status_code}"
    )


def test_create_budget_rejects_invalid_period():
    response = requests.post(
        f"{BASE_URL}/budgets", json=valid_payload(period="banana"), timeout=TIMEOUT
    )
    assert response.status_code == 422, (
        f"Invalid period was accepted with status {response.status_code}"
    )


def test_create_budget_rejects_unknown_scenario():
    response = requests.post(
        f"{BASE_URL}/budgets", json=valid_payload(scenario="Fantasy"), timeout=TIMEOUT
    )
    assert response.status_code == 422, (
        f"Unknown scenario was accepted with status {response.status_code}"
    )


# ---------- DELETE /budgets/{id} ----------

def test_delete_budget_returns_204_and_removes_record():
    created = requests.post(f"{BASE_URL}/budgets", json=valid_payload(), timeout=TIMEOUT).json()
    delete_response = requests.delete(f"{BASE_URL}/budgets/{created['id']}", timeout=TIMEOUT)
    assert delete_response.status_code == 204

    get_response = requests.get(f"{BASE_URL}/budgets/{created['id']}", timeout=TIMEOUT)
    assert get_response.status_code == 404


def test_delete_nonexistent_budget_returns_404():
    response = requests.delete(f"{BASE_URL}/budgets/999999", timeout=TIMEOUT)
    assert response.status_code == 404