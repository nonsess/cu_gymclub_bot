from fastapi import APIRouter

from src.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from src.core.deps import CurrentUserDep, ProfileServiceDep, UserWithActiveProfileDep

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileResponse)
async def get_my_profile(
    profile_service: ProfileServiceDep,
    current_user: CurrentUserDep,
):
    return await profile_service.get_profile(current_user.id)

@router.post("", response_model=ProfileResponse)
async def create_profile(
    profile: ProfileCreate,
    profile_service: ProfileServiceDep,
    current_user: CurrentUserDep,
):
    return await profile_service.create_profile(
        current_user.id,
        profile
    )

@router.patch("", response_model=ProfileResponse)
async def edit_profile(
    profile: ProfileUpdate,
    profile_service: ProfileServiceDep,
    current_user: CurrentUserDep,
):
    return await profile_service.update_profile(
        current_user.id,
        profile
    )

@router.get("/next", response_model=ProfileResponse)
async def get_next_profile(
    profile_service: ProfileServiceDep,
    current_user: UserWithActiveProfileDep,
):
    return await profile_service.get_next_profile(user_id=current_user.id)