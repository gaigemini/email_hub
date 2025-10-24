"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ==================== Email Account Schemas ====================

class EmailAccountCreate(BaseModel):
    user_identifier: str  # User ID from main app (can be string or int)
    email_address: EmailStr
    imap_server: str
    imap_port: int = 993
    smtp_server: str
    smtp_port: int = 587
    password: str
    webhook_url: Optional[str] = None


class EmailAccountResponse(BaseModel):
    id: int
    user_identifier: str
    email_address: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    webhook_url: Optional[str]
    is_active: bool
    last_checked: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Email Message Schemas ====================

class EmailMessageResponse(BaseModel):
    id: int
    email_account_id: int
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
    original_email_id: int
    body: str
    html_body: Optional[str] = None


class EmailSendRequest(BaseModel):
    account_id: int
    to_addr: str
    subject: str
    body: str
    html_body: Optional[str] = None


# ==================== Webhook Schemas ====================

class WebhookPayload(BaseModel):
    """Payload structure for incoming webhooks"""
    id: int
    email_account_id: int
    sender: str
    recipient: str
    subject: str
    body: str
    html_body: Optional[str] = None
    received_at: datetime