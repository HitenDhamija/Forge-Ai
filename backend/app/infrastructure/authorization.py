from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from functools import wraps

from fastapi import HTTPException


class Role(Enum):
    owner = "owner"
    admin = "admin"
    developer = "developer"
    reviewer = "reviewer"
    observer = "observer"


class Permission(Enum):
    read = "read"
    write = "write"
    delete = "delete"
    admin = "admin"
    manage_members = "manage_members"
    manage_workflows = "manage_workflows"
    manage_tools = "manage_tools"
    view_audit = "view_audit"


RolePermissions: dict[Role, list[Permission]] = {
    Role.owner: [
        Permission.read,
        Permission.write,
        Permission.delete,
        Permission.admin,
        Permission.manage_members,
        Permission.manage_workflows,
        Permission.manage_tools,
        Permission.view_audit,
    ],
    Role.admin: [
        Permission.read,
        Permission.write,
        Permission.delete,
        Permission.manage_members,
        Permission.manage_workflows,
        Permission.manage_tools,
        Permission.view_audit,
    ],
    Role.developer: [
        Permission.read,
        Permission.write,
        Permission.manage_workflows,
        Permission.manage_tools,
    ],
    Role.reviewer: [
        Permission.read,
        Permission.view_audit,
    ],
    Role.observer: [
        Permission.read,
    ],
}


@dataclass
class UserRole:
    user_id: str
    role: Role
    organization_id: str
    granted_at: datetime = field(default_factory=datetime.utcnow)
    granted_by: str = ""


@dataclass
class PermissionCheck:
    resource_type: str
    resource_id: str
    permission: Permission
    user_id: str


class AuthorizationService:
    def __init__(self) -> None:
        self._user_roles: dict[str, dict[str, UserRole]] = {}
        self._audit_log: list[dict[str, Any]] = []

    def assign_role(
        self,
        user_id: str,
        role: Role,
        org_id: str,
        granted_by: str,
    ) -> UserRole:
        key = f"{user_id}:{org_id}"
        user_role = UserRole(
            user_id=user_id,
            role=role,
            organization_id=org_id,
            granted_by=granted_by,
        )
        self._user_roles[key] = user_role
        self._audit_log.append(
            {
                "action": "assign_role",
                "user_id": user_id,
                "role": role.value,
                "organization_id": org_id,
                "granted_by": granted_by,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return user_role

    def remove_role(self, user_id: str, org_id: str) -> bool:
        key = f"{user_id}:{org_id}"
        if key in self._user_roles:
            removed = self._user_roles.pop(key)
            self._audit_log.append(
                {
                    "action": "remove_role",
                    "user_id": user_id,
                    "role": removed.role.value,
                    "organization_id": org_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return True
        return False

    def get_user_role(self, user_id: str, org_id: str) -> Role | None:
        key = f"{user_id}:{org_id}"
        user_role = self._user_roles.get(key)
        return user_role.role if user_role else None

    def get_user_permissions(self, user_id: str, org_id: str) -> list[Permission]:
        role = self.get_user_role(user_id, org_id)
        if role is None:
            return []
        return RolePermissions.get(role, [])

    def check_permission(
        self,
        user_id: str,
        org_id: str,
        permission: Permission,
    ) -> bool:
        permissions = self.get_user_permissions(user_id, org_id)
        return permission in permissions

    def check_resource_access(
        self,
        user_id: str,
        org_id: str,
        resource_type: str,
        resource_id: str,
        permission: Permission,
    ) -> bool:
        if not self.check_permission(user_id, org_id, permission):
            return False
        self._audit_log.append(
            {
                "action": "resource_access",
                "user_id": user_id,
                "organization_id": org_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "permission": permission.value,
                "granted": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return True

    def list_members(self, org_id: str) -> list[UserRole]:
        return [
            ur
            for ur in self._user_roles.values()
            if ur.organization_id == org_id
        ]

    def get_audit_log(self, org_id: str, limit: int = 100) -> list[dict[str, Any]]:
        org_entries = [
            entry
            for entry in self._audit_log
            if entry.get("organization_id") == org_id
        ]
        return org_entries[-limit:]


def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if hasattr(arg, "state") and hasattr(arg.state, "user_id"):
                        request = arg
                        break
            if not request:
                raise HTTPException(status_code=500, detail="No request context")
            user_id = getattr(request.state, "user_id", None)
            org_id = getattr(request.state, "organization_id", None)
            if not user_id or not org_id:
                raise HTTPException(status_code=401, detail="Unauthorized")
            if not auth_service.check_permission(user_id, org_id, permission):
                raise HTTPException(status_code=403, detail="Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


auth_service = AuthorizationService()
