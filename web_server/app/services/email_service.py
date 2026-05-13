"""Email service for notifications."""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os

class EmailService:
    """Service for sending emails asynchronously."""
    
    def __init__(self):
        self.smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('MAIL_PORT', 587))
        self.smtp_username = os.environ.get('MAIL_USERNAME', '')
        self.smtp_password = os.environ.get('MAIL_PASSWORD', '')
        self.from_email = self.smtp_username
        
    async def send_email(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Send email asynchronously."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._send_email_sync, to_email, subject, body, html
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _send_email_sync(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Synchronous email sending."""
        if not self.smtp_username or not self.smtp_password:
            print("Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html:
                msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email sending error: {e}")
            return False
    
    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email to new user."""
        subject = "Welcome to Todo-App!"
        body = f"""
        Hello {username},
        
        Welcome to Todo-App! We're excited to help you stay organized and productive.
        
        Here are some tips to get started:
        1. Create your first task
        2. Set priorities and due dates
        3. Track your progress
        
        If you have any questions, feel free to reply to this email.
        
        Best regards,
        The Todo App Team
        """
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h1>Welcome to Todo-App!</h1>
                <p>Hello {username},</p>
                <p>Welcome to Todo-App! We're excited to help you stay organized and productive.</p>
                <h3>Here are some tips to get started:</h3>
                <ul>
                    <li>Create your first task</li>
                    <li>Set priorities and due dates</li>
                    <li>Track your progress</li>
                </ul>
                <p>If you have any questions, feel free to reply to this email.</p>
                <br>
                <p>Best regards,<br>The Todo App Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, html)
    
    async def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email."""
        reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        body = f"""
        Hello,
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The Todo App Team
        """
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h1>Password Reset Request</h1>
                <p>We received a request to reset your password.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Reset Password
                </a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The Todo App Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, html)
    
    async def send_task_reminder(self, to_email: str, task_title: str, due_date: str) -> bool:
        """Send task reminder email."""
        subject = f"Reminder: Task '{task_title}' is due soon"
        body = f"""
        Hello,
        
        This is a reminder that your task "{task_title}" is due on {due_date}.
        
        Don't forget to complete it on time!
        
        Best regards,
        The Todo App Team
        """
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Task Reminder</h2>
                <p>This is a reminder that your task <strong>"{task_title}"</strong> is due on <strong>{due_date}</strong>.</p>
                <p>Don't forget to complete it on time!</p>
                <br>
                <p>Best regards,<br>The Todo App Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, html)