from fastapi import APIRouter
from .v1 import (action, matches, profile, user)

router = APIRouter()

router.include_router(action.router)
router.include_router(matches.router)
router.include_router(profile.router)
router.include_router(user.router)