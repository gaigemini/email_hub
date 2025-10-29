"""
Pydantic schemas for request/response validation
"""
import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ==================== Email Account Schemas ====================

class EmailAccountCreate(BaseModel):
    email_address: EmailStr
    imap_server: str
    imap_port: int = 993
    smtp_server: str
    smtp_port: int = 587
    password: str # We receive plaintext, then encrypt it


class EmailAccountResponse(BaseModel):
    # --- CHANGED to UUID ---
    id: uuid.UUID
    email_address: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    is_active: bool
    last_checked: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Email Message Schemas ====================

class EmailMessageResponse(BaseModel):
    # --- CHANGED to UUID ---
    id: uuid.UUID
    email_account_id: uuid.UUID
    message_id: str
    sender: str
    recipient: str
    subject: Optional[str]
    body: Optional[str]
    html_body: Optional[str]
    received_at: datetime
    is_read: bool
    webhook_sent: bool
    
    class Config:
        from_attributes = True


class EmailReplyRequest(BaseModel):
    # --- CHANGED to UUID ---
    original_email_id: uuid.UUID
    body: str
    html_body: Optional[str] = None


class EmailSendRequest(BaseModel):
    # --- CHANGED to UUID ---
    account_id: uuid.UUID
    to_addr: str
    subject: str
    body: str
    html_body: Optional[str] = None


# ==================== Webhook Schemas ====================

class WebhookPayload(BaseModel):
    """Payload structure for incoming webhooks"""
    # --- CHANGED to UUID ---
    id: uuid.UUID
    sender: str
    recipient: str
    subject: str
    body: str
    html_body: Optional[str] = None
    received_at: datetime
