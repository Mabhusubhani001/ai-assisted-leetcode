import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture(scope="session")
async def client():
    """
    Session-scoped asynchronous HTTP test client bound to FastAPI application.
    Reuses event loop across all tests to prevent asyncpg connection pool termination issues.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture
def auth_headers():
    """
    Provides mock Clerk authorization headers recognized by get_current_user in dev mode.
    """
    return {"Authorization": "Bearer dev_user_ci_tester"}
