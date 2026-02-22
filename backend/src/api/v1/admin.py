from fastapi import APIRouter

router = APIRouter(prefix="/admin")

@router.get("/export/profiles.csv")
async def export_profiles():
    ...

@router.post("/broadcasts")
async def start_broadcast():
    ...

@router.get("/broadcasts/{id}/cancel")
async def cancel_broadcast():
    ...
