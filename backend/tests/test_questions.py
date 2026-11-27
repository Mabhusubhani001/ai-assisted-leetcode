import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_questions_catalog(client: AsyncClient):
    """
    Validates question catalog retrieval and confirms seeded questions exist.
    """
    response = await client.get("/api/v1/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 3
    slugs = [q["slug"] for q in questions]
    assert "two-sum" in slugs
    assert "valid-parentheses" in slugs
    assert "reverse-linked-list" in slugs

@pytest.mark.asyncio
async def test_question_detail_and_hidden_test_case_isolation(client: AsyncClient):
    """
    Validates question detail schema and strictly enforces that NO hidden
    test cases or internal test case fields are exposed to the public API.
    """
    response = await client.get("/api/v1/questions/two-sum")
    assert response.status_code == 200
    question = response.json()
    assert question["slug"] == "two-sum"
    
    # 3 public test cases only
    test_cases = question["test_cases"]
    assert len(test_cases) == 3

    # Security assertion: ensure is_hidden is never exposed
    for tc in test_cases:
        assert "is_hidden" not in tc

@pytest.mark.asyncio
async def test_admin_create_question_unauthorized(client: AsyncClient):
    """
    Ensures that unauthenticated requests or invalid admin keys cannot
    create or upload questions.
    """
    payload = {
        "title": "Unauthorized Test Problem",
        "slug": "unauthorized-test-problem",
        "difficulty": "easy",
        "description": "Test description",
        "starter_code": {},
        "test_cases": []
    }
    # No header
    res = await client.post("/api/v1/questions", json=payload)
    assert res.status_code == 403

    # Invalid header
    res = await client.post(
        "/api/v1/questions",
        json=payload,
        headers={"X-Admin-Key": "wrong_key"}
    )
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_admin_create_question_authorized(client: AsyncClient):
    """
    Verifies that requests with the valid X-Admin-Key header can upload
    questions with both public and hidden test cases, and that subsequent
    public GET requests isolate hidden cases.
    """
    from app.core.config import settings

    payload = {
        "title": "Automated Unit Test Problem",
        "slug": "automated-unit-test-problem",
        "difficulty": "medium",
        "description": "Problem created via admin endpoint test.",
        "starter_code": {"python": "class Solution:\n    pass\n"},
        "memory_limit_mb": 256,
        "time_limit_sec": 2.0,
        "is_published": True,
        "test_cases": [
            {"stdin": "1 2\n", "expected_stdout": "3\n", "is_hidden": False},
            {"stdin": "5 5\n", "expected_stdout": "10\n", "is_hidden": True}
        ]
    }

    res = await client.post(
        "/api/v1/questions",
        json=payload,
        headers={"X-Admin-Key": settings.ADMIN_API_KEY}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == "automated-unit-test-problem"
    # Public view returned in response only contains visible test cases
    assert len(data["test_cases"]) == 1
    assert data["test_cases"][0]["stdin"] == "1 2\n"

    # Verify public GET endpoint also only returns the 1 public test case
    get_res = await client.get("/api/v1/questions/automated-unit-test-problem")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data["test_cases"]) == 1
    assert "is_hidden" not in get_data["test_cases"][0]
