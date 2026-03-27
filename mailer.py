# mailer.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self, sender_email: str, app_password: str):
        self.sender_email = sender_email
        self.app_password = app_password
        self.server = None

    def connect(self):
        """Connect and login to Gmail SMTP."""
        if self.server is None: 
            self.server = smtplib.SMTP("smtp.gmail.com", 587)
            self.server.starttls()
            self.server.login(self.sender_email, self.app_password)

    def send_mail(self, receiver_email: str, subject: str, body: str):
        """Send an email (connection must already be established)."""
        if self.server is None:
            raise Exception("SMTP server not connected. Call connect() first.")

        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        self.server.sendmail(
            self.sender_email,
            receiver_email,
            message.as_string()
        )

    def close(self):
        """Close the SMTP connection."""
        if self.server:
            self.server.quit()
            self.server = None
