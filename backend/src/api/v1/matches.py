from fastapi import APIRouter, status
from src.schemas.profile import ProfileResponse
from src.core.deps import UserWithActiveProfileDep, ActionServiceDep
from src.schemas.action import ActionCreate

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/incoming/next", response_model=ProfileResponse)
async def get_next_incoming_like(
    action_service: ActionServiceDep,
    current_user: UserWithActiveProfileDep,
):
    return await action_service.get_next_incoming_like(user_id=current_user.id)


@router.post("/incoming/{target_user_id}/decide", status_code=status.HTTP_204_NO_CONTENT)
async def decide_on_incoming(
    target_user_id: int,
    decision: ActionCreate,
    action_service: ActionServiceDep,
    current_user: UserWithActiveProfileDep,
):
    await action_service.decide_on_incoming(
        viewer_user_id=current_user.id,
        target_user_id=target_user_id,
        action_type=decision.action_type
    )