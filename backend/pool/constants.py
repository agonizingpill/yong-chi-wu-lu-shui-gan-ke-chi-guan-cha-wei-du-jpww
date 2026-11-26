from enum import StrEnum

MIN_COHORT = 8
MIN_TOTAL = 24
SCALE_TOP = 5


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
