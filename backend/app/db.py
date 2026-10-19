"""Lazy PostgreSQL engine; no connections or queries during module import."""
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DatabaseSettings, load_settings


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


@lru_cache
def get_engine():
    settings = load_settings(DatabaseSettings)
    return create_engine(
        settings.DATABASE_URL.get_secret_value(),
        pool_pre_ping=True, pool_recycle=1800, pool_size=5, max_overflow=5,
        connect_args={"connect_timeout": 10}, echo=False, hide_parameters=True,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with get_session_factory()() as session:
        yield session
