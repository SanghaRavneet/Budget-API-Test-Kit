"""
Mock Budget API: a small FastAPI app that imitates a finance planning service.
All data is synthetic and held in memory. It resets whenever the server restarts.

Run with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.

AI-assisted: this file was drafted with Claude and reviewed by the author.
"""

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Mock Budget API",
    description="Synthetic finance planning API used to practice API regression testing.",
    version="0.1.0",
)


# ---------- Data models ----------

MONTH_PATTERN = r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}$"


class BudgetIn(BaseModel):
    """Fields a client sends when creating a budget line."""
    entity: str = Field(min_length=1)                           # fixes #2
    account: str = Field(min_length=1)
    period: str = Field(pattern=MONTH_PATTERN)                  # fixes #3
    scenario: Literal["Budget", "Forecast", "Actual"]           # fixes #4
    amount: float = Field(ge=0)                                 # fixes #1


class Budget(BudgetIn):
    """A stored budget line: the input fields plus a server-assigned id."""
    id: int


# ---------- In-memory "database" ----------

budgets: dict[int, Budget] = {}
next_id = 1


def _add(entity: str, account: str, period: str, scenario: str, amount: float) -> Budget:
    """Helper that stores a budget line and assigns it the next id."""
    global next_id
    item = Budget(
        id=next_id,
        entity=entity,
        account=account,
        period=period,
        scenario=scenario,
        amount=amount,
    )
    budgets[next_id] = item
    next_id += 1
    return item


def _seed() -> None:
    """Load a few synthetic rows so GET endpoints return data right away."""
    _add("Canada", "Revenue", "Jan-2027", "Budget", 125000.00)
    _add("Canada", "Salaries", "Jan-2027", "Budget", 62000.00)
    _add("US_East", "Revenue", "Jan-2027", "Forecast", 98000.50)
    _add("US_East", "Marketing", "Feb-2027", "Budget", 15000.00)
    _add("UK", "Revenue", "Feb-2027", "Actual", 71250.75)


_seed()


# ---------- Endpoints ----------

@app.get("/health")
def health():
    """Simple check that the service is up."""
    return {"status": "ok"}


@app.get("/budgets", response_model=list[Budget])
def list_budgets(
    entity: Optional[str] = Query(None, description="Filter by entity"),
    scenario: Optional[str] = Query(None, description="Filter by scenario"),
):
    """Return all budget lines, optionally filtered by entity and/or scenario."""
    results = list(budgets.values())
    if entity is not None:
        results = [b for b in results if b.entity == entity]
    if scenario is not None:
        results = [b for b in results if b.scenario == scenario]
    return results


@app.get("/budgets/{budget_id}", response_model=Budget)
def get_budget(budget_id: int):
    """Return one budget line by id, or 404 if it does not exist."""
    if budget_id not in budgets:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budgets[budget_id]


@app.post("/budgets", response_model=Budget, status_code=201)
def create_budget(payload: BudgetIn):
    """Create a new budget line and return it with its new id."""
    return _add(
        payload.entity,
        payload.account,
        payload.period,
        payload.scenario,
        payload.amount,
    )


@app.delete("/budgets/{budget_id}", status_code=204)
def delete_budget(budget_id: int):
    """Delete a budget line, or 404 if it does not exist."""
    if budget_id not in budgets:
        raise HTTPException(status_code=404, detail="Budget not found")
    del budgets[budget_id]