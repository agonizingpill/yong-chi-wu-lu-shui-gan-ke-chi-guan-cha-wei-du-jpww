"""因子编号与方向的固定认定。

拟合结果每次都会重新给因子编号，也可能整体反号。教研按固定编号比较水感课，
所以新报告要先对齐到现行观察表的来源报告：

* 共有题在两次拟合里的载荷做相关，得到“拟合编号 -> 固定编号”的置换；
* 相关系数的正负给出每个因子的正反方向；
* 共有题太少、相关过弱或两种置换分不开时，不做自动认定，交给教研在工作台认定。

认定只影响新报告怎样被阅读和用来签发新版；报告里保存的原始载荷从不改写，
旧报告因此仍按原编号、原载荷显示。初版没有来源报告，就以首次核校的报告为基准。
"""

from datetime import datetime, timezone
from itertools import permutations
from math import isclose

from .constants import (
    ALIGN_ANCHOR_LOADING,
    ALIGN_MIN_ANCHORS,
    ALIGN_MIN_CORRELATION,
    ALIGN_MIN_MARGIN,
    ALIGN_MIN_SHARED,
    MIN_PRIMARY_LOADING,
)

def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def identity_alignment(source="baseline", decided_by="system"):
    return {"status": "decided", "source": source, "order": [1, 2], "signs": [1, 1],
            "decided_by": decided_by, "decided_at": _stamp(), "reference_report_id": None,
            "evidence": {"shared_items": None, "note": "初版没有来源报告，以首次核校的载荷编号为基准。"}}


def alignment_status(report):
    """未记录认定的旧报告按原样显示；记录为 pending 的必须等教研认定。"""
    if report.alignment is None:
        return "decided"
    return report.alignment.get("status", "decided")


def aligned_findings(findings, alignment):
    """按认定重排新报告的因子编号与方向；原始 findings 不被修改。"""
    if not findings or not alignment or alignment.get("status") != "decided":
        return findings
    order, signs = alignment.get("order"), alignment.get("signs")
    if not order or not signs or sorted(order) != list(range(1, len(order) + 1)):
        return findings
    if order == list(range(1, len(order) + 1)) and all(sign == 1 for sign in signs):
        return findings
    items = []
    for entry in findings["items"]:
        raw = entry["loadings"]
        if len(raw) != len(order):
            return findings
        loadings = [0.0] * len(raw)
        for fitted, value in enumerate(raw):
            loadings[order[fitted] - 1] = round(float(value) * signs[fitted], 4)
        primary = max(range(len(loadings)), key=lambda index: abs(loadings[index])) + 1
        items.append({**entry, "loadings": loadings, "primary": primary,
                      "strong": bool(abs(loadings[primary - 1]) >= MIN_PRIMARY_LOADING),
                      "communality": round(float(sum(value * value for value in loadings)), 4)})
    return {**findings, "items": items}


def _matrix(findings):
    return {entry["item_id"]: list(entry["loadings"]) for entry in findings["items"]}


def _correlation(left, right):
    if len(left) < 2:
        return 0.0
    mean_a, mean_b = sum(left) / len(left), sum(right) / len(right)
    cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(left, right))
    var_a = sum((a - mean_a) ** 2 for a in left)
    var_b = sum((b - mean_b) ** 2 for b in right)
    if isclose(var_a, 0.0) or isclose(var_b, 0.0):
        return 0.0
    return cov / (var_a * var_b) ** 0.5


def _candidates(reference_items, candidate_items, shared, dimensions):
    correlations = [[_correlation([candidate_items[key][j] for key in shared],
                                  [reference_items[key][k] for key in shared])
                     for k in range(dimensions)] for j in range(dimensions)]
    scored = []
    for permutation in permutations(range(dimensions)):
        signs, strengths = [], []
        for fitted, canonical in enumerate(permutation):
            value = correlations[fitted][canonical]
            signs.append(1 if value >= 0 else -1)
            strengths.append(abs(value))
        anchors = [0] * dimensions
        agreement = 0
        for key in shared:
            base, cand = reference_items[key], candidate_items[key]
            canonical = max(range(dimensions), key=lambda index: abs(base[index]))
            fitted = max(range(dimensions), key=lambda index: abs(cand[index]))
            if (abs(base[canonical]) >= ALIGN_ANCHOR_LOADING
                    and permutation[fitted] == canonical
                    and abs(cand[fitted]) >= ALIGN_ANCHOR_LOADING
                    and base[canonical] * cand[fitted] * signs[fitted] > 0):
                anchors[canonical] += 1
                agreement += 1
        scored.append({"order": [canonical + 1 for canonical in permutation], "signs": signs,
                       "score": round(min(strengths), 4), "anchors": anchors,
                       "agreement": agreement,
                       "usable": all(count >= ALIGN_MIN_ANCHORS for count in anchors)})
    # 可用的置换优先，其次最低相关、再次锚点一致数。
    scored.sort(key=lambda entry: (entry["usable"], entry["score"], entry["agreement"]), reverse=True)
    return correlations, scored


def _reason(shared, correlations, scored):
    if len(shared) < ALIGN_MIN_SHARED:
        return f"两版共有题只有 {len(shared)} 条，少于 {ALIGN_MIN_SHARED} 条，无法按载荷对齐。"
    if not scored or not scored[0]["usable"]:
        return (f"没有一条共有题能在两个因子上同时达到 {ALIGN_ANCHOR_LOADING} 的载荷，"
                "无法判定编号与方向。")
    best = scored[0]
    second = scored[1] if len(scored) > 1 else None
    if best["score"] < ALIGN_MIN_CORRELATION:
        return f"最吻合的共有题载荷相关仅 {best['score']:.2f}，低于 {ALIGN_MIN_CORRELATION:.2f}，证据不足。"
    if second is not None and second["usable"] and best["score"] - second["score"] < ALIGN_MIN_MARGIN:
        return "两种编号置换的载荷吻合度相差太小，无法区分，请教研认定。"
    return "共有题载荷不足以唯一确定因子编号与方向。"


def align_findings(reference, candidate, reference_report_id=None):
    """比较来源报告（已按固定编号显示）与新拟合结果，返回认定或待认定说明。"""
    if reference is None or candidate is None:
        return identity_alignment()
    reference_items = _matrix(reference)
    candidate_items = _matrix(candidate)
    dimensions = int(candidate.get("dimensions", 2))
    if int(reference.get("dimensions", 2)) != dimensions or dimensions != 2:
        return {"status": "pending", "source": None, "order": None, "signs": None,
                "decided_by": None, "decided_at": None, "reference_report_id": reference_report_id,
                "reason": "两版因子维度不一致，请教研认定编号与方向。",
                "evidence": {"shared_items": None}}
    shared = sorted(set(reference_items) & set(candidate_items))
    correlations, scored = _candidates(reference_items, candidate_items, shared, dimensions)
    evidence = {"shared_items": len(shared),
                "correlations": [[round(value, 4) for value in row] for row in correlations],
                "candidates": scored}
    best = scored[0] if scored else None
    if len(shared) >= ALIGN_MIN_SHARED and best and best["usable"]:
        second = scored[1] if len(scored) > 1 else None
        clear = (best["score"] >= ALIGN_MIN_CORRELATION
                 and (second is None or not second["usable"]
                      or best["score"] - second["score"] >= ALIGN_MIN_MARGIN))
        if clear:
            return {"status": "decided", "source": "auto", "order": best["order"],
                    "signs": best["signs"], "decided_by": "system", "decided_at": _stamp(),
                    "reference_report_id": reference_report_id, "evidence": evidence}
    return {"status": "pending", "source": None, "order": None, "signs": None,
            "decided_by": None, "decided_at": None, "reference_report_id": reference_report_id,
            "reason": _reason(shared, correlations, scored), "evidence": evidence}


def manual_alignment(order, signs, actor, reference_report_id=None, note=""):
    return {"status": "decided", "source": "manual", "order": list(order), "signs": list(signs),
            "decided_by": actor, "decided_at": _stamp(), "reference_report_id": reference_report_id,
            "evidence": {"shared_items": None,
                         "note": note or "证据不足，由教研在工作台认定。"}}


def alignment_summary(alignment):
    if not alignment:
        return None
    return {key: alignment.get(key) for key in
            ("status", "source", "order", "signs", "decided_by", "decided_at",
             "reference_report_id", "reason", "evidence")}
