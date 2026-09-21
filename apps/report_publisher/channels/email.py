"""Email channel provider — prepared for SMTP integration."""


def notify(recipient: str) -> bool:
    """Validate the recipient; actual SMTP dispatch is a deployment concern."""
    return "@" in recipient and "." in recipient.split("@")[-1]
