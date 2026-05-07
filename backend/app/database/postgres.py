from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Build async connection string from Supabase URL
# Supabase URL format: https://xxx.supabase.co
# We need the Postgres connection string; for local dev use docker postgres
DATABASE_URL = settings.supabase_url or "postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_memory"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore
    async with async_session() as session:
        yield session
