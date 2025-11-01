from typing import Annotated, Generator
from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine

from src.api.core.config import get_settings
from src.api.core import logger

app_settings = get_settings()

load_dotenv()

# Define choosing the settings
if app_settings.MODE == "testing":
    DATABASE_URL = "sqlite:///:memory:"
elif app_settings.MODE == "production":
    DATABASE_URL = app_settings.POSTGRES_URL
    if not DATABASE_URL:
        raise RuntimeError("POSTGRES_URL must be set in production mode")
elif app_settings.MODE == "dev":
    DATABASE_URL = f"sqlite:///{app_settings.SQLITE_DB_PATH}"

    # raise NotImplementedError("Development database is not ready yet")
else:
    raise ValueError(f"Unknown environment: {app_settings.MODE}")


logger.info(f"[DATABASE Intialization]: Database path set to {DATABASE_URL}")
try:
    connect_args = {}
    if app_settings.MODE == "dev" and DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(
        url=DATABASE_URL,
        echo=True,
        connect_args=connect_args,  # always a dict, never None
    )
    Base = SQLModel
except Exception as e:
    raise RuntimeError(f"Error initializing database engine {e}")


def create_db_and_tables(engine=engine):
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel session per request."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
