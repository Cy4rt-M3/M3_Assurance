"""
Database layer for the Blast Radius Engine (Task 2).

Stores one row per asset, with its exposure/criticality/connectivity
inputs and the calculated Blast Radius score. Re-scoring an asset
updates its existing row (see save_result in blast_radius_engine.py)
rather than creating duplicates.
"""

from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class BlastRadiusScore(Base):
    """One row = one asset's most recent Blast Radius calculation."""

    __tablename__ = "blast_radius_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String, nullable=False, unique=True, index=True)

    exposure_level = Column(String, nullable=False)
    criticality = Column(String, nullable=False)
    connected_assets_count = Column(Integer, nullable=False)

    exposure_score = Column(Float, nullable=False)
    criticality_score = Column(Float, nullable=False)
    connectivity_score = Column(Float, nullable=False)
    blast_radius_score = Column(Float, nullable=False)

    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BlastRadiusScore {self.asset_id} score={self.blast_radius_score}>"


def get_engine(db_path: str = "blast_radius.db"):
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path: str = "blast_radius.db"):
    """Creates the blast_radius_scores table if it doesn't exist. Safe to re-run."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path: str = "blast_radius.db"):
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    init_db()
    print("Database initialized: blast_radius.db (table: blast_radius_scores)")
