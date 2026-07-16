"""
Database layer for the Threat Intel Integration Pipeline (Task 1).

Stores every CVSS + EPSS lookup permanently in the `threat_intel` table,
so scores don't have to be re-fetched every time something needs them,
and so the Weighted Scoring Engine (Task 3) can read them later.
"""

from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ThreatIntel(Base):
    """One row = one CVE's CVSS + EPSS data, as of when it was fetched."""

    __tablename__ = "threat_intel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False, index=True)

    cvss_score = Column(Float, nullable=True)
    severity = Column(String, nullable=True)
    epss_score = Column(Float, nullable=True)
    epss_percentile = Column(Float, nullable=True)

    status = Column(String, nullable=False)   # "ok" or "error"
    error = Column(String, nullable=True)

    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ThreatIntel {self.cve_id} status={self.status}>"


def get_engine(db_path: str = "threat_intel.db"):
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path: str = "threat_intel.db"):
    """Creates the threat_intel table if it doesn't exist. Safe to re-run."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = "threat_intel.db"):
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    init_db()
    print("Database initialized: threat_intel.db (table: threat_intel)")
