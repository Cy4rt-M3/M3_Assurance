"""Centralised settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = (
        "postgresql+asyncpg://assurance:assurance@localhost:5433/assurance"
    )
    database_test_url: str = (
        "postgresql+asyncpg://assurance:assurance@localhost:5433/assurance_test"
    )

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # Service ports
    port_control_mapping: int = 10001
    port_evidence_aggregator: int = 10002
    port_gap_analyzer: int = 10003
    port_resilience_scorer: int = 10004
    port_report_generator: int = 10005
    port_framework_registry: int = 10006
    port_report_publisher: int = 10007
