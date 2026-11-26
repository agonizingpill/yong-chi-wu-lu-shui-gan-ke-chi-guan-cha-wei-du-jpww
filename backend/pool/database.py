from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
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
    # 旧部署没有认定列：就地补上，不动已有报告。
    columns = {column["name"] for column in inspect(engine).get_columns("factor_reports")}
    if "alignment" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE factor_reports ADD COLUMN IF NOT EXISTS alignment JSON"))
