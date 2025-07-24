from sqlmodel import Session, create_engine, SQLModel
import os
from dotenv import load_dotenv
load_dotenv()
import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from sqlalchemy.orm import sessionmaker

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


#DATABASE_URL = os.getenv('DATABASE_URL')
DB_URL = os.getenv('DB_URL')
#print(DATABASE_URL)
connect_arg= {"check_same_thread": False}


DATABASE_URL = (f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = create_async_engine(DATABASE_URL)

#engine = create_engine(DB_URL, connect_args=connect_arg, echo=True, future=True)
#engine = create_engine(DB_URL, connect_args=connect_arg, echo=True, future=True)
#engine = create_async_engine(DB_URL, echo=True)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = SQLModel

"""def get_db():
    with Session(engine) as session:
        yield session
"""

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

"""async def get_db():
    async with AsyncSessionLocal() as session:
        yield session"""
