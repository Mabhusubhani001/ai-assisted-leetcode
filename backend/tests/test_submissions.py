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
