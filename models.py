from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)  #for OAuth users
    is_admin = Column(Boolean, default=False)
    auth_provider = Column(String, default="local")
    provider_user_id = Column(String, nullable=True)
    
    # Email 2FA fields
    email_verification_code = Column(String, nullable=True)
    email_verification_code_expires = Column(DateTime, nullable=True)
    email_2fa_enabled = Column(Boolean, default=False)
    
    #later
    first_name = Column(String)
    last_name = Column(String)
    shipping_address = Column(Text)
    billing_address = Column(Text)
    phone = Column(String)

# Product model
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Integer)  
    stock = Column(Integer)
    image_url = Column(String, nullable=True)  
    category = Column(String, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    seller = relationship("User", backref="products")

# Order model
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, index=True)  # pending, paid, shipped, delivered
    total_amount = Column(Integer)  
    shipping_address = Column(Text)
    billing_address = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", backref="orders")
    items = relationship("OrderItem", back_populates="order")

# OrderItem model
class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_time = Column(Integer) 
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

# Review model
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # Out of 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    product = relationship("Product", backref="reviews")
    user = relationship("User", backref="reviews")

# Wishlist model
class Wishlist(Base):
    __tablename__ = "wishlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", backref="wishlist_items")
    product = relationship("Product", backref="wishlisted_by")

