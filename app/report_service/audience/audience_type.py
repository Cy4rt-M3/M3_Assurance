from enum import Enum


class AudienceType(str, Enum):

    EXECUTIVE = "executive"

    CISO = "ciso"

    TECHNICAL = "technical"

    COMPLIANCE = "compliance"

    DEVELOPER = "developer"

    CUSTOM = "custom"