"""
Background tasks for email polling and webhook delivery with session restore
"""
import asyncio
import httpx
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import os  # Imported OS

from database import SessionLocal
from models import EmailAccount, EmailMessage
from email_service import EmailService

# Global task reference
email_polling_task: Optional[asyncio.Task] = None


async def restore_polling_sessions():
    """
    Restore email polling sessions from database on startup
    This ensures continuity when service restarts or scales
    """
    print("🔄 Restoring email polling sessions from database...")
    
    db = SessionLocal()
    try:
        # Get all active email accounts
        active_accounts = db.query(EmailAccount).filter(
            EmailAccount.is_active == True
        ).all()
        
        print(f"📧 Found {len(active_accounts)} active email accounts to monitor")
        
        for account in active_accounts:
            print(f"  ✓ Restored session: {account.email_address} (ID: {account.id})")
            
            # Check last_checked time
            if account.last_checked:
                time_since = datetime.now(timezone.utc) - account.last_checked
                print(f"    Last checked: {time_since.total_seconds():.0f} seconds ago")
            else:
                print(f"    Last checked: Never")
        
        print("✅ Email polling sessions restored successfully")
        
    except Exception as e:
        print(f"❌ Error restoring sessions: {e}")
    finally:
        db.close()


async def poll_email_account(account: EmailAccount, db: Session):
    """Poll a single email account for new emails"""
    
    # Get the global webhook URL from environment
    global_webhook_url = os.getenv("WEBHOOK_URL")
    
    # Get the webhook enabled flag (default to True if not set)
    webhook_enabled_str = os.getenv("WEBHOOK_ENABLED", "True")
    webhook_enabled = webhook_enabled_str.lower() in ("true", "1", "t")

    try:
        email_service = EmailService()
        
        # Fetch new emails
        emails = email_service.fetch_emails(
            imap_server=account.imap_server,
            imap_port=account.imap_port,
            username=account.email_address,
            password=account.password,
            unread_only=True,
            limit=20
        )
        
        new_emails_count = 0
        
        # Process each email
        for email_data in emails:
            # Check if email already exists
            existing = db.query(EmailMessage).filter(
                EmailMessage.message_id == email_data["message_id"]
            ).first()
            
            if existing:
                continue
            
            # Save to database
            new_message = EmailMessage(
                email_account_id=account.id,
                message_id=email_data["message_id"],
                sender=email_data["sender"],
                recipient=email_data["recipient"],
                subject=email_data["subject"],
                body=email_data["body"],
                html_body=email_data["html_body"],
                received_at=email_data["received_at"]
            )
            
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            new_emails_count += 1
            
            # --- THIS IS THE FIX ---
            # Check if the email is "new" (received after the account was created)
            # Both datetimes are now timezone-aware, so this comparison is safe
            is_new_email = new_message.received_at > account.created_at

            # Send to webhook if URL is set, webhooks are enabled, AND it's a new email
            if global_webhook_url and webhook_enabled and is_new_email:
                await send_to_webhook(global_webhook_url, new_message, db)
            # -----------------------
        
        # Update last checked time
        account.last_checked = datetime.now(timezone.utc)
        db.commit()
        
        if new_emails_count > 0:
            print(f"📬 Received {new_emails_count} new email(s) for {account.email_address}")
        
    except Exception as e:
        print(f"❌ Error polling account {account.email_address}: {e}")


async def send_to_webhook(webhook_url: str, message: EmailMessage, db: Session):
    """Send email to webhook URL"""
    try:
        payload = {
            "id": message.id,
            "message_id": message.message_id,
            "sender": message.sender,
            "recipient": message.recipient,
            "subject": message.subject,
            "body": message.body,
            "html_body": message.html_body,
            "received_at": message.received_at.isoformat()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                message.webhook_sent = True
                message.webhook_sent_at = datetime.now(timezone.utc)
                db.commit()
                print(f"✅ Webhook sent successfully for email ID {message.id}")
            else:
                print(f"⚠️  Webhook failed with status {response.status_code} for email ID {message.id}")
                
    except Exception as e:
        print(f"❌ Error sending to webhook: {e}")


async def email_polling_worker():
    """
    Background worker that polls all active email accounts
    Handles service restart and scaling gracefully
    """
    print("🤖 Email polling worker started")
    
    while True:
        try:
            db = SessionLocal()
            
            # Get all active email accounts from database
            # This ensures we always have the latest state even after restart
            accounts = db.query(EmailAccount).filter(
                EmailAccount.is_active == True
            ).all()
            
            # Poll each account
            for account in accounts:
                # Check if it's time to poll (every 2 minutes)
                should_poll = False
                
                if account.last_checked is None:
                    should_poll = True
                else:
                    time_since_last_check = datetime.now(timezone.utc) - account.last_checked
                    if time_since_last_check > timedelta(minutes=2):
                        should_poll = True
                
                if should_poll:
                    await poll_email_account(account, db)
            
            db.close()
            
            # Wait before next iteration (30 seconds)
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ Error in polling worker: {e}")
            await asyncio.sleep(60)  # Wait longer on error


async def start_email_polling():
    """Start the email polling background task"""
    global email_polling_task
    
    if email_polling_task is None or email_polling_task.done():
        email_polling_task = asyncio.create_task(email_polling_worker())
        print("✅ Email polling task started")


async def stop_email_polling():
    """Stop the email polling background task"""
    global email_polling_task
    
    if email_polling_task and not email_polling_task.done():
        email_polling_task.cancel()
        try:
            await email_polling_task
        except asyncio.CancelledError:
            print("✅ Email polling task stopped")
        email_polling_task = None