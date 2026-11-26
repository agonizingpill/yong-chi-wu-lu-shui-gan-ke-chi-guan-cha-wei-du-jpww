from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from .auth import Current, Db, Supervisor, Technician
from .constants import ReportState, Role
from .report_control import approve, decide_alignment, display_report, get_report, queue_report
from .report_models import FactorReport

router = APIRouter(prefix="/factors", tags=["负荷核校"])


class RequestForm(BaseModel):
    wave_id: int = Field(gt=0)


class NoteForm(BaseModel):
    note: str = Field(min_length=6, max_length=180)


class AlignmentForm(BaseModel):
    order: list[int] = Field(min_length=2, max_length=2)
    signs: list[int] = Field(min_length=2, max_length=2)
    note: str = Field(min_length=6, max_length=180)

    @model_validator(mode="after")
    def valid_alignment(self):
        if sorted(self.order) != [1, 2]:
            raise ValueError("编号认定必须给出 1、2 两个固定编号的完整对应。")
        if any(sign not in (-1, 1) for sign in self.signs):
            raise ValueError("每个因子的方向只能是正向 1 或反向 -1。")
        return self


@router.get("")
def list_reports(db: Db, actor: Current):
    query = select(FactorReport).order_by(FactorReport.id.desc())
    if actor.role == Role.VIEWER:
        query = query.where(FactorReport.state == ReportState.APPROVED)
    return [display_report(row) for row in db.scalars(query.limit(80))]


@router.get("/{report_id}")
def report_details(report_id: int, db: Db, actor: Current):
    row = get_report(db, report_id)
    if actor.role == Role.VIEWER and row.state != ReportState.APPROVED:
        raise HTTPException(404, "找不到已核校的报告。")
    return display_report(row)


@router.post("", status_code=202)
def request_report(form: RequestForm, db: Db, actor: Technician):
    return display_report(queue_report(db, form.wave_id, actor.username))


@router.post("/{report_id}/align")
def align_report(report_id: int, form: AlignmentForm, db: Db, actor: Supervisor):
    return display_report(decide_alignment(db, report_id, form.order, form.signs, form.note, actor.username))


@router.post("/{report_id}/approve")
def approve_report(report_id: int, form: NoteForm, db: Db, actor: Supervisor):
    return display_report(approve(db, report_id, form.note, actor.username))
