from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/audit-logs")
def list_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "username": l.username,
            "details": l.details,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/audit-logs/recent-summary")
def recent_activity_summary(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "icon": "add_circle" if "create" in l.action else ("delete" if "delete" in l.action else "edit"),
            "text": f"{l.username or 'system'} — {l.action.replace('_', ' ')} ({l.details or ''})",
            "time": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]