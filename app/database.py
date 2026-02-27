"""데이터베이스 관리"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
#from dotenv import load_dotenv
#load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") # 실제에선 URL 변경

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
