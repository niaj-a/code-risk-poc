from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.models import Base


def _create_engine(database_url: str):
    if database_url.startswith("sqlite"):
        # in-memory sqlite needs a shared pool or each connection is a new db
        return create_engine(
