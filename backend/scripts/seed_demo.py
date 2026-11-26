from hashlib import sha256
import json

from sqlalchemy import func, select

from pool.auth import hash_password
from pool.cohort_models import Cohort, Wave
from pool.constants import FormState, WaveState
from pool.database import initialize, open_session
from pool.form_models import EditionRegister, FormItem, Item, ObservationForm
from pool.identity_models import Operator
from pool.report_models import FactorReport
from pool.settings import DEMO_PASSWORD
from pool.survey_models import Answer, Survey

from .class_fixtures import COHORTS, ITEMS, TEAM, observations


def seed():
    with open_session() as db:
        for username, display_name, role in TEAM:
            if db.scalar(select(Operator).where(Operator.username == username)) is None:
                db.add(Operator(username=username, display_name=display_name, role=role,
                                password_digest=hash_password(DEMO_PASSWORD)))
        items = []
        for code, prompt, domain, reversed_item, pinned in ITEMS:
            item = db.scalar(select(Item).where(Item.code == code))
            if item is None:
                item = Item(code=code, prompt=prompt, domain=domain, reversed=reversed_item, pinned=pinned)
                db.add(item)
            items.append(item)
        db.flush()
        form = db.scalar(select(ObservationForm).where(ObservationForm.edition == "LW-01"))
        if form is None:
            form = ObservationForm(edition="LW-01", title="课池观察表 · 基线 6 项", state=FormState.ACTIVE,
                                   signed_by="fang", sections=[FormItem(item_id=item.id, position=i)
                                                              for i, item in enumerate(items, 1)])
            db.add(form)
            db.flush()
        if db.get(EditionRegister, 1) is None:
            db.add(EditionRegister(id=1, current_form_id=form.id))
        wave = db.scalar(select(Wave).where(Wave.code == "POND-1124"))
        if wave is None:
            wave = Wave(code="POND-1124", title="11 月课池体验 · 模拟巡课", form_id=form.id,
                        state=WaveState.COLLECTING)
            db.add(wave)
            db.flush()
        cohorts = {}
        for code, label, planned, _ in COHORTS:
            cohort = db.scalar(select(Cohort).where(Cohort.wave_id == wave.id, Cohort.code == code))
            if cohort is None:
                cohort = Cohort(wave_id=wave.id, code=code, label=label, planned=planned)
                db.add(cohort)
            cohorts[code] = cohort
        db.flush()
        existing = set(db.scalars(select(Survey.ticket_hash).where(Survey.wave_id == wave.id)))
        for group, sample, values in observations():
            fingerprint = sha256(f"synthetic/{sample}".encode()).hexdigest()
            if fingerprint not in existing:
                db.add(Survey(wave_id=wave.id, cohort_id=cohorts[group].id, ticket_hash=fingerprint,
                              marks=[Answer(item_id=item.id, raw_value=val)
                                     for item, val in zip(items, values, strict=True)]))
        db.commit()
        tracked = (Operator, Cohort, Wave, Item, ObservationForm, Survey, Answer, FactorReport)
        return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) for model in tracked}


if __name__ == "__main__":
    initialize()
    print(json.dumps(seed(), sort_keys=True))
