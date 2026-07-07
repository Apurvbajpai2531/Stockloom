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
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "username": log.username,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/audit-logs/recent-summary")
def recent_activity_summary(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "icon": "add_circle" if "create" in log.action else ("delete" if "delete" in log.action else "edit"),
            "text": f"{log.username or 'system'} — {log.action.replace('_', ' ')} ({log.details or ''})",
            "time": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]