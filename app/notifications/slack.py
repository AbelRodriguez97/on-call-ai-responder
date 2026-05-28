"""
Slack notification module.

Sends structured incident alerts to a Slack channel via Incoming Webhooks
when an incident requires escalation (requires_escalation: True).

If SLACK_WEBHOOK_URL is not configured, notifications are silently skipped
so the system remains functional without Slack integration.
"""

import logging
import httpx
from app.core.config import settings
from app.agents.incident_agent import IncidentReport

logger = logging.getLogger(__name__)

# Severity → emoji mapping for visual triage at a glance
SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
}


class SlackNotifier:
    """Sends incident alerts to Slack via Incoming Webhooks."""

    def __init__(self, webhook_url: str = "") -> None:
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL

    def is_configured(self) -> bool:
        """Return True if a webhook URL is available."""
        return bool(self.webhook_url)

    def send_incident_alert(
        self,
        report: IncidentReport,
        alert_id: str,
        source_service: str,
        environment: str,
    ) -> bool:
        """
        Send a structured incident alert to Slack.

        Args:
            report:         The IncidentReport produced by the AI agent.
            alert_id:       Original alert identifier.
            source_service: Name of the affected service.
            environment:    Deployment environment (production, staging, etc.)

        Returns:
            True if the message was delivered successfully, False otherwise.
        """
        if not self.is_configured():
            logger.warning(
                "SLACK_WEBHOOK_URL not configured — skipping Slack notification "
                "for alert %s", alert_id
            )
            return False

        payload = self._build_payload(report, alert_id, source_service, environment)

        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info(
                "Slack notification sent successfully for alert %s (severity: %s)",
                alert_id, report.incident_severity
            )
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                "Slack webhook returned HTTP %s for alert %s: %s",
                e.response.status_code, alert_id, e.response.text
            )
            return False

        except httpx.RequestError as e:
            logger.error(
                "Failed to reach Slack webhook for alert %s: %s",
                alert_id, str(e)
            )
            return False

    def _build_payload(
        self,
        report: IncidentReport,
        alert_id: str,
        source_service: str,
        environment: str,
    ) -> dict:
        """Build the Slack Block Kit message payload."""
        emoji = SEVERITY_EMOJI.get(report.incident_severity.upper(), "⚪")
        steps_text = "\n".join(
            f"  {i}. {step}"
            for i, step in enumerate(report.mitigation_steps, 1)
        )
        escalation_line = (
            "⚠️ *ESCALATION REQUIRED* — Contact Senior/SRE on call."
            if report.requires_escalation
            else "✅ Incident is within playbook scope. No escalation needed."
        )

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} INCIDENT ALERT — {report.incident_severity}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:*\n{source_service}"},
                        {"type": "mrkdwn", "text": f"*Environment:*\n{environment}"},
                        {"type": "mrkdwn", "text": f"*Alert ID:*\n{alert_id}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{report.incident_severity}"},
                    ],
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Root cause:*\n{report.root_cause_analysis}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Mitigation steps:*\n{steps_text}",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": escalation_line,
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💬 _{report.slack_summary}_",
                        }
                    ],
                },
            ]
        }


# Module-level instance
slack_notifier = SlackNotifier()