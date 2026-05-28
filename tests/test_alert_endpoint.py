"""Tests for the POST /api/v1/alerts endpoint."""

import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_process_alert_returns_200(async_client, sample_alert_payload):
    """POST /api/v1/alerts with a valid payload should return 200."""
    response = await async_client.post("/api/v1/alerts", json=sample_alert_payload)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_process_alert_returns_incident_report_schema(async_client, sample_alert_payload):
    """Response should match the IncidentReport schema with all required fields."""
    response = await async_client.post("/api/v1/alerts", json=sample_alert_payload)

    body = response.json()
    assert "incident_severity" in body
    assert "root_cause_analysis" in body
    assert "mitigation_steps" in body
    assert "requires_escalation" in body
    assert "slack_summary" in body


@pytest.mark.asyncio
async def test_process_alert_severity_is_valid_enum(async_client, sample_alert_payload):
    """incident_severity must be one of the expected values."""
    response = await async_client.post("/api/v1/alerts", json=sample_alert_payload)

    body = response.json()
    assert body["incident_severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


@pytest.mark.asyncio
async def test_process_alert_mitigation_steps_is_list(async_client, sample_alert_payload):
    """mitigation_steps must be a non-empty list."""
    response = await async_client.post("/api/v1/alerts", json=sample_alert_payload)

    body = response.json()
    assert isinstance(body["mitigation_steps"], list)
    assert len(body["mitigation_steps"]) > 0


@pytest.mark.asyncio
async def test_process_alert_requires_escalation_is_bool(async_client, sample_alert_payload):
    """requires_escalation must be a boolean."""
    response = await async_client.post("/api/v1/alerts", json=sample_alert_payload)

    body = response.json()
    assert isinstance(body["requires_escalation"], bool)


@pytest.mark.asyncio
async def test_process_alert_missing_required_field_returns_422(async_client):
    """Missing required field should return 422 Unprocessable Entity."""
    incomplete_payload = {
        "alert_id": "ALR-TEST-002",
        # missing source_service, raw_message, environment
    }
    response = await async_client.post("/api/v1/alerts", json=incomplete_payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_process_alert_empty_payload_returns_422(async_client):
    """Empty payload should return 422."""
    response = await async_client.post("/api/v1/alerts", json={})

    assert response.status_code == 422