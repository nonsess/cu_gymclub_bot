from fastapi import APIRouter

from src.core.deps import UserServiceDep
from src.schemas.user import UserRegister

router = APIRouter(prefix="/users")

@router.post("/register")
async def register_user(
    user: UserRegister,
    user_service: UserServiceDep
):
    return await user_service.get_or_create_user(user)