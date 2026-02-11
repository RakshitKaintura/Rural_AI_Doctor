from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600, 
    echo=settings.DEBUG,

    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)

def get_db():
    """
    FastAPI dependency that provides a database session.
    Ensures the connection is closed even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()