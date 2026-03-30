from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator


@lru_cache(maxsize=1)
def get_engine():
    from config import settings

    return create_engine(settings.database_url)


def get_db() -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
