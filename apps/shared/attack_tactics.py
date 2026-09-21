"""ATT&CK technique → tactic translation for the registry definitions.

The registry controls list ATT&CK *tactics* (e.g. "Initial Access") rather
than technique ids, while verdicts carry technique ids. This module resolves
technique ids back to their tactic and name labels so tactic-based controls
match. Cyclomatic complexity ≤4.
"""

from collections.abc import Iterable

TECHNIQUE_TACTICS: dict[str, tuple[str, ...]] = {
    "T1053": ("Execution", "Persistence", "Privilege Escalation"),
    "T1059": ("Execution",),
    "T1021": ("Lateral Movement",),
    "T1027": ("Defense Evasion",),
    "T1036": ("Defense Evasion",),
    "T1048": ("Exfiltration",),
    "T1069": ("Discovery",),
    "T1078": (
        "Initial Access",
        "Defense Evasion",
        "Persistence",
        "Privilege Escalation",
    ),
    "T1098": ("Persistence", "Privilege Escalation"),
    "T1110": ("Credential Access",),
    "T1111": ("Credential Access",),
    "T1136": ("Persistence",),
    "T1187": ("Credential Access", "Lateral Movement"),
    "T1190": ("Initial Access",),
    "T1485": ("Impact",),
    "T1486": ("Impact",),
    "T1490": ("Impact",),
    "T1505": ("Persistence",),
    "T1537": ("Exfiltration",),
    "T1543": ("Persistence", "Privilege Escalation"),
    "T1547": ("Persistence", "Privilege Escalation"),
    "T1548": ("Defense Evasion", "Privilege Escalation"),
    "T1557": ("Credential Access", "Collection"),
    "T1562": ("Defense Evasion",),
    "T1566": ("Initial Access",),
    "T1567": ("Exfiltration",),
    "T1578": ("Defense Evasion",),
    "T0831": ("Collection",),
    "T0853": ("Collection", "Exfiltration"),
    "T0867": ("Discovery",),
}

TECHNIQUE_NAMES: dict[str, str] = {
    "T1078": "Valid Accounts",
}

_EMPTY: frozenset[str] = frozenset()


def tactics_for(technique_id: str) -> frozenset[str]:
    """Return the ATT&CK tactics a technique belongs to."""
    return frozenset(TECHNIQUE_TACTICS.get(technique_id, ()))


def labels_for(technique_id: str) -> frozenset[str]:
    """Expand a technique id into its id, name, and tactic labels."""
    labels = {technique_id}
    name = TECHNIQUE_NAMES.get(technique_id)
    if name is not None:
        labels.add(name)
    labels.update(tactics_for(technique_id))
    return frozenset(labels)


def effective_mapping(
    attack_mapping: Iterable[str],
    tested_techniques: set[str],
) -> list[str]:
    """Return the tested techniques a control's mapping actually covers."""
    mapping = [label.strip() for label in attack_mapping]
    resolved: list[str] = []
    for technique in sorted(tested_techniques):
        if labels_for(technique) & set(mapping):
            resolved.append(technique)
    return resolved
