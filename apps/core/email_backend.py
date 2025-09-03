"""Custom email backend that bypasses SSL certificate verification"""
from django.core.mail.backends.smtp import EmailBackend
import ssl


class SSLEmailBackend(EmailBackend):
    """Email backend that bypasses SSL certificate verification for self-signed certs"""
    
    def open(self):
        """Override open to set custom SSL context"""
        if self.connection:
            return False
        
        # Create connection using parent class
        connection_opened = super().open()
        
        if connection_opened and self.use_ssl:
            # Create SSL context that bypasses certificate verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Apply the SSL context to the connection
            if hasattr(self.connection, 'sock'):
                self.connection.sock = context.wrap_socket(
                    self.connection.sock,
                    server_hostname=self.host
                )
        
        return connection_opened