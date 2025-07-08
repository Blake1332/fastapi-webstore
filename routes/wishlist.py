from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from models import Wishlist, Product, User
from database import get_db
from auth_utils import auth_required

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/wishlist", response_class=HTMLResponse)
async def view_wishlist(
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    # Get user's wishlist items 
    wishlist_items = db.query(Wishlist, Product)\
        .join(Product, Wishlist.product_id == Product.id)\
        .filter(Wishlist.user_id == user_data["id"])\
        .all()
    
    return templates.TemplateResponse(
        "wishlist/view.html",
        {
            "request": request,
            "wishlist_items": wishlist_items,
            "user": user_data
        }
    )

@router.post("/wishlist/add/{product_id}")
async def add_to_wishlist(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if already in wishlist
    existing = db.query(Wishlist).filter(
        Wishlist.user_id == user_data["id"],
        Wishlist.product_id == product_id
    ).first()
    
    if existing:
        # If already in wishlist, just redirect 
        return RedirectResponse(url=f"/product/{product_id}", status_code=303)
    
    # Add to wishlist
    wishlist_item = Wishlist(
        user_id=user_data["id"],
        product_id=product_id
    )
    db.add(wishlist_item)
    db.commit()
    
    return RedirectResponse(url=f"/product/{product_id}", status_code=303)

@router.post("/wishlist/remove/{product_id}")
async def remove_from_wishlist(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    # Find and remove wishlist item
    wishlist_item = db.query(Wishlist).filter(
        Wishlist.user_id == user_data["id"],
        Wishlist.product_id == product_id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Product not in wishlist")
    
    db.delete(wishlist_item)
    db.commit()
    
    return RedirectResponse(url="/wishlist", status_code=303)