"""Tests for the health check endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_check_returns_online(async_client):
    """GET / should return status online with service name."""
    response = await async_client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert "service" in body
    assert "version" in body


@pytest.mark.asyncio
async def test_health_check_content_type(async_client):
    """GET / should return JSON content type."""
    response = await async_client.get("/")

    assert "application/json" in response.headers["content-type"]