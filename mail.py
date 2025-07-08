from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import secrets
from typing import Optional
import config

# Email setup
conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM_EMAIL,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

# FastMail
fastmail = FastMail(conf)

def generate_verification_code() -> str:
    """Generate a 6-digit verification code."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

async def send_verification_email(email: EmailStr, verification_code: str) -> bool:
    """Send a verification code via email."""
    try:
        message = MessageSchema(
            subject="Your Verification Code",
            recipients=[email],
            body=f"""
            <html>
                <body>
                    <h2>Your Verification Code</h2>
                    <p>Please use the following code to verify your account:</p>
                    <h1 style="color: #4CAF50; font-size: 32px; letter-spacing: 5px;">{verification_code}</h1>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
            </html>
            """,
            subtype="html"
        )
        
        await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

async def verify_email_code(stored_code: str, provided_code: str) -> bool:
    """Verify the provided code against the stored code."""
    return secrets.compare_digest(stored_code, provided_code) 