from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)
    prompt: Mapped[str] = mapped_column(String(120))
    domain: Mapped[str] = mapped_column(String(20))
    reversed: Mapped[bool] = mapped_column(Boolean)
    pinned: Mapped[bool] = mapped_column(Boolean)


class ObservationForm(Base):
    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edition: Mapped[str] = mapped_column(String(20), unique=True)
    title: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(16))
    source_report_id: Mapped[int | None] = mapped_column(ForeignKey("factor_reports.id"), unique=True)
    signed_by: Mapped[str] = mapped_column(String(32))
    sections: Mapped[list["FormItem"]] = relationship(lazy="selectin", order_by="FormItem.position",
                                                       cascade="all, delete-orphan")


class FormItem(Base):
    __tablename__ = "form_items"
    __table_args__ = (
        UniqueConstraint("form_id", "item_id", name="unique_observation_form_item"),
        UniqueConstraint("form_id", "position", name="unique_item_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    position: Mapped[int] = mapped_column(Integer)
    factor: Mapped[int | None] = mapped_column(Integer)


class EditionRegister(Base):
    __tablename__ = "edition_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_form_id: Mapped[int] = mapped_column(ForeignKey("forms.id"))
