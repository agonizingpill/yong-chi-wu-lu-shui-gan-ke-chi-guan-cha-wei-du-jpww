from fastapi import HTTPException
from sqlalchemy import select

from .audit import record
from .cohort_models import Cohort, Wave
from .cohorts import load_wave
from .constants import FormState, ReportState, WaveState
from .form_models import EditionRegister, FormItem, Item, ObservationForm
from .report_control import get_report


def available_items(db):
    return {item.id: item for item in db.scalars(select(Item))}


def describe_form(form, items):
    return {"id": form.id, "edition": form.edition, "title": form.title, "state": form.state,
            "source_report_id": form.source_report_id, "signed_by": form.signed_by,
            "items": [{"id": section.item_id, "code": items[section.item_id].code,
                       "prompt": items[section.item_id].prompt, "reversed": items[section.item_id].reversed,
                       "pinned": items[section.item_id].pinned, "position": section.position,
                       "factor": section.factor} for section in form.sections]}


def revise(db, data, actor):
    edition = db.scalar(select(EditionRegister).where(EditionRegister.id == 1).with_for_update())
    if edition is None:
        raise HTTPException(409, "观察表版次尚未建立。")
    report = get_report(db, data.report_id, lock=True)
    wave = load_wave(db, report.wave_id, lock=True)
    if report.state != ReportState.APPROVED or wave.state != WaveState.REVIEW or report.findings is None:
        raise HTTPException(409, "新表需要已核校且未使用过的因子报告。")
    if edition.current_form_id != wave.form_id:
        raise HTTPException(409, "本轮基于旧版，当前版次已更新，请重新组织观察。")
    old = db.get(ObservationForm, wave.form_id)
    items = available_items(db)
    positions = {entry.item_id: entry for entry in old.sections}
    chosen = set(data.item_ids)
    if not chosen.issubset(positions):
        raise HTTPException(409, "不得从本轮观察表以外添加未经核验的条目。")
    pinned = {entry_id for entry_id in positions if items[entry_id].pinned}
    if not chosen.issuperset(pinned):
        raise HTTPException(409, "须保留固定的开场登记条目。")
    loadings = {item["item_id"]: item for item in report.findings["items"]}
    factors = {loadings[item]["primary"] for item in chosen if loadings[item]["strong"]}
    if factors != {1, 2}:
        raise HTTPException(409, "下一轮观察表须各保留一个主要载荷达到阈值的条目。")
    new_form = ObservationForm(
        edition=data.edition, title=data.title, state=FormState.ACTIVE, source_report_id=report.id,
        signed_by=actor, sections=[FormItem(item_id=item_id, position=i, factor=loadings[item_id]["primary"])
                                   for i, item_id in enumerate(data.item_ids, 1)],
    )
    db.add(new_form)
    db.flush()
    next_wave = Wave(code=data.next_code, title=data.next_title, form_id=new_form.id, state=WaveState.COLLECTING)
    db.add(next_wave)
    db.flush()
    for old_cohort in db.scalars(select(Cohort).where(Cohort.wave_id == wave.id)):
        db.add(Cohort(wave_id=next_wave.id, code=old_cohort.code, label=old_cohort.label, planned=old_cohort.planned))
    wave.state, wave.next_wave_id = WaveState.SEALED, next_wave.id
    old.state, edition.current_form_id = FormState.ARCHIVED, new_form.id
    record(db, actor, "publish_form_revision", f"{data.edition}/{data.next_code}")
    db.commit()
    return {"form": describe_form(new_form, items), "new_wave_id": next_wave.id}
