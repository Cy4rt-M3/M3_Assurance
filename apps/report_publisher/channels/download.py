"""Download channel provider — ties a report to a local artifact."""


def notify(recipient: str) -> bool:
    """Acknowledge the delivery slot for the named recipient."""
    return bool(recipient.strip())
