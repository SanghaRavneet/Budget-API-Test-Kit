# Budget API Test Kit

A small project that practises API regression testing. It contains a mock REST API for a fake finance planning app, an automated test suite, and a written record of the bugs found and fixed.

All data is synthetic. No real or client data is used anywhere.

**AI-assisted:** the API and the first draft of the tests were written with Claude. I ran the tests, reproduced each bug by hand, wrote the bug reports, applied the fix, and verified it.

## What's in this repo

| File | Purpose |
|---|---|
| `main.py` | Mock Budget API (FastAPI, in-memory data) |
| `test_api.py` | 20 pytest regression tests that call the API over HTTP |
| `TEST_RESULTS.md` | Before/after pass/fail record and the defects found |
| `results_before.txt` | Raw test output before the fix (16 passed, 4 failed) |
| `results_after.txt` | Raw test output after the fix (20 passed) |

## The API

Each budget line has an `entity`, `account`, `period`, `scenario`, and `amount`, modelled loosely on finance planning concepts.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check the service is up |
| GET | `/budgets` | List budget lines (optional `entity` and `scenario` filters) |
| GET | `/budgets/{id}` | Get one budget line, or 404 |
| POST | `/budgets` | Create a budget line, or 422 if the input is invalid |
| DELETE | `/budgets/{id}` | Delete a budget line, or 404 |

Valid input rules for `POST /budgets`:
- `entity` and `account` must not be empty
- `period` must look like `Mar-2027` (three-letter month, dash, four-digit year)
- `scenario` must be `Budget`, `Forecast`, or `Actual`
- `amount` must be a number that is zero or greater

## Setup

Requires Python 3.10 or newer and Git.

```
git clone https://github.com/SanghaRavneet/budget-api-test-kit.git
cd budget-api-test-kit
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pytest requests
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Run the API

```
uvicorn main:app --reload
```

The API interactive docs are at http://127.0.0.1:8000/docs.

The data lives in memory and resets every time the server restarts.

## Run the tests

The tests call the live API, so the server must be running first. You need two terminals.

1. **Terminal 1:** start the server as shown above and leave it running.
2. **Terminal 2:** activate the environment, then run:

```
source .venv/bin/activate
pytest -v
```

All 20 tests should pass.

## Testing record

This project followed a simple find, report, fix, and retest loop:

1. The first test run found 4 failures: `POST /budgets` accepted invalid input and returned `201` instead of `422`.
2. Each bug was reproduced by hand with `curl` and filed as a GitHub issue with steps, expected result, actual result, and evidence (issues #1 to #4).
3. A single pull request added the validation and closed all four issues.
4. The suite was rerun to confirm 20 of 20 passing.

See [TEST_RESULTS.md](TEST_RESULTS.md) for the full pass/fail table and known limitations.

## Known limitations

- The tests need a running server and do not start one themselves.
- Whitespace-only values (such as `"   "` for `entity`) are still accepted.
- Authentication, concurrency, and persistence are not tested.
