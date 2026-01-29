from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.config import DATABASE_URL_SYNC

engine = create_engine(DATABASE_URL_SYNC, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
