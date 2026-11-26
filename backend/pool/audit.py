from contextvars import ContextVar

from sqlalchemy.orm import Session

from .identity_models import AuditEvent

request_id: ContextVar[str] = ContextVar("request_id", default="worker")


def record(db: Session, actor: str, action: str, subject: str):
    db.add(AuditEvent(
        actor=actor, action=action, subject=subject, request_id=request_id.get(),
    ))
