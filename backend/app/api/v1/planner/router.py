"""Planner API router."""

from fastapi import APIRouter, Request

from app.planner.exceptions import (
    PlanNotFoundException,
    PlanningException,
)
from app.planner.schemas.planner import (
    Plan,
    PlanCreateRequest,
    PlanHistoryEntry,
    PlanUpdateRequest,
)
from app.schemas.common import BaseResponse

router = APIRouter(prefix="/planner", tags=["Planner"])


@router.post("/plans", response_model=BaseResponse[Plan])
async def create_plan(
    request: PlanCreateRequest, req: Request
) -> BaseResponse[Plan]:
    """Create an execution plan from a request.

    Analyzes the objective, classifies intent, decomposes into tasks,
    and returns a structured execution plan with risks and dependencies.
    """
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.create_plan(request)
        return BaseResponse(
            data=result,
            message="Plan created successfully",
        )
    except PlanningException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Plan creation failed: {e}",
        )


@router.get("/plans", response_model=BaseResponse[list[Plan]])
async def list_plans(
    page: int = 1,
    per_page: int = 20,
    req: Request = None,
) -> BaseResponse[list[Plan]]:
    """List all plans with pagination.

    Returns a paginated list of plans sorted by creation time.
    """
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.list_plans(page=page, per_page=per_page)
        return BaseResponse(
            data=result.plans,
            message=f"Found {result.total} plans",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to list plans: {e}",
        )


@router.get("/plans/{plan_id}", response_model=BaseResponse[Plan])
async def get_plan(
    plan_id: str, req: Request
) -> BaseResponse[Plan]:
    """Get a plan by ID.

    Returns the full execution plan including all tasks, risks, and dependencies.
    """
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.get_plan(plan_id)
        return BaseResponse(
            data=result,
            message="Plan retrieved successfully",
        )
    except PlanNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to get plan: {e}",
        )


@router.put("/plans/{plan_id}", response_model=BaseResponse[Plan])
async def update_plan(
    plan_id: str,
    request: PlanUpdateRequest,
    req: Request,
) -> BaseResponse[Plan]:
    """Update an existing plan.

    Allows updating title, description, status, or metadata.
    """
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.update_plan(plan_id, request)
        return BaseResponse(
            data=result,
            message="Plan updated successfully",
        )
    except PlanNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except PlanningException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to update plan: {e}",
        )


@router.delete("/plans/{plan_id}", response_model=BaseResponse[dict])
async def delete_plan(
    plan_id: str, req: Request
) -> BaseResponse[dict]:
    """Delete a plan.

    Removes the plan from history. This action cannot be undone.
    """
    planner_service = req.app.state.planner_service

    try:
        deleted = await planner_service.delete_plan(plan_id)
        return BaseResponse(
            data={"deleted": True, "plan_id": plan_id},
            message="Plan deleted successfully",
        )
    except PlanNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to delete plan: {e}",
        )


@router.get(
    "/plans/{plan_id}/history",
    response_model=BaseResponse[list[PlanHistoryEntry]],
)
async def get_plan_history(
    plan_id: str, req: Request
) -> BaseResponse[list[PlanHistoryEntry]]:
    """Get history for a specific plan."""
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.get_plan_history(plan_id)
        return BaseResponse(
            data=result,
            message=f"Found {len(result)} history entries",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to get plan history: {e}",
        )


@router.get(
    "/history",
    response_model=BaseResponse[list[PlanHistoryEntry]],
)
async def list_all_history(req: Request) -> BaseResponse[list[PlanHistoryEntry]]:
    """List all plan history entries."""
    planner_service = req.app.state.planner_service

    try:
        result = await planner_service.get_plan_history()
        return BaseResponse(
            data=result,
            message=f"Found {len(result)} history entries",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to get history: {e}",
        )
