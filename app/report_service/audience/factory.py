from .executive import ExecutiveAudience
from .technical import TechnicalAudience
from .ciso import CISOAudience
from .board import BoardAudience
from .customer import CustomerAudience


class AudienceFactory:

    _audiences = {
        "executive": ExecutiveAudience,
        "technical": TechnicalAudience,
        "ciso": CISOAudience,
        "board": BoardAudience,
        "customer": CustomerAudience,
    }

    @classmethod
    def get(cls, audience_name: str):
        audience_name = (audience_name or "technical").lower()

        audience = cls._audiences.get(audience_name)

        if audience is None:
            raise ValueError(
                f"Unsupported audience '{audience_name}'. "
                f"Supported audiences: {', '.join(cls._audiences.keys())}"
            )

        return audience()