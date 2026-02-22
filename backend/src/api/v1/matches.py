from fastapi import APIRouter
from src.core.deps import CurrentUserDep, ActionServiceDep, MatchServiceDep
from src.schemas.action import ActionCreate, ActionResponse, IncomingLikeResponse
from src.schemas.match import MatchResponse

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("/incoming", response_model=list[IncomingLikeResponse])
async def get_incoming_likes(
    action_service: ActionServiceDep,
    current_user: CurrentUserDep,
):
    return await action_service.get_incoming_likes(current_user.id)

@router.post("/incoming/{target_user_id}/decide", response_model=ActionResponse)
async def decide_on_incoming(
    target_user_id: int,
    decision: ActionCreate,
    action_service: ActionServiceDep,
    current_user: CurrentUserDep,
):
    result = await action_service.decide_on_incoming(
        viewer_user_id=current_user.id,
        target_user_id=target_user_id,
        action_type=decision.action_type
    )
    return result

@router.get("/", response_model=list[MatchResponse])
async def get_matches(
    match_service: MatchServiceDep,
    current_user: CurrentUserDep,
):
    matches = await match_service.get_matches(current_user.id)
    return matches