# Test Results

Pass/fail record for the Mock Budget API regression suite (`test_api.py`).
All data is synthetic.

## Summary

| Run | Commit | Passed | Failed | Total |
|---|---|---|---|---|
| Before fix | `59e8f61` | 16 | 4 | 20 |
| After fix | `17f23b6` | 20 | 0 | 20 |

Raw output: [`results_before.txt`](results_before.txt) and [`results_after.txt`](results_after.txt).

## Environment

- Python 3.12.6, pytest 9.2.0, FastAPI 0.165.0, macOS
- Server: `uvicorn main:app --reload` on `http://127.0.0.1:8000`
- Tests run over HTTP with `requests` against the live server

## Results by test

| # | Test | Before | After | Issue |
|---|---|---|---|---|
| 1 | `test_health_returns_ok` | Pass | Pass | |
| 2 | `test_list_budgets_returns_200_and_a_list` | Pass | Pass | |
| 3 | `test_list_budgets_items_match_schema` | Pass | Pass | |
| 4 | `test_filter_by_entity_returns_only_that_entity` | Pass | Pass | |
| 5 | `test_filter_by_scenario_returns_only_that_scenario` | Pass | Pass | |
| 6 | `test_filter_with_no_matches_returns_empty_list` | Pass | Pass | |
| 7 | `test_list_budgets_responds_quickly` | Pass | Pass | |
| 8 | `test_get_budget_by_id_returns_matching_record` | Pass | Pass | |
| 9 | `test_get_nonexistent_budget_returns_404` | Pass | Pass | |
| 10 | `test_get_budget_with_non_numeric_id_returns_422` | Pass | Pass | |
| 11 | `test_create_budget_returns_201_and_echoes_fields` | Pass | Pass | |
| 12 | `test_created_budget_can_be_retrieved` | Pass | Pass | |
| 13 | `test_create_budget_missing_field_returns_422` | Pass | Pass | |
| 14 | `test_create_budget_with_text_amount_returns_422` | Pass | Pass | |
| 15 | `test_create_budget_rejects_negative_amount` | **Fail** | Pass | #1 |
| 16 | `test_create_budget_rejects_empty_entity` | **Fail** | Pass | #2 |
| 17 | `test_create_budget_rejects_invalid_period` | **Fail** | Pass | #3 |
| 18 | `test_create_budget_rejects_unknown_scenario` | **Fail** | Pass | #4 |
| 19 | `test_delete_budget_returns_204_and_removes_record` | Pass | Pass | |
| 20 | `test_delete_nonexistent_budget_returns_404` | Pass | Pass | |

## Defects found and fixed

All four defects were in `POST /budgets`, which accepted invalid input and returned `201 Created` instead of `422`.

| Issue | Defect | Fix |
|---|---|---|
| #1 | Negative `amount` accepted | `amount: float = Field(ge=0)` |
| #2 | Empty `entity` accepted | `entity: str = Field(min_length=1)` |
| #3 | Invalid `period` (e.g. "banana") accepted | `period` must match `Mon-YYYY` |
| #4 | Unknown `scenario` (e.g. "Fantasy") accepted | `scenario` limited to Budget, Forecast, Actual |

Each defect was reproduced by hand with `curl` and by an automated test before the fix, then verified by the same test after it.

## Known limitations

- **Not covered by tests:** `account` also gained a `min_length=1` check in the fix, but no test checks it.
- **Gaps in the new validation:** a whitespace-only `entity` (e.g. `"   "`) still passes, and the period pattern checks format only, so a value like `Mar-0000` is accepted.
- **Test data left behind:** the tests that create records clean up after themselves, but the four failing tests in the "before" run created records that were never deleted, because the API wrongly accepted them. Restarting the server clears the in-memory data.
- **Scope:** the suite requires a running server, uses synthetic data only, and does not test authentication, concurrency, or persistence.