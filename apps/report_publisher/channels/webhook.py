"""Webhook channel provider — prepared for HTTP endpoint delivery."""


def notify(recipient: str) -> bool:
    """Validate the webhook target URL format."""
    return recipient.startswith("https://")
