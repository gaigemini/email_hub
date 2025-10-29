"""
Email service for IMAP and SMTP operations
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict, Optional
import ssl


def _decode_payload(part) -> str:
    """Safely decode email payload"""
    
    payload = part.get_payload(decode=True)
    if not payload:
        return ""

    charset = part.get_content_charset()

    if charset:
        try:
            return payload.decode(charset, errors="replace")
        except (UnicodeDecodeError, LookupError):
            pass
    
    try:
        return payload.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
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
                
                search_criteria = "UNSEEN" if unread_only else "ALL"
                status, messages = imap.search(None, search_criteria)
                
                if status != "OK":
                    return emails
                
                message_ids = messages[0].split()
                message_ids = message_ids[-limit:]
                
                for msg_id in message_ids:
                    try:
                        status, msg_data = imap.fetch(msg_id, "(RFC822)")
                        
                        if status != "OK":
                            continue
                        
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        subject = email_message.get("Subject", "")
                        sender = email_message.get("From", "")
                        recipient = email_message.get("To", "")
                        date_str = email_message.get("Date", "")
                        message_id = email_message.get("Message-ID", "")
                        
                        try:
                            date_tuple = email.utils.parsedate_tz(date_str)
                            if date_tuple:
                                timestamp = email.utils.mktime_tz(date_tuple)
                                received_at = datetime.fromtimestamp(timestamp, timezone.utc)
                            else:
                                received_at = datetime.now(timezone.utc)
                        except:
                            received_at = datetime.now(timezone.utc)
                        
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
        """Send email via SMTP, supporting both SSL and STARTTLS"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            
            if reply_to_message_id:
                msg["In-Reply-To"] = reply_to_message_id
                msg["References"] = reply_to_message_id
            
            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
            
            context = ssl.create_default_context()
            server = None
            
            # --- START FIX ---
            # Check port to decide between SSL (465) or STARTTLS (587, 25, etc.)
            if smtp_port == 465:
                # Use SMTP_SSL for implicit SSL
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
                server.login(username, password)
            else:
                # Use standard SMTP for STARTTLS
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls(context=context) # Upgrade to secure connection
                server.login(username, password)
            # --- END FIX ---

            # Send the message and quit
            server.send_message(msg)
            server.quit()
                
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")

