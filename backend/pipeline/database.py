import os
from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session

# 1. This finds your 'backend' folder and targets a clean 'database' folder inside it
PIPELINE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PIPELINE_DIR.parent
DB_FOLDER = BACKEND_DIR / "database"

# 2. This automatically creates the 'database' folder if it doesn't exist yet
DB_FOLDER.mkdir(parents=True, exist_ok=True)

# 3. Tell SQLite to save the file inside backend/database/
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FOLDER}/trend_intel.db")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    """Creates the tables in the database if they don't exist."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provides a database session for transactions."""
    with Session(engine) as session:
        yield session