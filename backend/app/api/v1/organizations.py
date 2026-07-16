"""Organizations API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, UTC


router = APIRouter()


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    owner_id: Optional[str] = ""
    settings: Optional[dict] = {}


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class RepositoryAdd(BaseModel):
    repository_id: Optional[str] = None
    repository_name: str
    repository_path: str
    project_id: Optional[str] = None


class KnowledgeCreate(BaseModel):
    knowledge_type: str
    title: str
    description: Optional[str] = ""
    content: Optional[dict] = {}
    source_repository_id: Optional[str] = None
    tags: Optional[list[str]] = []


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    template_type: str
    template_data: dict
    tags: Optional[list[str]] = []


class CommentCreate(BaseModel):
    entity_type: str
    entity_id: str
    user_id: Optional[str] = ""
    content: str


class CompareRequest(BaseModel):
    repository_a_id: str
    repository_b_id: str
    comparison_type: Optional[str] = "full"


class SearchRequest(BaseModel):
    query: str
    types: Optional[list[str]] = None
    limit: Optional[int] = 20


_organizations: dict[str, dict] = {}
_repositories: dict[str, list[dict]] = {}
_knowledge: dict[str, dict] = {}
_templates: dict[str, dict] = {}
_collaborations: dict[str, dict] = {}
_comparisons: dict[str, dict] = {}


@router.post("/organizations")
async def create_organization(data: OrganizationCreate):
    org_id = str(uuid4())
    org = {
        "id": org_id,
        "name": data.name,
        "description": data.description,
        "owner_id": data.owner_id,
        "settings": data.settings,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _organizations[org_id] = org
    _repositories[org_id] = []
    return org


@router.get("/organizations")
async def list_organizations():
    return list(_organizations.values())


@router.get("/organizations/{org_id}")
async def get_organization(org_id: str):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    org = _organizations[org_id].copy()
    org["repositories"] = _repositories.get(org_id, [])
    org["stats"] = {
        "repositories": len(_repositories.get(org_id, [])),
        "knowledge": len([k for k in _knowledge.values() if k.get("organization_id") == org_id]),
        "templates": len([t for t in _templates.values() if t.get("organization_id") == org_id]),
        "collaborations": len([c for c in _collaborations.values() if c.get("organization_id") == org_id]),
    }
    return org


@router.put("/organizations/{org_id}")
async def update_organization(org_id: str, data: OrganizationUpdate):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    org = _organizations[org_id]
    if data.name is not None:
        org["name"] = data.name
    if data.description is not None:
        org["description"] = data.description
    if data.settings is not None:
        org["settings"] = data.settings
    org["updated_at"] = datetime.now(UTC).isoformat()
    return org


@router.delete("/organizations/{org_id}")
async def delete_organization(org_id: str):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    del _organizations[org_id]
    _repositories.pop(org_id, None)
    return {"status": "deleted"}


@router.post("/organizations/{org_id}/repositories")
async def add_repository(org_id: str, data: RepositoryAdd):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    repo_id = data.repository_id or str(uuid4())
    repo = {
        "id": repo_id,
        "organization_id": org_id,
        "repository_name": data.repository_name,
        "repository_path": data.repository_path,
        "project_id": data.project_id,
        "status": "active",
        "added_at": datetime.now(UTC).isoformat(),
    }
    _repositories.setdefault(org_id, []).append(repo)
    return repo


@router.get("/organizations/{org_id}/repositories")
async def list_repositories(org_id: str):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _repositories.get(org_id, [])


@router.delete("/organizations/{org_id}/repositories/{repo_id}")
async def remove_repository(org_id: str, repo_id: str):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    repos = _repositories.get(org_id, [])
    _repositories[org_id] = [r for r in repos if r["id"] != repo_id]
    return {"status": "deleted"}


@router.get("/organizations/{org_id}/stats")
async def get_organization_stats(org_id: str):
    if org_id not in _organizations:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "repositories": len(_repositories.get(org_id, [])),
        "knowledge": len([k for k in _knowledge.values() if k.get("organization_id") == org_id]),
        "templates": len([t for t in _templates.values() if t.get("organization_id") == org_id]),
        "collaborations": len([c for c in _collaborations.values() if c.get("organization_id") == org_id]),
        "comparisons": len([c for c in _comparisons.values() if c.get("organization_id") == org_id]),
    }


@router.post("/organizations/shared-learning")
async def add_knowledge(data: KnowledgeCreate):
    knowledge_id = str(uuid4())
    knowledge = {
        "id": knowledge_id,
        "organization_id": "",
        "knowledge_type": data.knowledge_type,
        "title": data.title,
        "description": data.description,
        "content": data.content,
        "source_repository_id": data.source_repository_id,
        "tags": data.tags,
        "confidence": 0.5,
        "usage_count": 0,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _knowledge[knowledge_id] = knowledge
    return knowledge


@router.get("/organizations/shared-learning")
async def list_knowledge(org_id: Optional[str] = None, knowledge_type: Optional[str] = None):
    results = list(_knowledge.values())
    if org_id:
        results = [k for k in results if k.get("organization_id") == org_id]
    if knowledge_type:
        results = [k for k in results if k.get("knowledge_type") == knowledge_type]
    return results


@router.get("/organizations/shared-learning/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    if knowledge_id not in _knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return _knowledge[knowledge_id]


@router.post("/organizations/templates")
async def create_template(data: TemplateCreate):
    template_id = str(uuid4())
    template = {
        "id": template_id,
        "organization_id": "",
        "name": data.name,
        "description": data.description,
        "template_type": data.template_type,
        "template_data": data.template_data,
        "tags": data.tags,
        "usage_count": 0,
        "is_default": False,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _templates[template_id] = template
    return template


@router.get("/organizations/templates")
async def list_templates(org_id: Optional[str] = None, template_type: Optional[str] = None):
    results = list(_templates.values())
    if org_id:
        results = [t for t in results if t.get("organization_id") == org_id]
    if template_type:
        results = [t for t in results if t.get("template_type") == template_type]
    return results


@router.get("/organizations/templates/{template_id}")
async def get_template(template_id: str):
    if template_id not in _templates:
        raise HTTPException(status_code=404, detail="Template not found")
    return _templates[template_id]


@router.post("/organizations/templates/{template_id}/use")
async def use_template(template_id: str):
    if template_id not in _templates:
        raise HTTPException(status_code=404, detail="Template not found")
    _templates[template_id]["usage_count"] += 1
    return _templates[template_id]


@router.post("/organizations/search")
async def search_organization(data: SearchRequest, org_id: Optional[str] = None):
    results = []
    query = data.query.lower()

    for k in _knowledge.values():
        if org_id and k.get("organization_id") != org_id:
            continue
        if query in k.get("title", "").lower() or query in k.get("description", "").lower():
            results.append({
                "id": k["id"],
                "type": "knowledge",
                "title": k["title"],
                "description": k.get("description", ""),
                "score": 0.9,
            })

    for t in _templates.values():
        if org_id and t.get("organization_id") != org_id:
            continue
        if query in t.get("name", "").lower() or query in t.get("description", "").lower():
            results.append({
                "id": t["id"],
                "type": "template",
                "title": t["name"],
                "description": t.get("description", ""),
                "score": 0.85,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:data.limit]


@router.post("/organizations/compare")
async def compare_repositories(data: CompareRequest, org_id: Optional[str] = None):
    comparison_id = str(uuid4())
    comparison = {
        "id": comparison_id,
        "organization_id": org_id or "",
        "repository_a_id": data.repository_a_id,
        "repository_b_id": data.repository_b_id,
        "comparison_type": data.comparison_type,
        "result": {
            "similarities": [
                {"type": "architecture", "description": "Both use similar patterns"},
                {"type": "dependencies", "description": "Shared core dependencies"},
            ],
            "differences": [
                {"type": "api", "description": "Different API structure"},
                {"type": "database", "description": "Schema variations"},
            ],
            "score": 0.75,
        },
        "created_at": datetime.now(UTC).isoformat(),
    }
    _comparisons[comparison_id] = comparison
    return comparison


@router.get("/organizations/compare")
async def list_comparisons(org_id: Optional[str] = None):
    results = list(_comparisons.values())
    if org_id:
        results = [c for c in results if c.get("organization_id") == org_id]
    return results


@router.get("/organizations/graph")
async def get_organization_graph(org_id: Optional[str] = None):
    nodes = [
        {"id": "org-1", "type": "organization", "label": "ForgeAI", "x": 400, "y": 100},
        {"id": "repo-1", "type": "repository", "label": "forge-ai-backend", "x": 200, "y": 300},
        {"id": "repo-2", "type": "repository", "label": "forge-ai-frontend", "x": 600, "y": 300},
        {"id": "repo-3", "type": "repository", "label": "forge-docs", "x": 400, "y": 500},
        {"id": "lib-1", "type": "library", "label": "forge-common", "x": 100, "y": 400},
        {"id": "lib-2", "type": "library", "label": "forge-ui-kit", "x": 700, "y": 400},
        {"id": "team-1", "type": "team", "label": "Backend Team", "x": 150, "y": 200},
        {"id": "team-2", "type": "team", "label": "Frontend Team", "x": 650, "y": 200},
    ]
    edges = [
        {"id": "e1", "source": "org-1", "target": "repo-1", "relationship": "contains"},
        {"id": "e2", "source": "org-1", "target": "repo-2", "relationship": "contains"},
        {"id": "e3", "source": "org-1", "target": "repo-3", "relationship": "contains"},
        {"id": "e4", "source": "repo-1", "target": "lib-1", "relationship": "depends_on"},
        {"id": "e5", "source": "repo-2", "target": "lib-2", "relationship": "depends_on"},
        {"id": "e6", "source": "repo-2", "target": "lib-1", "relationship": "depends_on"},
        {"id": "e7", "source": "team-1", "target": "repo-1", "relationship": "maintains"},
        {"id": "e8", "source": "team-2", "target": "repo-2", "relationship": "maintains"},
    ]
    return {"nodes": nodes, "edges": edges}


@router.post("/organizations/collaboration")
async def add_collaboration(data: CommentCreate, org_id: Optional[str] = None):
    collab_id = str(uuid4())
    collab = {
        "id": collab_id,
        "organization_id": org_id or "",
        "collaboration_type": "comment",
        "entity_type": data.entity_type,
        "entity_id": data.entity_id,
        "user_id": data.user_id,
        "content": data.content,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _collaborations[collab_id] = collab
    return collab


@router.get("/organizations/collaboration")
async def get_collaborations(entity_type: Optional[str] = None, entity_id: Optional[str] = None):
    results = list(_collaborations.values())
    if entity_type:
        results = [c for c in results if c.get("entity_type") == entity_type]
    if entity_id:
        results = [c for c in results if c.get("entity_id") == entity_id]
    results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return results


@router.get("/organizations/activity")
async def get_organization_activity(org_id: Optional[str] = None, limit: int = 20):
    activities = []
    for c in list(_collaborations.values())[:limit]:
        activities.append({
            "id": c["id"],
            "type": c["collaboration_type"],
            "entity": c["entity_type"],
            "content": c["content"],
            "user_id": c.get("user_id"),
            "timestamp": c["created_at"],
        })
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return activities[:limit]


@router.get("/organizations/recommendations")
async def get_recommendations(org_id: Optional[str] = None):
    return [
        {
            "id": "rec-1",
            "type": "reuse",
            "title": "Reuse Authentication Module",
            "description": "Repository forge-ai-backend has a well-tested JWT implementation",
            "source_repository": "forge-ai-backend",
            "confidence": 0.85,
        },
        {
            "id": "rec-2",
            "type": "standardize",
            "title": "Standardize API Response Format",
            "description": "Different response formats detected across repositories",
            "confidence": 0.78,
        },
        {
            "id": "rec-3",
            "type": "consolidate",
            "title": "Consolidate Duplicate Utilities",
            "description": "Similar utility functions found in forge-ai-backend and forge-docs",
            "confidence": 0.72,
        },
    ]
