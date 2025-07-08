from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import exists
from datetime import datetime
from slugify import slugify

import models
from models import Product, User, Review
from database import get_db
from auth_utils import auth_required, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/products", response_class=HTMLResponse)
async def list_products(
    request: Request, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)  #
):
    user = db.query(User).filter(User.id == user_data["id"]).first()
    if not user:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    # Get all products for admin users
    products = db.query(models.Product)
    if not user.is_admin:
        products = products.filter(models.Product.seller_id == user.id)
    products = products.all()
        
    return templates.TemplateResponse(
        "products/list.html",
        {"request": request, "products": products, "user": user}
    )

@router.get("/products/new", response_class=HTMLResponse)
async def new_product_form(
    request: Request,
    user_data: dict = Depends(auth_required)
):
    return templates.TemplateResponse(
        "products/new.html",
        {"request": request}
    )

@router.post("/products")
async def create_product(
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    form = await request.form()
    
    try:
        image_url = None
        image = form.get("image")
        if image and image.filename:
            # Validate file type
            if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Only JPG, JPEG and PNG files are allowed")
                
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{slugify(image.filename)}"
            
            # Create uploads directory if it doesn't exist
            import os
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = f"{upload_dir}/{filename}"
            with open(file_path, "wb") as f:
                content = await image.read()
                f.write(content)
                
            image_url = f"/static/uploads/{filename}"
            
        product = Product(
            name=form.get("name"),
            description=form.get("description"),
            price=int(float(form.get("price")) * 100),  
            stock=int(form.get("stock")),
            image_url=image_url,
            category=form.get("category"),
            seller_id=user_data["id"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return RedirectResponse(url="/products", status_code=303)
        
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "products/new.html",
            {"request": request, "error": str(e)}
        )

@router.get("/products/{product_id}/delete")
async def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    user = db.query(User).filter(User.id == user_data["id"]).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    if product.seller_id != user_data["id"] and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this product")
    
    try:
        db.delete(product)
        db.commit()
        return RedirectResponse(url="/products", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product/{product_id}")
async def product_details(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict | None = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 404,
                "error": "Product not found"
            }
        )

    #query reviews for the product
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        avg_rating = total_rating / len(reviews)

    return templates.TemplateResponse(
        "products/details.html",
        {
            "request": request,
            "product": product,
            "user": user_data,
            "reviews": reviews,
            "avg_rating": avg_rating
        }
    )

@router.get("/search", response_class=HTMLResponse)
async def search_products(
    request: Request,
    query: str = "",
    category: str = "",
    db: Session = Depends(get_db),
    user_data: dict | None = Depends(get_current_user)
):
    # Start with base query
    products_query = db.query(Product)
    
    # Apply search filters if provided
    # ilike() performs case-insensitive LIKE query
    # %text% matches if text appears anywhere in string
    # | operator means OR - match either condition
    if query:
        products_query = products_query.filter(
            (Product.name.ilike(f"%{query}%")) | 
            (Product.description.ilike(f"%{query}%"))
        )
    if category:
        products_query = products_query.filter(Product.category == category)
    
    # Get all products that match the search criteria
    products = products_query.all()
    
    return templates.TemplateResponse(
        "products/search.html",
        {
            "request": request,
            "products": products,
            "query": query,
            "category": category,
            "user": user_data
        }
    )

@router.post("/product/{product_id}/review")
async def submit_review(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(auth_required)
):
    form = await request.form()
    rating = int(form.get("rating"))
    comment = form.get("comment")
    
    # Validate rating 1 to 5
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Check if product exists(duh)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has already reviewed this product
    #If so replace there last review with new one
    existing_review = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == user_data["id"]
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.created_at = datetime.now()
    else:
        # Create new review
        review = Review(
            product_id=product_id,
            user_id=user_data["id"],
            rating=rating,
            comment=comment
        )
        db.add(review)
    
    db.commit()
    return RedirectResponse(url=f"/product/{product_id}", status_code=303)
