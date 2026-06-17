import os
from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session

PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PIPELINE_DIR.parent
DB_FOLDER = BACKEND_DIR / "database"
DB_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FOLDER}/trend_intel.db")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
