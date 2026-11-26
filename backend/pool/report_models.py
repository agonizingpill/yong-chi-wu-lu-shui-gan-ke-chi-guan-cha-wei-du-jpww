from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class FactorReport(Base):
    __tablename__ = "factor_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wave_id: Mapped[int] = mapped_column(ForeignKey("waves.id"), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    state: Mapped[str] = mapped_column(String(16), index=True)
    requested_by: Mapped[str] = mapped_column(String(32))
    reviewed_by: Mapped[str | None] = mapped_column(String(32))
    review_note: Mapped[str | None] = mapped_column(String(180))
    findings: Mapped[dict | None] = mapped_column(JSON)
