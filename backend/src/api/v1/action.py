from fastapi import APIRouter
from src.core.deps import CurrentUserDep, ActionServiceDep
from src.schemas.action import ActionCreate, ActionResponse

router = APIRouter(prefix="/actions", tags=["Actions"])

@router.post("/", response_model=ActionResponse)
async def send_action(
    action: ActionCreate,
    action_service: ActionServiceDep,
    current_user: CurrentUserDep,
):
    return await action_service.send_action(
        from_user_id=current_user.id,
        to_user_id=action.to_user_id,
        action_type=action.action_type,
        report_reason=action.report_reason
    )
