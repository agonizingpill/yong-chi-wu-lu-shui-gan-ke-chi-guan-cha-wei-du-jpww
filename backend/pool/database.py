from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .settings import DB_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DB_URL, pool_pre_ping=True)
open_session = sessionmaker(bind=engine, expire_on_commit=False)


def session_dependency() -> Iterator[Session]:
    with open_session() as db:
        yield db


def initialize():
    from . import cohort_models, identity_models, report_models, survey_models, form_models

    Base.metadata.create_all(engine)
