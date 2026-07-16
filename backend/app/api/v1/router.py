"""V1 API router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.users.router import router as users_router
from app.api.v1.projects.router import router as projects_router
from app.api.v1.ai.router import router as ai_router
from app.api.v1.repositories_standalone import router as repositories_standalone_router
from app.api.v1.memory.router import router as memory_router
from app.api.v1.planner.router import router as planner_router
from app.api.v1.agents import router as agents_router
from app.api.v1.workflows_standalone import router as workflows_router
from app.api.v1.workforce import router as workforce_router
from app.api.v1.tools import router as tools_router
from app.api.v1.software_engineer import router as software_engineer_router
from app.api.v1.approval import router as approval_router
from app.api.v1.devops import router as devops_router
from app.api.v1.learning import router as learning_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.studio import router as studio_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.developer import router as developer_router
from app.api.v1.plugins import router as plugins_router
from app.api.v1.experience import router as experience_router
from app.api.v1.validation import router as validation_router
from app.api.v1.documentation_standalone import router as documentation_router
from app.infrastructure.observability import observability_router

router = APIRouter()

# Sub-routers with their own prefix
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(projects_router)
router.include_router(ai_router)
router.include_router(repositories_standalone_router)
router.include_router(memory_router)
router.include_router(planner_router)
router.include_router(devops_router)
router.include_router(learning_router)
router.include_router(monitoring_router)
router.include_router(studio_router)
router.include_router(organizations_router)
router.include_router(developer_router)
router.include_router(plugins_router)
router.include_router(experience_router)
router.include_router(validation_router)

# Sub-routers without prefix (need include_router prefix)
router.include_router(agents_router, prefix="/agents", tags=["Agents"])
router.include_router(workflows_router)
router.include_router(workforce_router, prefix="/workforce", tags=["Enterprise Workforce"])
router.include_router(tools_router, prefix="/tools", tags=["Tool Virtualization"])
router.include_router(software_engineer_router, prefix="/agents", tags=["Software Engineer"])
router.include_router(approval_router, prefix="/approval", tags=["Approval Gates"])
router.include_router(observability_router, prefix="", tags=["Observability"])
router.include_router(documentation_router)
