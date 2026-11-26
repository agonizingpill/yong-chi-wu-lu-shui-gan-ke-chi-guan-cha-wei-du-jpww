from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from .auth import Current, Db
from .cohort_models import Cohort, Wave
from .constants import MIN_COHORT, Role
from .survey_models import Survey

router = APIRouter(prefix="/waves", tags=["批次与匿名门槛"])


def load_wave(db, key, *, lock=False):
    query = select(Wave).where(Wave.id == key)
    wave = db.scalar(query.with_for_update() if lock else query)
    if wave is None:
        raise HTTPException(404, "找不到观察批次。")
    return wave


def count_cohorts(db, wave_id):
    tally = select(Survey.cohort_id, func.count(Survey.id)).where(Survey.wave_id == wave_id)
    counts = dict(db.execute(tally.group_by(Survey.cohort_id)).all())
    cohort_rows = db.scalars(select(Cohort).where(Cohort.wave_id == wave_id).order_by(Cohort.code))
    return [(cohort, counts.get(cohort.id, 0)) for cohort in cohort_rows]


@router.get("")
def waves(db: Db, actor: Current):
    rows = db.scalars(select(Wave).order_by(Wave.id.desc())).all()
    return [{"id": wave.id, "code": wave.code, "title": wave.title, "form_id": wave.form_id,
             "state": wave.state, "next_wave_id": wave.next_wave_id,
             "cohorts": [{"id": item.id, "code": item.code, "label": item.label, "planned": item.planned,
                          "collected": size if size >= MIN_COHORT or actor.role != Role.VIEWER else None,
                          "eligible": size >= MIN_COHORT} for item, size in count_cohorts(db, wave.id)]}
            for wave in rows]
