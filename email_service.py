"""
Email service for IMAP and SMTP operations
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone  # <-- IMPORTED timezone
from typing import List, Dict, Optional
import ssl


def _decode_payload(part) -> str:
    """Safely decode email payload"""
    
    # Get payload bytes
    payload = part.get_payload(decode=True)
    if not payload:
        return ""

    # Get charset from email part
    charset = part.get_content_charset()

    # If charset is specified, try to use it
    if charset:
        try:
            return payload.decode(charset, errors="replace")
        except (UnicodeDecodeError, LookupError):
            # Fallback if charset is wrong or unknown
            pass
    
    # If no charset or if it failed, try utf-8, then latin-1
    try:
        return payload.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        # Final fallback
        return payload.decode("latin-1", errors="replace")


class EmailService:
    """Service for handling email operations"""
    
    def test_connection(self, imap_server: str, imap_port: int, username: str, password: str) -> bool:
        """Test IMAP connection"""
        try:
            context = ssl.create_default_context()
            with imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context) as imap:
                imap.login(username, password)
                return True
        except Exception as e:
            raise Exception(f"IMAP connection failed: {str(e)}")
    
    def fetch_emails(
        self,
        imap_server: str,
        imap_port: int,
        username: str,
        password: str,
        folder: str = "INBOX",
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """Fetch emails from IMAP server"""
        emails = []
        
        try:
            context = ssl.create_default_context()
            with imaplib.IMAP4_SSL(imap_server, imap_port, ssl_context=context) as imap:
                imap.login(username, password)
                imap.select(folder)
                
                # Search for emails
                search_criteria = "UNSEEN" if unread_only else "ALL"
                status, messages = imap.search(None, search_criteria)
                
                if status != "OK":
                    return emails
                
                # Get message IDs
                message_ids = messages[0].split()
                
                # Limit the number of emails
                message_ids = message_ids[-limit:]
                
                for msg_id in message_ids:
                    try:
                        # Fetch email
                        status, msg_data = imap.fetch(msg_id, "(RFC822)")
                        
                        if status != "OK":
                            continue
                        
                        # Parse email
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        # Extract details
                        subject = email_message.get("Subject", "")
                        sender = email_message.get("From", "")
                        recipient = email_message.get("To", "")
                        date_str = email_message.get("Date", "")
                        message_id = email_message.get("Message-ID", "")
                        
                        # --- THIS IS THE FIX ---
                        # Parse date and ensure it's timezone-aware (UTC)
                        try:
                            date_tuple = email.utils.parsedate_tz(date_str)
                            if date_tuple:
                                timestamp = email.utils.mktime_tz(date_tuple)
                                # Convert timestamp to aware UTC datetime
                                received_at = datetime.fromtimestamp(timestamp, timezone.utc)
                            else:
                                # Fallback to aware UTC datetime
                                received_at = datetime.now(timezone.utc)
                        except:
                            # Fallback to aware UTC datetime
                            received_at = datetime.now(timezone.utc)
                        # -------------------------
                        
                        # Extract body
                        body = ""
                        html_body = ""
                        
                        if email_message.is_multipart():
                            for part in email_message.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                if "attachment" not in content_disposition:
                                    if content_type == "text/plain":
                                        body = _decode_payload(part)
                                    elif content_type == "text/html":
                                        html_body = _decode_payload(part)
                        else:
                            # Non-multipart email
                            body = _decode_payload(email_message)
                        
                        emails.append({
                            "message_id": message_id,
                            "sender": sender,
                            "recipient": recipient,
                            "subject": subject,
                            "body": body,
                            "html_body": html_body,
                            "received_at": received_at
                        })
                        
                    except Exception as e:
                        print(f"Error parsing email {msg_id}: {e}")
                        continue
                
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")
        
        return emails
    
    def send_email(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addr: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    ):
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            
            if reply_to_message_id:
                msg["In-Reply-To"] = reply_to_message_id
                msg["References"] = reply_to_message_id
            
            # Add body
            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.send_message(msg)
                
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")