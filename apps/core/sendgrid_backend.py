"""SendGrid email backend for Django"""
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Content
import os

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """Email backend using SendGrid API"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None) or os.getenv('SENDGRID_API_KEY')
        self.client = None
        if self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
        
    def send_messages(self, email_messages):
        """Send multiple email messages"""
        if not self.client:
            logger.error("SendGrid API key not configured")
            return 0
        
        sent_count = 0
        for message in email_messages:
            if self._send_message(message):
                sent_count += 1
        
        return sent_count
    
    def _send_message(self, message):
        """Send a single email message"""
        try:
            # Create SendGrid mail object
            mail = Mail(
                from_email=From(message.from_email),
                to_emails=[To(email) for email in message.to],
                subject=message.subject,
            )
            
            # Add content
            if hasattr(message, 'body') and message.body:
                mail.content = Content("text/plain", message.body)
            
            # Add HTML content if available
            if hasattr(message, 'alternatives') and message.alternatives:
                for alternative in message.alternatives:
                    if alternative[1] == 'text/html':
                        if mail.content:
                            # Add HTML as alternative
                            mail.content = [
                                Content("text/plain", message.body),
                                Content("text/html", alternative[0])
                            ]
                        else:
                            mail.content = Content("text/html", alternative[0])
            
            # Send email
            logger.info(f"Sending email via SendGrid to {message.to}")
            logger.info(f"Subject: {message.subject}")
            logger.info(f"From: {message.from_email}")
            
            response = self.client.send(mail)
            
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email sent successfully via SendGrid. Status: {response.status_code}")
                return True
            else:
                logger.error(f"❌ SendGrid API error. Status: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send email via SendGrid: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return False