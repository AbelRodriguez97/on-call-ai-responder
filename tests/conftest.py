"""
Shared fixtures for the test suite.

Strategy:
- We mock external services (Gemini API) to keep tests fast and free.
- We use the real Qdrant in-memory instance since it requires no server.
- We set a dummy GEMINI_API_KEY env var to prevent Settings from raising ValueError.
"""

import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Set dummy env vars BEFORE importing anything from the app
# This prevents Settings from raising ValueError during import
os.environ.setdefault("GEMINI_API_KEY", "test-api-key-dummy")


@pytest.fixture
def sample_alert_payload() -> dict:
    """A realistic alert payload for endpoint tests."""
    return {
        "alert_id": "ALR-TEST-001",
        "source_service": "Keycloak-Identity-Provider",
        "raw_message": "CRITICAL: AUTH_TIMEOUT_500. Database pool exhausted.",
        "environment": "production",
    }


@pytest.fixture
def sample_incident_report() -> dict:
    """A realistic IncidentReport response payload."""
    return {
        "incident_severity": "CRITICAL",
        "root_cause_analysis": "Database connection pool exhausted due to AUTH_TIMEOUT_500.",
        "mitigation_steps": [
            "Execute db_flush_connections.sh immediately.",
            "Restart Keycloak service if connections do not recover.",
            "Monitor connection pool metrics in Datadog.",
        ],
        "requires_escalation": True,
        "slack_summary": "CRITICAL: Keycloak AUTH_TIMEOUT_500 — DB pool exhausted. Escalation required.",
    }


@pytest.fixture
def mock_gemini_response(sample_incident_report):
    """Mocked Gemini API response returning a valid IncidentReport JSON."""
    import json
    mock_response = MagicMock()
    mock_response.text = json.dumps(sample_incident_report)
    return mock_response


@pytest.fixture
def app_with_mocked_agent(mock_gemini_response):
    """
    FastAPI app instance with Gemini fully mocked.
    The lifespan runs (indexing playbooks into real in-memory Qdrant).
    """
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_client_cls.return_value = mock_client

        from app.main import app
        yield app


@pytest_asyncio.fixture
async def async_client(app_with_mocked_agent):
    """AsyncClient wired to the FastAPI app via ASGI transport."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mocked_agent),
        base_url="http://test"
    ) as client:
        yield client