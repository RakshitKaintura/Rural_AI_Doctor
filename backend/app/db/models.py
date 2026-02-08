from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False)
    symptoms = Column(Text)
    diagnosis = Column(Text)
    confidence = Column(Float)
    severity = Column(String)
    treatment_plan = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # pgvector column
    
    # Change the Python attribute name to 'doc_metadata'
    # The first argument "metadata" tells Postgres to keep the column name as is
    doc_metadata = Column("metadata", JSON) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)  # user or assistant
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())