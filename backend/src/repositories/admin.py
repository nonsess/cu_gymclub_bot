import io
import csv
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.profile import Profile
from src.core.logger import get_repo_logger

class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session
        self.logger = get_repo_logger()
        self.logger.debug(
            f"AdminRepository initialized with session {id(session)}",
            extra={"operation": "init"}
        )

    async def export_profiles_to_csv(
        self,
        limit: int = 1000,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> str:
        self.logger.info(
            f"Starting profiles export to CSV",
            extra={
                "operation": "export_profiles_to_csv",
                "export_params": {
                    "limit": limit,
                    "offset": offset,
                    "is_active": is_active
                }
            }
        )
        
        try:
            import time
            start_time = time.time()
            
            query = (
                select(Profile, User)
                .join(User, Profile.user_id == User.id)
                .order_by(Profile.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            if is_active is not None:
                query = query.where(Profile.is_active == is_active)
                self.logger.debug(
                    f"Applied is_active filter: {is_active}",
                    extra={
                        "operation": "export_profiles_to_csv",
                        "filter_applied": "is_active",
                        "filter_value": is_active
                    }
                )
            
            self.logger.debug(
                "Executing database query for profiles export",
                extra={
                    "operation": "export_profiles_to_csv",
                    "query": str(query)
                }
            )
            
            result = await self.__session.execute(query)
            rows = result.all()
            
            query_time = time.time() - start_time
            profiles_count = len(rows)
            
            self.logger.debug(
                f"Query executed in {query_time:.3f}s, retrieved {profiles_count} profiles",
                extra={
                    "operation": "export_profiles_to_csv",
                    "query_time_seconds": round(query_time, 3),
                    "profiles_retrieved": profiles_count,
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if profiles_count == 0:
                self.logger.warning(
                    "No profiles found for export with current parameters",
                    extra={
                        "operation": "export_profiles_to_csv",
                        "limit": limit,
                        "offset": offset,
                        "is_active": is_active
                    }
                )
                output = io.StringIO()
                writer = csv.writer(output, quoting=csv.QUOTE_ALL)
                writer.writerow([
                    'profile_id',
                    'user_id',
                    'telegram_id',
                    'username',
                    'first_name',
                    'name',
                    'gender',
                    'age',
                    'description',
                    'media_count',
                    'is_active',
                    'created_at',
                    'updated_at',
                ])
                return output.getvalue()
            
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            
            headers = [
                'profile_id',
                'user_id',
                'telegram_id',
                'username',
                'first_name',
                'name',
                'gender',
                'age',
                'description',
                'media_count',
                'is_active',
                'created_at',
                'updated_at',
            ]
            writer.writerow(headers)
            
            rows_written = 0
            for profile, user in rows:
                try:                    
                    writer.writerow([
                        profile.id,
                        profile.user_id,
                        user.telegram_id,
                        user.username or '',
                        user.first_name or '',
                        profile.name or '',
                        profile.gender.value if profile.gender else '',
                        profile.age or '',
                        profile.description or '',
                        len(profile.media) if profile.media else 0,
                        profile.is_active,
                        profile.created_at.isoformat() if profile.created_at else '',
                        profile.updated_at.isoformat() if profile.updated_at else '',
                    ])
                    rows_written += 1
                    
                    if rows_written % 100 == 0:
                        self.logger.debug(
                            f"Processed {rows_written} profiles for CSV export",
                            extra={
                                "operation": "export_profiles_to_csv",
                                "rows_processed": rows_written,
                                "total_rows": profiles_count,
                                "progress_percent": round(rows_written / profiles_count * 100, 1)
                            }
                        )
                        
                except Exception as e:
                    self.logger.error(
                        f"Error processing profile {profile.id} for CSV export",
                        extra={
                            "operation": "export_profiles_to_csv",
                            "profile_id": profile.id,
                            "user_id": profile.user_id,
                            "error_type": type(e).__name__,
                            "error": str(e)
                        },
                        exc_info=True
                    )
                    continue
            
            total_time = time.time() - start_time
            
            self.logger.info(
                f"Successfully exported {rows_written} profiles to CSV",
                extra={
                    "operation": "export_profiles_to_csv",
                    "total_rows": rows_written,
                    "limit": limit,
                    "offset": offset,
                    "is_active": is_active,
                    "total_time_seconds": round(total_time, 3),
                    "rows_per_second": round(rows_written / total_time, 1) if total_time > 0 else 0,
                    "csv_size_bytes": len(output.getvalue())
                }
            )
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(
                f"Failed to export profiles to CSV",
                extra={
                    "operation": "export_profiles_to_csv",
                    "limit": limit,
                    "offset": offset,
                    "is_active": is_active,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise