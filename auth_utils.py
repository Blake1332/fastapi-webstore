import pyotp
import qrcode
import base64
import io
from typing import Optional, Tuple, Any

from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from models import User
from database import get_db

# TOTP-based 2FA functions
def generate_totp_secret() -> str:
    """Generate a new TOTP secret key."""
    return pyotp.random_base32()


def get_totp_uri(username: str, secret: str, issuer: str = "BR95 Assignment 3/4/5") -> str:
    """Generate the TOTP URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )


def generate_qr_code(uri: str) -> str:
    """Generate a QR code for the TOTP URI and return as base64 data URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to bytes buffer
    buffer = io.BytesIO()
    img.save(buffer)
    
    # Convert to base64
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"


def verify_totp(secret: str, token: str) -> bool:
    """Verify a TOTP token against the secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)


def setup_2fa(username: str) -> Tuple[str, str, str]:
    """Set up 2FA for a user.
    
    Returns:
        Tuple containing (secret, uri, qr_code_data_url)
    """
    secret = generate_totp_secret()
    uri = get_totp_uri(username, secret)
    qr_code = generate_qr_code(uri)
    return secret, uri, qr_code


# User authentication utilities
async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[dict[str, Any]]:
    """Get the current authenticated user from session."""
    user_data = request.session.get("user")
    if not user_data:
        return None
    
    # Verify user exists in DB
    user_id = user_data.get("id")
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user_data
    
    # Clear invalid session
    request.session.pop("user", None)
    return None


async def auth_required(request: Request, current_user = Depends(get_current_user)):
    """Dependency to require authentication."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return current_user
