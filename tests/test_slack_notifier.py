"""Tests for the SlackNotifier."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.incident_agent import IncidentReport
from app.notifications.slack import SlackNotifier


@pytest.fixture
def sample_report():
    return IncidentReport(
        incident_severity="CRITICAL",
        root_cause_analysis="Database pool exhausted.",
        mitigation_steps=["Restart service.", "Check Datadog."],
        requires_escalation=True,
        slack_summary="CRITICAL: DB pool exhausted. Escalation required.",
    )


@pytest.fixture
def notifier_with_url():
    return SlackNotifier(webhook_url="https://hooks.slack.com/services/TEST/TEST/TEST")


@pytest.fixture
def notifier_without_url():
    return SlackNotifier(webhook_url="")


def test_is_configured_true_when_url_set(notifier_with_url):
    assert notifier_with_url.is_configured() is True


def test_is_configured_false_when_no_url(notifier_without_url):
    assert notifier_without_url.is_configured() is False


def test_send_returns_false_when_not_configured(notifier_without_url, sample_report):
    """Should skip silently and return False if webhook is not configured."""
    result = notifier_without_url.send_incident_alert(
        report=sample_report,
        alert_id="ALR-001",
        source_service="Keycloak",
        environment="production",
    )
    assert result is False


def test_send_returns_true_on_success(notifier_with_url, sample_report):
    """Should return True when Slack responds with 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    with patch("app.notifications.slack.httpx.post", return_value=mock_response):
        result = notifier_with_url.send_incident_alert(
            report=sample_report,
            alert_id="ALR-001",
            source_service="Keycloak",
            environment="production",
        )
    assert result is True


def test_send_returns_false_on_http_error(notifier_with_url, sample_report):
    """Should return False and not raise when Slack returns an HTTP error."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("app.notifications.slack.httpx.post") as mock_post:
        mock_post.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_response
        )
        result = notifier_with_url.send_incident_alert(
            report=sample_report,
            alert_id="ALR-001",
            source_service="Keycloak",
            environment="production",
        )
    assert result is False


def test_send_returns_false_on_network_error(notifier_with_url, sample_report):
    """Should return False and not raise when network is unreachable."""
    import httpx

    with patch("app.notifications.slack.httpx.post") as mock_post:
        mock_post.side_effect = httpx.RequestError("Connection refused")
        result = notifier_with_url.send_incident_alert(
            report=sample_report,
            alert_id="ALR-001",
            source_service="Keycloak",
            environment="production",
        )
    assert result is False


def test_payload_contains_severity(notifier_with_url, sample_report):
    """The built payload should include the severity in the header."""
    payload = notifier_with_url._build_payload(
        report=sample_report,
        alert_id="ALR-001",
        source_service="Keycloak",
        environment="production",
    )
    header_text = payload["blocks"][0]["text"]["text"]
    assert "CRITICAL" in header_text


def test_payload_escalation_line_when_required(notifier_with_url, sample_report):
    """Escalation warning should appear when requires_escalation is True."""
    payload = notifier_with_url._build_payload(
        report=sample_report,
        alert_id="ALR-001",
        source_service="Keycloak",
        environment="production",
    )
    # The escalation section is the second-to-last block
    escalation_block = payload["blocks"][-2]
    assert "ESCALATION REQUIRED" in escalation_block["text"]["text"]


def test_payload_no_escalation_line_when_not_required(notifier_with_url):
    """No escalation warning when requires_escalation is False."""
    report = IncidentReport(
        incident_severity="LOW",
        root_cause_analysis="Minor config issue.",
        mitigation_steps=["Check logs."],
        requires_escalation=False,
        slack_summary="LOW: Minor issue, no escalation needed.",
    )
    payload = notifier_with_url._build_payload(
        report=report,
        alert_id="ALR-002",
        source_service="Keycloak",
        environment="staging",
    )
    escalation_block = payload["blocks"][-2]
    assert "No escalation needed" in escalation_block["text"]["text"]