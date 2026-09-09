"""Centralised settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    database_url: str = (
        "postgresql+asyncpg://assurance:assurance@localhost:5433/assurance"
    )
    database_test_url: str = (
        "postgresql+asyncpg://assurance:assurance@localhost:5433/assurance_test"
    )

    # Redis
    redis_url: str = "redis://127.0.0.1:6380/0"

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "m3_controls"
    mongodb_collection: str = "controls"

    # Controls source
    controls_file: str = (
        "data/controls/Pod_Nova_Framework_Registry_updated.xlsx"
    )
    controls_sheet: str = "Master Controls"

    # Service ports
    port_control_mapping: int = 10001
    port_evidence_aggregator: int = 10002
    port_gap_analyzer: int = 10003
    port_resilience_scorer: int = 10004
    port_report_generator: int = 10005
    port_framework_registry: int = 10006
    port_report_publisher: int = 10007
