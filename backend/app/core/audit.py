import uuid

from sqlalchemy.orm import Session

from ..models.report import AuditLog


def log_audit(
    db: Session,
    action: str,
    resource_type: str,
    user_id: uuid.UUID | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata,
        )
    )
    db.commit()
