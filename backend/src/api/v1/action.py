from fastapi import APIRouter, status
from src.core.deps import UserWithActiveProfileDep, ActionServiceDep
from src.schemas.action import ActionCreate

router = APIRouter(prefix="/actions", tags=["Actions"])

@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def send_action(
    action: ActionCreate,
    action_service: ActionServiceDep,
    current_user: UserWithActiveProfileDep,
):
    await action_service.send_action(
        from_user_id=current_user.id,
        to_user_id=action.to_user_id,
        action_type=action.action_type,
        report_reason=action.report_reason
    )
