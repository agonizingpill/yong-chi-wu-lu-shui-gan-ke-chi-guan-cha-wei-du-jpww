from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Wave(Base):
    __tablename__ = "waves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(18), unique=True)
    title: Mapped[str] = mapped_column(String(80))
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id"))
    state: Mapped[str] = mapped_column(String(16))
    next_wave_id: Mapped[int | None] = mapped_column(ForeignKey("waves.id"), unique=True)


class Cohort(Base):
    __tablename__ = "cohorts"
    __table_args__ = (
        UniqueConstraint("wave_id", "code", name="unique_observation_cohort"),
        CheckConstraint("planned BETWEEN 8 AND 200", name="observation_cohort_plan"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wave_id: Mapped[int] = mapped_column(ForeignKey("waves.id"), index=True)
    code: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(60))
    planned: Mapped[int] = mapped_column(Integer)
