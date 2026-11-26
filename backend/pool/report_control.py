import logging
from uuid import uuid4

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select

from .alignment import (
    aligned_findings,
    alignment_status,
    alignment_summary,
    align_findings,
    identity_alignment,
    manual_alignment,
)
from .audit import record
from .cohort_models import Wave
from .cohorts import count_cohorts, load_wave
from .constants import MIN_COHORT, MIN_TOTAL, ReportState, WaveState
from .factor_math import UnfitObservation, identify_factors
from .form_models import FormItem, Item, ObservationForm
from .report_models import FactorReport
from .settings import QUEUE_KEY, REDIS_URL
from .survey_models import Survey

logger = logging.getLogger("pool.reports")


def get_report(db, report_id, *, lock=False):
    query = select(FactorReport).where(FactorReport.id == report_id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "找不到因子核校单。")
    return row


def display_report(row):
    # findings 始终按该报告自己的认定显示；报告原始载荷保存不动，故旧报告仍是原编号、原载荷。
    return {"id": row.id, "wave_id": row.wave_id, "code": row.code, "state": row.state,
            "reviewed_by": row.reviewed_by, "review_note": row.review_note,
            "findings": aligned_findings(row.findings, row.alignment),
            "alignment": alignment_summary(row.alignment)}


def reference_for_report(db, report):
    """现行观察表的来源报告，返回 (报告行, 按固定编号显示的载荷)。"""
    wave = db.get(Wave, report.wave_id)
    form = db.get(ObservationForm, wave.form_id) if wave is not None else None
    if form is None or form.source_report_id is None:
        return None, None
    reference = get_report(db, form.source_report_id)
    return reference, aligned_findings(reference.findings, reference.alignment)


def resolve_alignment(db, report):
    """为新报告确定编号与方向：有来源报告就按共有题载荷对齐，否则以初版为基准。"""
    if report.alignment is not None:
        return report.alignment
    reference, view = reference_for_report(db, report)
    if reference is None:
        report.alignment = identity_alignment()
    else:
        report.alignment = align_findings(view, report.findings, reference_report_id=reference.id)
    return report.alignment


def queue_report(db, wave_id, actor):
    wave = load_wave(db, wave_id, lock=True)
    if wave.state != WaveState.COLLECTING:
        raise HTTPException(409, "本轮已冻结，不能重复提报。")
    counts = count_cohorts(db, wave.id)
    missing = [item.code for item, size in counts if size < MIN_COHORT]
    if missing:
        raise HTTPException(409, f"教练组 {'、'.join(missing)} 未达到 {MIN_COHORT} 份匿名门槛，禁止合并。")
    if sum(size for _, size in counts) < MIN_TOTAL:
        raise HTTPException(409, f"合并建模需要至少 {MIN_TOTAL} 份完整观察。")
    report = FactorReport(wave_id=wave.id, code="FA-" + uuid4().hex[:10].upper(),
                          state=ReportState.QUEUED, requested_by=actor)
    wave.state = WaveState.ANALYZING
    db.add(report)
    record(db, actor, "freeze_for_fit", wave.code)
    db.commit()
    try:
        Redis.from_url(REDIS_URL, socket_timeout=3, socket_connect_timeout=2).lpush(QUEUE_KEY, report.id)
    except RedisError:
        logger.warning("Database request retained: %s", report.code)
    return report


def do_pending(db):
    pending = db.scalar(select(FactorReport).where(FactorReport.state == ReportState.QUEUED)
                        .order_by(FactorReport.id).limit(1).with_for_update(skip_locked=True))
    if pending is None:
        return False
    wave = load_wave(db, pending.wave_id, lock=True)
    items = db.scalars(select(Item).join(FormItem, FormItem.item_id == Item.id)
                       .where(FormItem.form_id == wave.form_id).order_by(FormItem.position)).all()
    surveys = db.scalars(select(Survey).where(Survey.wave_id == wave.id).order_by(Survey.id)).all()
    try:
        pending.findings = identify_factors(items, surveys)
    except UnfitObservation as error:
        pending.state, pending.review_note, wave.state = ReportState.FAILED, str(error), WaveState.COLLECTING
    else:
        pending.state, wave.state = ReportState.READY, WaveState.REVIEW
        resolve_alignment(db, pending)
    record(db, "worker", "factor_" + pending.state, pending.code)
    db.commit()
    return True


def decide_alignment(db, report_id, order, signs, note, actor):
    """教研在证据不足时认定编号与正反方向；两位同时提交时以先确认的为准。"""
    report = get_report(db, report_id, lock=True)
    wave = load_wave(db, report.wave_id, lock=True)
    if report.state != ReportState.READY or wave.state != WaveState.REVIEW or report.findings is None:
        raise HTTPException(409, "只能在待核校的报告上认定编号与方向。")
    if report.alignment is None:
        resolve_alignment(db, report)
    current = report.alignment or {}
    if current.get("status") == "decided":
        decided_by = current.get("decided_by") or "系统"
        raise HTTPException(409, f"编号与方向已由 {decided_by} 认定，以先确认的为准。")
    reference, _view = reference_for_report(db, report)
    report.alignment = manual_alignment(order, signs, actor,
                                        reference_report_id=reference.id if reference else None,
                                        note=note)
    record(db, actor, "decide_factor_alignment", report.code)
    db.commit()
    return report


def approve(db, report_id, note, actor):
    report = get_report(db, report_id, lock=True)
    if report.state != ReportState.READY:
        raise HTTPException(409, "须先完成待核校的结果。")
    if actor == report.requested_by:
        raise HTTPException(409, "请交由不同岗位核校。")
    if report.alignment is None:
        resolve_alignment(db, report)
    if alignment_status(report) != "decided":
        raise HTTPException(409, "共有题证据不足，请先在工作台认定因子编号与方向，再核校签发。")
    report.state, report.review_note, report.reviewed_by = ReportState.APPROVED, note, actor
    record(db, actor, "approve_factor_review", report.code)
    db.commit()
    return report
