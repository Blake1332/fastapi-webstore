from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models import User, Product
from database import get_db
from auth_utils import auth_required, get_current_user
from mail import send_verification_email, generate_verification_code, verify_email_code

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Home page
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "user": current_user, "products": products, "now": datetime.now()}
    )

# Dashboard (protected)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user = Depends(auth_required)):
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": current_user}
    )

# Email 2FA setup
@router.get("/dashboard/setup-2fa", response_class=HTMLResponse)
async def setup_2fa_page(request: Request, current_user = Depends(auth_required), db: Session = Depends(get_db)):
    # Get user from db using id
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if user.auth_provider != "local":
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "2FA is only available for local accounts", "status_code": 400}
        )
    
    if user.email_2fa_enabled:
        return templates.TemplateResponse(
            "2fa/already_enabled.html", {"request": request, "user": current_user}
        )
    
    # Generate and send verification code
    verification_code = generate_verification_code()
    user.email_verification_code = verification_code
    user.email_verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    # Send email
    await send_verification_email(user.email, verification_code)
    
    return templates.TemplateResponse(
        "2fa/setup_email.html", 
        {"request": request, "user": current_user}
    )

# Confirm email 2FA setup
@router.post("/dashboard/confirm-2fa")
async def confirm_2fa(request: Request, current_user = Depends(auth_required), db: Session = Depends(get_db)):
    form = await request.form()
    code = form.get("code")
    
    # Get the user
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not code:
        return templates.TemplateResponse(
            "2fa/setup_email.html", 
            {
                "request": request, 
                "user": current_user, 
                "error": "Missing verification code. Please try again."
            }
        )
    
    # Check if code has expired
    if datetime.utcnow() > user.email_verification_code_expires:
        return templates.TemplateResponse(
            "2fa/setup_email.html", 
            {
                "request": request, 
                "user": current_user, 
                "error": "Verification code has expired. Please try again."
            }
        )
    
    # Verify the code
    if not verify_email_code(user.email_verification_code, code):
        return templates.TemplateResponse(
            "2fa/setup_email.html", 
            {
                "request": request, 
                "user": current_user, 
                "error": "Invalid verification code. Please try again."
            }
        )
    
    # Enable email 2FA
    user.email_2fa_enabled = True
    user.email_verification_code = None
    user.email_verification_code_expires = None
    db.commit()
    
    return templates.TemplateResponse(
        "2fa/success.html", {"request": request, "user": current_user}
    )

# Disable 2FA page
@router.get("/dashboard/disable-2fa", response_class=HTMLResponse)
async def disable_2fa_page(request: Request, current_user = Depends(auth_required), db: Session = Depends(get_db)):
    # Get the user
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not user.email_2fa_enabled:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Generate and send verification code
    verification_code = generate_verification_code()
    user.email_verification_code = verification_code
    user.email_verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    # Send verification email
    await send_verification_email(user.email, verification_code)
    
    return templates.TemplateResponse(
        "2fa/disable.html", {"request": request, "user": current_user, "message": "Verification code sent to your email"}
    )

# Disable 2FA action
@router.post("/dashboard/disable-2fa")
async def disable_2fa(request: Request, current_user = Depends(auth_required), db: Session = Depends(get_db)):
    form = await request.form()
    code = form.get("code")
    
    # Get the user
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not user.email_2fa_enabled:
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # Check if code is expired
    if datetime.utcnow() > user.email_verification_code_expires:
        return templates.TemplateResponse(
            "2fa/disable.html", 
            {"request": request, "user": current_user, "error": "Verification code has expired. Please try again."}
        )
    
    # Verify the code
    if not verify_email_code(user.email_verification_code, code):
        return templates.TemplateResponse(
            "2fa/disable.html", 
            {"request": request, "user": current_user, "error": "Invalid verification code"}
        )
    
    # remove 2FA
    user.email_2fa_enabled = False
    user.email_verification_code = None
    user.email_verification_code_expires = None
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=303)
