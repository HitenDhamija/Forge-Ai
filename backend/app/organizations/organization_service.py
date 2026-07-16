from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


class OrganizationService:
    def __init__(self) -> None:
        self._organizations: dict[str, dict[str, Any]] = {}
        self._repositories: dict[str, dict[str, dict[str, Any]]] = {}

    async def create_organization(
        self,
        name: str,
        description: str,
        owner_id: str,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        org_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        org = {
            "id": org_id,
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "settings": settings or {},
            "created_at": now,
            "updated_at": now,
        }
        self._organizations[org_id] = org
        self._repositories[org_id] = {}
        return org

    async def get_organization(self, org_id: str) -> dict[str, Any]:
        return self._organizations.get(org_id, {})

    async def list_organizations(self, owner_id: str | None = None) -> list[dict[str, Any]]:
        orgs = list(self._organizations.values())
        if owner_id:
            orgs = [o for o in orgs if o["owner_id"] == owner_id]
        return orgs

    async def update_organization(self, org_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        org = self._organizations.get(org_id)
        if not org:
            return {}
        org.update(updates)
        org["updated_at"] = datetime.utcnow().isoformat()
        return org

    async def delete_organization(self, org_id: str) -> None:
        self._organizations.pop(org_id, None)
        self._repositories.pop(org_id, None)

    async def add_repository(
        self,
        org_id: str,
        repository_id: str,
        name: str,
        path: str,
        project_id: str,
    ) -> dict[str, Any]:
        repo = {
            "repository_id": repository_id,
            "name": name,
            "path": path,
            "project_id": project_id,
            "added_at": datetime.utcnow().isoformat(),
        }
        self._repositories.setdefault(org_id, {})[repository_id] = repo
        return repo

    async def remove_repository(self, org_id: str, repository_id: str) -> None:
        repos = self._repositories.get(org_id, {})
        repos.pop(repository_id, None)

    async def list_repositories(self, org_id: str) -> list[dict[str, Any]]:
        return list(self._repositories.get(org_id, {}).values())

    async def get_organization_stats(self, org_id: str) -> dict[str, Any]:
        repos = self._repositories.get(org_id, {})
        return {
            "organization_id": org_id,
            "repository_count": len(repos),
            "repositories": list(repos.keys()),
        }

    async def search_organizations(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            o for o in self._organizations.values()
            if q in o["name"].lower() or q in o["description"].lower()
        ]
