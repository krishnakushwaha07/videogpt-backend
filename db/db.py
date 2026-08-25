from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from utility.env import settings

# create async engine
engine = create_async_engine(url=settings.DB_URL)

# bind engine with async session
Session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False
    )


async def get_db():
    async with Session() as local_session:
        try:
            yield local_session
        except Exception:
            await local_session.rollback()
            raise

