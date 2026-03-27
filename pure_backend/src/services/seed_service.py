from sqlalchemy.orm import Session

from src.models.enums import RoleName
from src.models.identity import RolePermission

DEFAULT_ROLE_PERMISSIONS: dict[RoleName, list[tuple[str, str]]] = {
    RoleName.ADMINISTRATOR: [
        ("identity", "manage"),
        ("organization", "manage"),
        ("process", "manage"),
        ("analytics", "read"),
        ("export", "manage"),
        ("governance", "manage"),
        ("audit", "read"),
        ("audit", "append"),
    ],
    RoleName.REVIEWER: [
        ("process", "review"),
        ("process", "create"),
        ("analytics", "read"),
        ("export", "request"),
    ],
    RoleName.GENERAL_USER: [
        ("process", "create"),
        ("analytics", "read"),
        ("export", "request"),
    ],
    RoleName.AUDITOR: [
        ("audit", "read"),
        ("analytics", "read"),
        ("export", "read"),
    ],
}


def seed_role_permissions(session: Session) -> None:
    existing = session.query(RolePermission).count()
    if existing > 0:
        return

    for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        for resource, action in permissions:
            session.add(
                RolePermission(
                    role_name=role_name,
                    resource=resource,
                    action=action,
                )
            )
    session.commit()
