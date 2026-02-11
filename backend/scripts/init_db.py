from app.db.base import Base
from app.db.session import engine
from app.db.models import Patient, Diagnosis, MedicalDocument, ChatHistory
from sqlalchemy import text

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()