from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[Optional[int]]
    gender: Mapped[Optional[str]]
    phone: Mapped[Optional[str]]
    
    diagnoses: Mapped[List["Diagnosis"]] = relationship(
        back_populates="patient", 
        cascade="all, delete-orphan",
        passive_deletes=True 
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), 
        index=True
    )
    
    symptoms: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]]
    severity: Mapped[Optional[str]] 
    treatment_plan: Mapped[Optional[str]] = mapped_column(Text)
    
    patient: Mapped["Patient"] = relationship(back_populates="diagnoses")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
   
    embedding: Mapped[Vector] = mapped_column(Vector(768)) 
    
   
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict) 
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] 
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

class ImageAnalysis(Base):
    """
    NEW: Jan 2026 Image Analysis Table
    Stores AI-generated insights from clinical imagery (X-rays, etc.)
    """
    __tablename__ = "image_analyses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), 
        index=True
    )
    
    image_type: Mapped[str] = mapped_column(String(50)) 
    original_filename: Mapped[str] = mapped_column(String(255))
    analysis_result: Mapped[dict[str, Any]] = mapped_column(JSONB) 
    findings: Mapped[Optional[str]] = mapped_column(Text) 
    confidence: Mapped[float]
    severity: Mapped[str]
    recommendations: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )