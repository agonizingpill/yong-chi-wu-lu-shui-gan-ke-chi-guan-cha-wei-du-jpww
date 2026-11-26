from enum import StrEnum

MIN_COHORT = 8
MIN_TOTAL = 24
SCALE_TOP = 5
MIN_PRIMARY_LOADING = 0.45

# 因子编号与方向对齐：只有共有题载荷足够清楚时才自动认定，否则交给教研在工作台认定。
ALIGN_MIN_SHARED = 4
ALIGN_MIN_CORRELATION = 0.65
ALIGN_MIN_ANCHORS = 1
ALIGN_ANCHOR_LOADING = 0.45
ALIGN_MIN_MARGIN = 0.1


class Role(StrEnum):
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    VIEWER = "viewer"


class WaveState(StrEnum):
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    REVIEW = "review"
    SEALED = "sealed"


class ReportState(StrEnum):
    QUEUED = "queued"
    READY = "ready"
    FAILED = "failed"
    APPROVED = "approved"


class FormState(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
