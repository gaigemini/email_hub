"""
Database models
"""
import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID  # Import UUID for PostgreSQL
from database import Base


class EmailAccount(Base):
    __tablename__ = "email_accounts"
    
    # --- CHANGED to UUID ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_address = Column(String, nullable=False, index=True)
    
    # IMAP settings
    imap_server = Column(String, nullable=False)
    imap_port = Column(Integer, default=993)
    
    # SMTP settings
    smtp_server = Column(String, nullable=False)
    smtp_port = Column(Integer, default=587)
    
    # --- NOTE: This now stores ENCRYPTED data ---
    password = Column(String, nullable=False)
    
    # Webhook URL to forward emails to
    webhook_url = Column(String)
    
    # Polling settings
    is_active = Column(Boolean, default=True, index=True)
    last_checked = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("EmailMessage", back_populates="email_account", cascade="all, delete-orphan")


class EmailMessage(Base):
    __tablename__ = "email_messages"
    
    # --- CHANGED to UUID ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- CHANGED to UUID Foreign Key ---
    email_account_id = Column(UUID(as_uuid=True), ForeignKey("email_accounts.id"), nullable=False, index=True)
    
    # Email details
    message_id = Column(String, unique=True, index=True)
    sender = Column(String, nullable=False, index=True)
    recipient = Column(String, nullable=False)
    subject = Column(String)
    body = Column(Text)
    html_body = Column(Text)
    
    # Metadata
    received_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_read = Column(Boolean, default=False)
    webhook_sent = Column(Boolean, default=False)
    webhook_sent_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    email_account = relationship("EmailAccount", back_populates="messages", foreign_keys=[email_account_id])
