from fastapi import APIRouter, BackgroundTasks, status
from fastapi.responses import StreamingResponse

from src.core.deps import AdminDep, AdminServiceDep

router = APIRouter(prefix="/admin")

@router.get("/export/profiles")
async def export_profiles(
    admin: AdminDep,
    admin_service: AdminServiceDep,
):
    csv_content = await admin_service.export_profiles_to_csv(
        admin
    )

    return StreamingResponse(
        iter([csv_content.encode('utf-8-sig')]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=profiles.csv",
            "Cache-Control": "no-cache",
        }
    )


@router.post(
    "/broadcasts",
    status_code=status.HTTP_204_NO_CONTENT
)
async def start_broadcast(
    admin: AdminDep,
    admin_service: AdminServiceDep,
    message_text: str,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        admin_service.run_broadcast_task,
        admin,
        admin.telegram_id,
        message_text
    )


@router.post(
    "/ban/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def ban_user(
    admin: AdminDep,
    user_id: int,
    admin_service: AdminServiceDep,
):
    await admin_service.ban_user(
        user_id, admin
    )