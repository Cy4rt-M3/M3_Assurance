"""
Database layer for the Weighted Scoring Engine (Task 3).

Stores the final combined risk score for a (CVE, asset) pair - i.e.
"if this specific vulnerability were exploited on this specific asset,
how risky is that combination overall?"
"""

from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class RiskScore(Base):
    """One row = one CVE + asset combination's most recent risk score."""

    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cve_id = Column(String, nullable=False, index=True)
    asset_id = Column(String, nullable=False, index=True)

    cvss_score = Column(Float, nullable=False)          # 0-10 as given
    epss_score = Column(Float, nullable=False)           # 0-1 as given
    blast_radius_score = Column(Float, nullable=False)   # 0-100 as given

    composite_score = Column(Float, nullable=False)      # final 0-100 score
    risk_band = Column(String, nullable=False)           # Low / Medium / High / Critical

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RiskScore {self.cve_id}/{self.asset_id} score={self.composite_score}>"


def get_engine(db_path: str = "risk_scores.db"):
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path: str = "risk_scores.db"):
    """Creates the risk_scores table if it doesn't exist. Safe to re-run."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = "risk_scores.db"):
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    init_db()
    print("Database initialized: risk_scores.db (table: risk_scores)")
