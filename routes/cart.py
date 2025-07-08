from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models import User, Product
from database import get_db
from auth_utils import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get cart from cookie if it exists
    cart_cookie = request.cookies.get("cart", "{}")
    import json
    try:
        cart_items = json.loads(cart_cookie)
    except:
        cart_items = {}

    # Get product details for cart items
    products = []
    total = 0
    
    for product_id, quantity_data in cart_items.items():
        product = db.query(Product).filter(Product.id == int(product_id)).first()
        if product:
            quantity = quantity_data.get('quantity', 1)  
            item_total = product.price * quantity
            products.append({
                "product": product,
                "quantity": quantity,
                "total": item_total
            })
            total += item_total

    return templates.TemplateResponse(
        "cart/view.html",
        {
            "request": request,
            "cart_items": products,
            "total": total,
            "user": current_user
        }
    )

@router.post("/cart/add/{product_id}")
async def add_to_cart(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    response = JSONResponse({
        "message": "Product added to cart",
        "redirect_options": {
            "cart": "/cart",
            "continue_shopping": "/"
        }
    })
    
    # Let the frontend handle cart storage in cookies
    return response

@router.post("/cart/remove/{product_id}")
async def remove_from_cart(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Return success response - cart management handled client-side
    return JSONResponse({
        "message": "Product removed from cart"
    })

