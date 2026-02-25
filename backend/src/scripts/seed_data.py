import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import settings
from src.models.user import User
from src.models.profile import Profile, GenderEnum
from src.services.embedding import embedding_service
from src.repositories.profile import ProfileRepository

logger = logging.getLogger(__name__)


TEST_PROFILES: List[dict] = [
    {
        "telegram_id": "test_1",
        "username": "alex_gym",
        "first_name": "Алексей",
        "profile": {
            "description": "Качалка в ЦУ, пн-ср-пт, 15.00-17.00. Люблю базу: присед, жим, тяга. Ищу напарника для прогресса в силе.\n\n🏋️ Опыт тренировок: 3+ лет",
            "gender": GenderEnum.male.value,
            "age": 22,
            "photo_ids": [],
        }
    },
    {
        "telegram_id": "test_2",
        "username": "maria_fit",
        "first_name": "Мария",
        "profile": {
            "description": "Тренируюсь в ЦУ, утро, пн-пт. Люблю функционал, кроссфит, кардио. Ищу партнёра для взаимной мотивации.\n\n🏋️ Опыт тренировок: 1-2 года",
            "gender": GenderEnum.female.value,
            "age": 20,
            "photo_ids": [],
        }
    },
    {
        "telegram_id": "test_3",
        "username": "dmitry_power",
        "first_name": "Дмитрий",
        "profile": {
            "description": "Силовой тренинг, ЦУ, вечерние часы. Работаю на массу, люблю тяжелые веса. Ищу серьёзного напарника.\n\n🏋️ Опыт тренировок: 3+ лет",
            "gender": GenderEnum.male.value,
            "age": 25,
            "photo_ids": [],
        }
    },
    {
        "telegram_id": "test_4",
        "username": "anna_cardio",
        "first_name": "Анна",
        "profile": {
            "description": "Бег, велосипед, групповые программы в ЦУ. Утро, выходные. Ищу компанию для активного отдыха.\n\n🏋️ Опыт тренировок: 2-3 года",
            "gender": GenderEnum.female.value,
            "age": 23,
            "photo_ids": [],
        }
    },
    {
        "telegram_id": "test_5",
        "username": "ivan_beginner",
        "first_name": "Иван",
        "profile": {
            "description": "Только начал ходить в зал ЦУ. Нужен наставник или такой же новичок для поддержки. Готов учиться.\n\n🏋️ Опыт тренировок: Я новичок",
            "gender": GenderEnum.male.value,
            "age": 19,
            "photo_ids": [],
        }
    },
    {
        "telegram_id": "test_6",
        "username": "elena_yoga",
        "first_name": "Елена",
        "profile": {
            "description": "Йога, пилатес, растяжка в ЦУ. Ищу партнёра для спокойных тренировок и восстановления.\n\n🏋️ Опыт тренировок: 2-3 года",
            "gender": GenderEnum.female.value,
            "age": 27,
            "photo_ids": [],
        }
    },
]


async def seed_database(session: AsyncSession):
    logger.info("🌱 Starting test data seeding...")
    
    profile_repo = ProfileRepository(session)
    
    for test_user in TEST_PROFILES:
        existing_user = await session.execute(
            select(User).where(User.telegram_id == test_user["telegram_id"])
        )
        user = existing_user.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=test_user["telegram_id"],
                username=test_user["username"],
                first_name=test_user["first_name"]
            )
            session.add(user)
            await session.flush()
            logger.info(f"✅ Created user: {test_user['telegram_id']}")
        
        existing_profile = await profile_repo.get_by_user_id(user.id)
        
        if not existing_profile:
            profile_data = test_user["profile"]
            embedding = await embedding_service.generate_embedding(
                profile_data["description"]
            )
            user_name = test_user.get("first_name") or test_user.get("username") or "User"
            
            profile = Profile(
                user_id=user.id,
                name=user_name,
                description=profile_data["description"],
                gender=profile_data["gender"],
                age=profile_data["age"],
                photo_ids=profile_data["photo_ids"],
                embedding=embedding,
                is_active=True
            )
            session.add(profile)
            logger.info(f"✅ Created profile for: {test_user['telegram_id']}")
    
    await session.commit()
    logger.info(f"🎉 Seeding completed! Created {len(TEST_PROFILES)} test profiles.")


async def run_seed():
    engine = create_async_engine(settings.POSTGRES_DSN, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await seed_database(session)
    
    await engine.dispose()

async def seed_on_startup():
    try:
        await run_seed()
    except Exception as e:
        logger.error(f"❌ Failed to seed test data: {e}")
