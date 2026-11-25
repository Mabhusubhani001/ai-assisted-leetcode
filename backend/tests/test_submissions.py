import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_optimal_code_submission_accepted(client: AsyncClient, auth_headers: dict):
    """
    Validates that a correct solution evaluates against all test cases and is ACCEPTED.
    """
    q_res = await client.get("/api/v1/questions/two-sum")
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    optimal_code = """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        lookup = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in lookup:
                return [lookup[diff], i]
            lookup[num] = i
        return []
"""
    res = await client.post(
        "/api/v1/submissions",
        headers=auth_headers,
        json={
            "question_id": q_id,
            "language_id": 71,
            "source_code": optimal_code,
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ACCEPTED"
    assert data["passed_test_cases"] == data["total_test_cases"]
    assert data["total_test_cases"] == 10

@pytest.mark.asyncio
async def test_infinite_loop_submission_tle(client: AsyncClient, auth_headers: dict):
    """
    Validates that execution timeouts prevent CPU starvation and return TIME_LIMIT_EXCEEDED.
    """
    q_res = await client.get("/api/v1/questions/two-sum")
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    infinite_loop_code = """import time
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        while True:
            time.sleep(0.05)
"""
    res = await client.post(
        "/api/v1/submissions",
        headers=auth_headers,
        json={
            "question_id": q_id,
            "language_id": 71,
            "source_code": infinite_loop_code,
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "TIME_LIMIT_EXCEEDED"

@pytest.mark.asyncio
async def test_get_submission_history_ordered(client: AsyncClient, auth_headers: dict):
    """
    Validates that a student can retrieve their past submission history for a problem,
    ordered newest-first (descending by created_at).
    """
    q_res = await client.get("/api/v1/questions/two-sum")
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    res = await client.get(f"/api/v1/submissions/history/{q_id}", headers=auth_headers)
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    assert len(history) >= 2

    # Verify descending chronological order
    for i in range(len(history) - 1):
        assert history[i]["created_at"] >= history[i + 1]["created_at"]

    # Verify data integrity
    first = history[0]
    assert first["question_id"] == q_id
    assert first["user_id"] == "dev_user_ci_tester"
    assert "status" in first
    assert "source_code" in first

@pytest.mark.asyncio
async def test_get_submissions_catalog_summary(client: AsyncClient, auth_headers: dict):
    """
    Validates that the aggregated submission summary computes correct
    SOLVED status, total solved count, and attempts per question.
    """
    q_res = await client.get("/api/v1/questions/two-sum")
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    res = await client.get("/api/v1/submissions/summary", headers=auth_headers)
    assert res.status_code == 200
    summary = res.json()

    assert "total_solved" in summary
    assert "total_attempted" in summary
    assert "progress" in summary
    assert summary["total_solved"] >= 1
    assert summary["total_attempted"] >= 1

    progress_entry = summary["progress"].get(q_id)
    assert progress_entry is not None
    assert progress_entry["status"] == "SOLVED"
    assert progress_entry["attempts"] >= 2
    assert "last_submitted_at" in progress_entry

@pytest.mark.asyncio
async def test_submission_history_unauthenticated_rejected(client: AsyncClient):
    """
    Validates that unauthenticated requests without authorization headers are blocked.
    """
    q_res = await client.get("/api/v1/questions/two-sum")
    assert q_res.status_code == 200
    q_id = q_res.json()["id"]

    res = await client.get(f"/api/v1/submissions/history/{q_id}")
    assert res.status_code in (401, 403)

