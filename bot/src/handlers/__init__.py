from .start import router as start_router
from .profile import router as profile_router
from .swipe import router as swipe_router
from .matches import router as matches_router

__all__ = [
    "start_router",
    "profile_router",
    "swipe_router",
    "matches_router",
]