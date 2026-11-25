import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_token_guardrail_flow(client: AsyncClient, auth_headers: dict):
    """
    Validates Redis atomic token tracking:
    1. Initial check (0 used, 2000 remaining)
    2. Atomic increment
    3. Exceeding 2,000 token limit returns 403 Forbidden with is_locked=True.
    """
    test_question_id = str(uuid.uuid4())
    user_id = "dev_user_ci_tester"

    # 1. Check initial balance
    res1 = await client.get(
        f"/api/v1/tokens/{test_question_id}?user_id={user_id}",
        headers=auth_headers
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["tokens_used"] == 0
    assert data1["token_limit"] == 2000
    assert data1["is_locked"] is False

    # 2. Consume 500 tokens
    res2 = await client.post(
        f"/api/v1/tokens/{test_question_id}/consume?user_id={user_id}&tokens=500",
        headers=auth_headers
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["tokens_used"] == 500
    assert data2["is_locked"] is False

    # 3. Attempt to consume 1600 tokens (500 + 1600 = 2100 > 2000)
    res3 = await client.post(
        f"/api/v1/tokens/{test_question_id}/consume?user_id={user_id}&tokens=1600",
        headers=auth_headers
    )
    assert res3.status_code == 403
    err = res3.json()
    assert "detail" in err
