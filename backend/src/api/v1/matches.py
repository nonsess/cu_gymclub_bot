from fastapi import APIRouter, status, HTTPException
from src.schemas.profile import ProfileResponse
from src.schemas.action import IncomingLikeResponse, DecideOnIncomingRequest, DecideOnIncomingResponse
from src.core.deps import UserWithActiveProfileDep, ActionServiceDep

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/incoming/next", response_model=IncomingLikeResponse)
async def get_next_incoming_like(
    action_service: ActionServiceDep,
    current_user: UserWithActiveProfileDep,
):
    result = await action_service.get_next_incoming_like(user_id=current_user.id)
    profile = result["profile"]
    action_id = result["action_id"]
    
    profile_data = ProfileResponse.model_validate(profile).model_dump()
    profile_data["incoming_action_id"] = action_id
    
    return profile_data


@router.post("/incoming/decide", status_code=status.HTTP_200_OK, response_model=DecideOnIncomingResponse)
async def decide_on_incoming(
    request: DecideOnIncomingRequest,
    action_service: ActionServiceDep,
    current_user: UserWithActiveProfileDep,
):
    if request.decision.value == "report" and not request.report_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report reason is required for report action"
        )
    
    result = await action_service.decide_on_incoming(
        viewer_user_id=current_user.id,
        action_id=request.action_id,
        decision_type=request.decision,
        report_reason=request.report_reason
    )
    
    return DecideOnIncomingResponse(
        success=True,
        match_id=result.get("match_id")
    )