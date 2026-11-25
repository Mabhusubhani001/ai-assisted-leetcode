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
