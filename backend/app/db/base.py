from sqlalchemy.ext.declarative import declarative_base

# 1. Initialize the Base
Base = declarative_base()

# 2. MANUALLY IMPORT every model file here. 
# Even if you don't use them in this file, 
# importing them registers them with the Base.metadata.
from app.db.models import (
    Patient, 
    ChatHistory, 
    Diagnosis, 
    VoiceInteraction, 
    MedicalDocument
)