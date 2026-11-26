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
    # 因子编号与方向认定：order/signs 把本次拟合的原始编号映射到固定编号。
    # 报告原始载荷始终保存在 findings 中，从不改写。
    alignment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
