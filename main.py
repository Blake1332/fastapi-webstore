from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from datetime import datetime

import config
from database import engine, SessionLocal, get_db
import models
from routes import auth, user, products, cart, wishlist

# Create tables
models.Base.metadata.create_all(bind=engine)

# Setup app
app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    max_age=config.SESSION_MAX_AGE,
)

# Setup OAuth
oauth = OAuth()
oauth.register(
    name="gitlab",
    client_id=config.GITLAB_CLIENT_ID,
    client_secret=config.GITLAB_CLIENT_SECRET,
    access_token_url=f"{config.GITLAB_DOMAIN}/oauth/token",
    authorize_url=f"{config.GITLAB_DOMAIN}/oauth/authorize",
    api_base_url=f"{config.GITLAB_DOMAIN}/api/v4/",
    client_kwargs={"scope": "read_user"},
)

# Store OAuth instance in app state
app.state.oauth = oauth

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(wishlist.router)

# Initialize default admin user
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        # Check if any user exists
        user_count = db.query(models.User).count()
        if user_count == 0:
            # Create default admin user
            password_hash = bcrypt.hash("theadmin")
            admin = models.User(
                username="admin",
                email="admin@example.com",
                password_hash=password_hash,
                is_admin=True,
                auth_provider="local"
            )
            db.add(admin)
            db.commit()
            print("Created default admin user: admin/theadmin")

            # Create some initial products if none exist
            product_count = db.query(models.Product).count()
            if product_count == 0:
                try:
                    products = [
                        models.Product(
                            name="Laptop Pro",
                            description="High-performance laptop for professionals",
                            price=129900,  
                            stock=50,
                            image_url="/static/images/laptop.jpg",
                            category="Electronics",
                            seller_id=admin.id
                        ),
                        models.Product(
                            name="Wireless Headphones", 
                            description="Premium noise-cancelling headphones",
                            price=19900, 
                            stock=100,
                            image_url="/static/images/headphones.jpg",
                            category="Electronics",
                            seller_id=admin.id
                        ),
                        models.Product(
                            name="Coffee Maker",
                            description="Automatic drip coffee maker with timer", 
                            price=7999, 
                            stock=30,
                            image_url="/static/images/coffee-maker.jpg",
                            category="Home Appliances",
                            seller_id=admin.id
                        ),
                        models.Product(
                            name="Yoga Mat",
                            description="Non-slip exercise yoga mat",
                            price=2999,  
                            stock=200,
                            image_url="/static/images/yoga-mat.jpg", 
                            category="Fitness",
                            seller_id=admin.id
                        ),
                        models.Product(
                            name="Smart Watch",
                            description="Fitness tracking smartwatch with heart rate monitor(This should have no image attached to this product)",
                            price=24900,  
                            stock=75,
                            image_url="/static/images/smartwatch.jpg",
                            category="Electronics",
                            seller_id=admin.id
                        )
                    ]
                    
                    for product in products:
                        db.add(product)
                    db.commit()
                    print("Created initial product catalog")

                    # Add a review for the Yoga Mat
                    yoga_mat = db.query(models.Product).filter(models.Product.name == "Yoga Mat").first()
                    if yoga_mat:
                        review = models.Review(
                            user_id=admin.id,
                            product_id=yoga_mat.id,
                            rating=5,
                            comment="Excellent quality yoga mat! Very comfortable and durable. Perfect for my daily practice.",
                            created_at=datetime.utcnow()
                        )
                        db.add(review)
                        db.commit()
                        print("Created review for Yoga Mat from admin user")
                except Exception as e:
                    db.rollback()
                    print(f"Error creating products: {str(e)}")



    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
