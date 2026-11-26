"""因子编号与方向认定的纯逻辑测试（不依赖数据库与 sklearn）。"""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pool.alignment import (  # noqa: E402
    aligned_findings,
    align_findings,
    identity_alignment,
    manual_alignment,
)


def findings(loads, dimensions=2):
    items = []
    for index, row in enumerate(loads, 1):
        primary = max(range(len(row)), key=lambda i: abs(row[i])) + 1
        items.append({"item_id": index, "code": f"CW-{index:02d}", "reverse": False,
                      "loadings": list(row), "primary": primary,
                      "strong": abs(row[primary - 1]) >= 0.45,
                      "communality": round(sum(value * value for value in row), 4),
                      "residual": 0.1})
    return {"dimensions": dimensions, "items": items}


REFERENCE = findings([(0.8, 0.1), (0.7, 0.05), (0.1, 0.85), (0.05, 0.9), (-0.6, 0.2), (0.2, -0.7)])


class AlignmentTests(unittest.TestCase):
    def test_swapped_columns_recover_fixed_numbering(self):
        candidate = findings([(0.1, 0.78), (0.05, 0.72), (0.84, 0.12), (0.88, 0.06),
                              (0.2, -0.58), (-0.68, 0.18)])
        alignment = align_findings(REFERENCE, candidate, 7)
        self.assertEqual(alignment["status"], "decided")
        self.assertEqual(alignment["order"], [2, 1])
        self.assertEqual(alignment["signs"], [1, 1])
        view = {entry["code"]: entry["primary"] for entry in aligned_findings(candidate, alignment)["items"]}
        self.assertEqual(view["CW-01"], 1)
        self.assertEqual(view["CW-03"], 2)

    def test_global_sign_flip_is_restored(self):
        candidate = findings([(-0.8, -0.1), (-0.7, -0.05), (-0.1, -0.85), (-0.05, -0.9),
                              (0.6, -0.2), (-0.2, 0.7)])
        alignment = align_findings(REFERENCE, candidate, 3)
        self.assertEqual(alignment["status"], "decided")
        self.assertEqual(alignment["signs"], [-1, -1])
        entry = aligned_findings(candidate, alignment)["items"][0]
        self.assertAlmostEqual(entry["loadings"][0], 0.8)
        self.assertEqual(entry["primary"], 1)

    def test_too_few_shared_items_requests_decision(self):
        candidate = findings([(0.8, 0.1), (0.7, 0.05)])
        alignment = align_findings(REFERENCE, candidate, 8)
        self.assertEqual(alignment["status"], "pending")
        self.assertIn("共有题", alignment["reason"])

    def test_ambiguous_loadings_request_decision(self):
        candidate = findings([(0.6, 0.6)] * 6)
        alignment = align_findings(REFERENCE, candidate, 9)
        self.assertEqual(alignment["status"], "pending")

    def test_dimension_mismatch_requests_decision(self):
        alignment = align_findings(REFERENCE, findings([(0.8, 0.1)], dimensions=3), 10)
        self.assertEqual(alignment["status"], "pending")

    def test_pending_alignment_leaves_findings_untouched(self):
        candidate = findings([(0.6, 0.6)] * 6)
        alignment = align_findings(REFERENCE, candidate, 11)
        self.assertEqual(aligned_findings(candidate, alignment), candidate)

    def test_manual_alignment_applies_choice_as_given(self):
        candidate = findings([(0.1, 0.78), (0.05, 0.72), (0.84, 0.12), (0.88, 0.06)])
        # order[fitted] = 固定编号；signs 按拟合因子给出。
        alignment = manual_alignment([2, 1], [-1, 1], "fang", 12)
        self.assertEqual(alignment["status"], "decided")
        view = aligned_findings(candidate, alignment)["items"][0]
        # 拟合因子一 0.1 → 固定因子二，反号 -0.1；拟合因子二 0.78 → 固定因子一，正向 0.78。
        self.assertEqual(view["loadings"], [0.78, -0.1])
        self.assertEqual(view["primary"], 1)

    def test_baseline_is_identity(self):
        alignment = identity_alignment()
        self.assertEqual((alignment["order"], alignment["signs"]), ([1, 2], [1, 1]))
        self.assertEqual(aligned_findings(REFERENCE, alignment), REFERENCE)

    def test_original_findings_are_not_mutated(self):
        candidate = findings([(0.1, 0.78), (0.05, 0.72), (0.84, 0.12), (0.88, 0.06)])
        before = [list(entry["loadings"]) for entry in candidate["items"]]
        aligned_findings(candidate, align_findings(REFERENCE, candidate, 13))
        self.assertEqual([entry["loadings"] for entry in candidate["items"]], before)


if __name__ == "__main__":
    unittest.main()
