"""
FastAPI Email Hub Backend - Stateless Microservice
Main application file
"""
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn
import os

from database import engine, Base, get_db, init_db
from models import EmailAccount, EmailMessage
from schemas import (
    EmailAccountCreate, EmailAccountResponse,
    EmailMessageResponse, WebhookPayload, EmailReplyRequest, EmailSendRequest
)
from auth import verify_api_key
from email_service import EmailService
from background_tasks import start_email_polling, stop_email_polling, restore_polling_sessions

# Initialize database
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Email Hub Microservice...")
    
    # Restore email polling sessions from database
    await restore_polling_sessions()
    
    # Start background email polling
    await start_email_polling()
    
    print("✅ Email Hub Microservice started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Stopping Email Hub Microservice...")
    await stop_email_polling()
    print("✅ Email Hub Microservice stopped")

app = FastAPI(
    title="Email Hub API",
    description="Stateless email hub microservice with webhook integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


# ==================== Email Account Management ====================

@app.post("/email-accounts", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def add_email_account(
    account_data: EmailAccountCreate,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Add a new email account"""
    # Verify API key
    verify_api_key(api_key)
    
    # Check if account already exists
    existing = db.query(EmailAccount).filter(
        EmailAccount.email_address == account_data.email_address,
        EmailAccount.user_identifier == account_data.user_identifier
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email account already exists for this user")
    
    # Test connection
    email_service = EmailService()
    try:
        email_service.test_connection(
            account_data.imap_server,
            account_data.imap_port,
            account_data.email_address,
            account_data.password
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")
    
    # Create email account
    new_account = EmailAccount(
        user_identifier=account_data.user_identifier,
        email_address=account_data.email_address,
        imap_server=account_data.imap_server,
        imap_port=account_data.imap_port,
        smtp_server=account_data.smtp_server,
        smtp_port=account_data.smtp_port,
        password=account_data.password,  # In production, encrypt this!
        webhook_url=account_data.webhook_url
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account


@app.get("/email-accounts", response_model=list[EmailAccountResponse])
async def list_email_accounts(
    user_identifier: str,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """List all email accounts for a user"""
    verify_api_key(api_key)
    
    accounts = db.query(EmailAccount).filter(
        EmailAccount.user_identifier == user_identifier
    ).all()
    return accounts


@app.get("/email-accounts/{account_id}", response_model=EmailAccountResponse)
async def get_email_account(
    account_id: int,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Get specific email account"""
    verify_api_key(api_key)
    
    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    return account


@app.put("/email-accounts/{account_id}", response_model=EmailAccountResponse)
async def update_email_account(
    account_id: int,
    account_data: EmailAccountCreate,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Update email account"""
    verify_api_key(api_key)
    
    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    # Test new connection if credentials changed
    if (account.imap_server != account_data.imap_server or 
        account.email_address != account_data.email_address or
        account.password != account_data.password):
        
        email_service = EmailService()
        try:
            email_service.test_connection(
                account_data.imap_server,
                account_data.imap_port,
                account_data.email_address,
                account_data.password
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to connect: {str(e)}")
    
    # Update fields
    account.email_address = account_data.email_address
    account.imap_server = account_data.imap_server
    account.imap_port = account_data.imap_port
    account.smtp_server = account_data.smtp_server
    account.smtp_port = account_data.smtp_port
    account.password = account_data.password
    account.webhook_url = account_data.webhook_url
    
    db.commit()
    db.refresh(account)
    
    return account


@app.delete("/email-accounts/{account_id}")
async def delete_email_account(
    account_id: int,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Delete an email account"""
    verify_api_key(api_key)
    
    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    db.delete(account)
    db.commit()
    
    return {"message": "Email account deleted successfully"}


@app.post("/email-accounts/{account_id}/toggle")
async def toggle_email_account(
    account_id: int,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Enable/disable email account polling"""
    verify_api_key(api_key)
    
    account = db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    account.is_active = not account.is_active
    db.commit()
    
    status = "enabled" if account.is_active else "disabled"
    return {"message": f"Email account polling {status}"}


# ==================== Email Operations ====================

@app.get("/emails", response_model=list[EmailMessageResponse])
async def list_emails(
    user_identifier: str = None,
    account_id: int = None,
    limit: int = 50,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """List received emails"""
    verify_api_key(api_key)
    
    query = db.query(EmailMessage).join(EmailAccount)
    
    if user_identifier:
        query = query.filter(EmailAccount.user_identifier == user_identifier)
    
    if account_id:
        query = query.filter(EmailMessage.email_account_id == account_id)
    
    emails = query.order_by(EmailMessage.received_at.desc()).limit(limit).all()
    return emails


@app.get("/emails/{email_id}", response_model=EmailMessageResponse)
async def get_email(
    email_id: int,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Get specific email"""
    verify_api_key(api_key)
    
    email = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return email


@app.post("/emails/reply")
async def send_reply(
    reply_data: EmailReplyRequest,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Send a reply email"""
    verify_api_key(api_key)
    
    # Get the original email
    original_email = db.query(EmailMessage).filter(
        EmailMessage.id == reply_data.original_email_id
    ).first()
    
    if not original_email:
        raise HTTPException(status_code=404, detail="Original email not found")
    
    # Get the email account
    account = original_email.email_account
    
    # Send reply
    email_service = EmailService()
    try:
        email_service.send_email(
            smtp_server=account.smtp_server,
            smtp_port=account.smtp_port,
            username=account.email_address,
            password=account.password,
            from_addr=account.email_address,
            to_addr=original_email.sender,
            subject=f"Re: {original_email.subject}",
            body=reply_data.body,
            reply_to_message_id=original_email.message_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    return {"message": "Reply sent successfully"}


@app.post("/emails/send")
async def send_email(
    email_data: EmailSendRequest,
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Send a new email"""
    verify_api_key(api_key)
    
    # Get the email account
    account = db.query(EmailAccount).filter(
        EmailAccount.id == email_data.account_id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Email account not found")
    
    # Send email
    email_service = EmailService()
    try:
        email_service.send_email(
            smtp_server=account.smtp_server,
            smtp_port=account.smtp_port,
            username=account.email_address,
            password=account.password,
            from_addr=account.email_address,
            to_addr=email_data.to_addr,
            subject=email_data.subject,
            body=email_data.body,
            html_body=email_data.html_body
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    
    return {"message": "Email sent successfully"}


# ==================== Webhook Endpoints ====================

@app.post("/webhooks/email-received")
async def webhook_email_received(
    payload: WebhookPayload,
    api_key: str = Security(api_key_header)
):
    """Webhook endpoint for external services to send emails"""
    verify_api_key(api_key)
    
    # Process webhook payload
    return {"message": "Webhook received", "email_id": payload.id}


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "email-hub"}


@app.get("/status")
async def service_status(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Get service status and statistics"""
    verify_api_key(api_key)
    
    total_accounts = db.query(EmailAccount).count()
    active_accounts = db.query(EmailAccount).filter(EmailAccount.is_active == True).count()
    total_emails = db.query(EmailMessage).count()
    
    return {
        "status": "running",
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "total_emails": total_emails
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)