from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(db: Session, action: str, entity_type: str, entity_id: int | None, username: str | None, details: str = ""):
    entry = AuditLog(action=action, entity_type=entity_type, entity_id=entity_id, username=username, details=details)
    db.add(entry)
    db.commit()
