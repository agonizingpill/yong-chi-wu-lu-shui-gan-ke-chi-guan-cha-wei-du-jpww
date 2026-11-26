from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Survey(Base):
    __tablename__ = "surveys"
    __table_args__ = (
        UniqueConstraint("wave_id", "ticket_hash", name="one_anonymous_ticket_in_wave"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wave_id: Mapped[int] = mapped_column(ForeignKey("waves.id"), index=True)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), index=True)
    ticket_hash: Mapped[str] = mapped_column(String(64))
    marks: Mapped[list["Answer"]] = relationship(lazy="selectin", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        CheckConstraint("raw_value BETWEEN 1 AND 5", name="observation_answer_range"),
        UniqueConstraint("survey_id", "item_id", name="one_answer_per_form_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("surveys.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    raw_value: Mapped[int] = mapped_column(Integer)
