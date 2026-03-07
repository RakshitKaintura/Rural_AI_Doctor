from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.db.models import (
    Patient, 
    ChatHistory, 
    Diagnosis, 
    VoiceInteraction, 
    MedicalDocument
)