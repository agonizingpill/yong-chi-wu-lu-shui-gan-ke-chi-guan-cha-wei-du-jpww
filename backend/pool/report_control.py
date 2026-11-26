import logging
from uuid import uuid4

from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import select

from .audit import record
from .cohorts import count_cohorts, load_wave
from .constants import MIN_COHORT, MIN_TOTAL, ReportState, WaveState
from .factor_math import UnfitObservation, identify_factors
from .form_models import FormItem, Item
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
    return {"id": row.id, "wave_id": row.wave_id, "code": row.code, "state": row.state,
            "reviewed_by": row.reviewed_by, "review_note": row.review_note, "findings": row.findings}


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
    record(db, "worker", "factor_" + pending.state, pending.code)
    db.commit()
    return True


def approve(db, report_id, note, actor):
    report = get_report(db, report_id, lock=True)
    if report.state != ReportState.READY:
        raise HTTPException(409, "须先完成待核校的结果。")
    if actor == report.requested_by:
        raise HTTPException(409, "请交由不同岗位核校。")
    report.state, report.review_note, report.reviewed_by = ReportState.APPROVED, note, actor
    record(db, actor, "approve_factor_review", report.code)
    db.commit()
    return report
