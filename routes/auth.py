from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from sqlalchemy.sql import exists
import re
import secrets
from datetime import datetime, timedelta

from models import User
from database import get_db
from auth_utils import auth_required
from mail import send_verification_email, generate_verification_code, verify_email_code

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_oauth(request: Request):
    return request.app.state.oauth

def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 7:
        return False, "Password must be at least 7 characters long"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""

# Login page
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request}
    )

# Local login
@router.post("/login/local")
async def login_local(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    if not username or not password:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Username and password are required"}
        )
    
    # Authenticate user
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.verify(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )
    
    # Check if email 2FA is enabled
    if user.email_2fa_enabled:
        # Generate and send code
        verification_code = generate_verification_code()
        user.email_verification_code = verification_code
        user.email_verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.commit()
        
        # Send verification email
        await send_verification_email(user.email, verification_code)
        
        # wait for email
        request.session["pending_user_id"] = user.id
        return templates.TemplateResponse(
            "2fa/verify_email.html", {"request": request, "username": username}
        )
    
    # for users without 2FA
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "auth_provider": "local",
    }
    
    return RedirectResponse(url="/", status_code=303)

# GitLab login
@router.get("/login/gitlab")
async def login_gitlab(request: Request, oauth = Depends(get_oauth)):
    redirect_uri = request.url_for("auth_gitlab")
    return await oauth.gitlab.authorize_redirect(request, redirect_uri)

# GitLab auth callback
@router.get("/auth/gitlab")
async def auth_gitlab(request: Request, db: Session = Depends(get_db), oauth = Depends(get_oauth)):
    try:
        token = await oauth.gitlab.authorize_access_token(request)
        user_resp = await oauth.gitlab.get("user", token=token)
        gitlab_user = user_resp.json()
        
        # Check if user exists
        provider_user_id = str(gitlab_user.get("id"))
        user = db.query(User).filter(
            User.auth_provider == "gitlab", 
            User.provider_user_id == provider_user_id
        ).first()
        
        if not user:
            # Create user if not exists
            username = gitlab_user.get("username")
            email = gitlab_user.get("email", f"{username}@gitlab.example.com")
            
            # Ensure username is unique
            base_username = username
            count = 1
            while db.query(exists().where(User.username == username)).scalar():
                username = f"{base_username}_{count}"
                count += 1
            
            # Create new user
            user = User(
                username=username,
                email=email,
                auth_provider="gitlab",
                provider_user_id=provider_user_id,
                is_admin=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Set session
        request.session["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "auth_provider": "gitlab",
        }
        
        return RedirectResponse(url="/", status_code=303)
    
    except Exception as e:
        print(f"GitLab OAuth error: {e}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Authentication failed"}
        )

# Add email verification route
@router.post("/verify-email")
async def verify_email_route(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    code = form.get("code")
    pending_user_id = request.session.get("pending_user_id")
    
    if not pending_user_id or not code:
        return RedirectResponse(url="/login", status_code=303)
    
    # Get the user
    user = db.query(User).filter(User.id == pending_user_id).first()
    if not user:
        request.session.pop("pending_user_id", None)
        return RedirectResponse(url="/login", status_code=303)
    
    # Check if code has expired
    if datetime.utcnow() > user.email_verification_code_expires:
        return templates.TemplateResponse(
            "2fa/verify_email.html", 
            {"request": request, "username": user.username, "error": "Verification code has expired"}
        )
    
    # Verify the code
    if not verify_email_code(user.email_verification_code, code):
        return templates.TemplateResponse(
            "2fa/verify_email.html", 
            {"request": request, "username": user.username, "error": "Invalid verification code"}
        )
    
    # Remove code/cleanup
    user.email_verification_code = None
    user.email_verification_code_expires = None
    db.commit()
    request.session.pop("pending_user_id", None)
    
    # Set the user session
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "auth_provider": "local",
    }
    
    return RedirectResponse(url="/", status_code=303)

# Logout
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# Registration page
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html", {"request": request}
    )

# Handle registration
@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    email = form.get("email")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    
    # Validate input
    if not all([username, email, password, confirm_password]):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "All fields are required"}
        )
    
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Passwords do not match"}
        )
    
    # Validate password requirements
    is_valid, error_message = validate_password(password)
    if not is_valid:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error_message}
        )
    
    # Check if username or email already exists
    if db.query(exists().where(User.username == username)).scalar():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username/Email already taken"}
        )
    
    if db.query(exists().where(User.email == email)).scalar():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username/Email already registered"}
        )
    
    # Create new user
    password_hash = bcrypt.hash(password)
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        auth_provider="local",
        is_admin=False
    )
    
    db.add(user)
    db.commit()
    
    # Set session
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "auth_provider": "local",
    }
    
    return RedirectResponse(url="/", status_code=303)
