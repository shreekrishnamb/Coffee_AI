#!/usr/bin/env python3
"""
FastAPI application for RAG Chat API with SQLite Database
"""

import sys
import os
from pathlib import Path
import logging
import uuid
import hashlib
import secrets
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv
import json

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import RAG system and database services
from core.rag import advanced_rag_query
from database.db_service import ProductService, CartService, OrderService, ChatService, UserService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize database services
db_path = str(project_root / "database" / "coffee_shop.db")
product_service = ProductService(db_path)
cart_service = CartService(db_path)
order_service = OrderService(db_path)
chat_service = ChatService(db_path)
user_service = UserService(db_path)

# Create FastAPI app
app = FastAPI(
    title="Coffee RAG API",
    description="API for RAG-based coffee shop assistant with SQLite database",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication utilities
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, hash_value = hashed_password.split('$')
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False

def generate_token(user_id: int) -> str:
    """Generate a simple token for demo purposes"""
    return f"token_{user_id}_{secrets.token_hex(16)}"

# Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID for continuing a conversation")
    message: str = Field(..., description="User message")

class Product(BaseModel):
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    buy_link: str = Field(..., description="Link to buy the product")
    image_url: str = Field(..., description="URL of the product image")

class ChatResponse(BaseModel):
    session_id: str = Field(..., description="Session ID for the conversation")
    response: str = Field(..., description="Assistant response")
    intent: str = Field(..., description="Detected intent")
    agent: str = Field(..., description="Agent who handled the request")
    products: List[Product] = Field(default_factory=list, description="Products mentioned in the response")
    sources_count: int = Field(..., description="Number of sources used")
    chat_history: List[ChatMessage] = Field(..., description="Chat history")

class CartItemRequest(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    product_id: int
    quantity: int
    selected_size: Optional[str] = None
    customizations: Optional[Dict[str, Any]] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class OrderRequest(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    total_amount: float
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    final_amount: float
    payment_method: Optional[str] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Coffee RAG API with SQLite Database"}

@app.get("/api/v1/")
async def api_root():
    """API root endpoint"""
    return {"message": "Coffee RAG API v1", "endpoints": ["/chat", "/products", "/cart", "/orders"]}

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that uses the RAG system to generate responses
    
    - Maintains chat history across requests using session_id
    - Generates responses using the advanced RAG system
    - Returns structured data including product recommendations
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create or get chat session in database
        chat_service.create_chat_session(session_id)
        
        # Retrieve chat history from database
        db_messages = chat_service.get_chat_history(session_id)
        
        # Convert to format expected by RAG system
        rag_chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in db_messages
        ]
        
        # Add user message to database
        chat_service.add_chat_message(session_id, "user", request.message)
        
        # Call RAG system with chat history
        logger.info(f"Processing query: '{request.message[:50]}...' for session {session_id}")
        result = advanced_rag_query(
            query=request.message,
            chat_history=rag_chat_history,
            llm_provider="gemini"  # Using Gemini as default
        )
        
        # Add assistant response to database
        chat_service.add_chat_message(
            session_id, 
            "assistant", 
            result["response"],
            result.get("intent"),
            result.get("agent")
        )
        
        # Update session timestamp
        chat_service.update_session_timestamp(session_id)
        
        # Convert database messages to response format
        chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in db_messages
        ]
        
        # Add current messages
        chat_history.append(ChatMessage(role="user", content=request.message))
        chat_history.append(ChatMessage(role="assistant", content=result["response"]))
        
        # Return structured response
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            intent=result.get("intent", "unknown"),
            agent=result.get("agent", "Assistant"),
            products=result.get("products", []),
            sources_count=len(result.get("sources", [])),
            chat_history=chat_history
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/api/chatbot")
async def chatbot_endpoint(request: ChatRequest):
    """
    Legacy chatbot endpoint for frontend compatibility
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create or get chat session in database
        chat_service.create_chat_session(session_id)
        
        # Retrieve chat history from database
        db_messages = chat_service.get_chat_history(session_id)
        
        # Convert to format expected by RAG system
        rag_chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in db_messages
        ]
        
        # Add user message to database
        chat_service.add_chat_message(session_id, "user", request.message)
        
        # Call RAG system
        result = advanced_rag_query(
            query=request.message,
            chat_history=rag_chat_history,
            llm_provider="gemini"
        )
        
        # Add assistant response to database
        chat_service.add_chat_message(
            session_id, 
            "assistant", 
            result["response"],
            result.get("intent"),
            result.get("agent")
        )
        
        # Update session timestamp
        chat_service.update_session_timestamp(session_id)
        
        # Return simplified response for frontend
        return {
            "reply": result["response"],
            "session_id": session_id,
            "intent": result.get("intent", "unknown")
        }
    except Exception as e:
        logger.error(f"Error processing chatbot request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Product endpoints
@app.get("/api/v1/products/")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    is_popular: Optional[bool] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    """Get products with filtering and pagination"""
    try:
        return product_service.get_products(
            skip=skip,
            limit=limit,
            category_id=category_id,
            is_popular=is_popular,
            is_active=is_active,
            search=search
        )
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving products")

@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product by ID"""
    try:
        product = product_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving product")

# Cart endpoints
@app.post("/api/v1/cart/")
async def add_to_cart(request: CartItemRequest):
    """Add item to cart"""
    try:
        return cart_service.add_to_cart(
            session_id=request.session_id,
            product_id=request.product_id,
            quantity=request.quantity,
            user_id=request.user_id,
            selected_size=request.selected_size,
            customizations=request.customizations
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail="Error adding item to cart")

@app.get("/api/v1/cart/")
async def get_cart(
    session_id: str = Query(...),
    user_id: Optional[int] = None
):
    """Get cart items"""
    try:
        return cart_service.get_cart(session_id, user_id)
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving cart")

@app.put("/api/v1/cart/{cart_item_id}")
async def update_cart_item(cart_item_id: int, quantity: int):
    """Update cart item quantity"""
    try:
        success = cart_service.update_cart_item_quantity(cart_item_id, quantity)
        if not success:
            raise HTTPException(status_code=404, detail="Cart item not found")
        return {"message": "Cart item updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail="Error updating cart item")

@app.delete("/api/v1/cart/{cart_item_id}")
async def remove_from_cart(cart_item_id: int):
    """Remove item from cart"""
    try:
        success = cart_service.remove_from_cart(cart_item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cart item not found")
        return {"message": "Item removed from cart"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail="Error removing item from cart")

@app.delete("/api/v1/cart/")
async def clear_cart(
    session_id: str = Query(...),
    user_id: Optional[int] = None
):
    """Clear all items from cart"""
    try:
        success = cart_service.clear_cart(session_id, user_id)
        return {"message": "Cart cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail="Error clearing cart")

# Session endpoint
@app.get("/api/v1/session-id/")
async def generate_session_id():
    """Generate a new session ID"""
    session_id = str(uuid.uuid4())
    # Create session in database
    chat_service.create_chat_session(session_id)
    return {"session_id": session_id}

# Auth endpoints
@app.post("/api/v1/login")
async def login(request: LoginRequest):
    """User login endpoint"""
    try:
        user = user_service.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = generate_token(user["id"])
        return {
            "access_token": token,
            "user_id": user["id"],
            "email": user["email"]
        }
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Error during login")

@app.post("/api/v1/register")
async def register(request: RegisterRequest):
    """User registration endpoint"""
    try:
        if user_service.get_user_by_email(request.email):
            raise HTTPException(status_code=409, detail="Email already registered")
        
        user_data = {
            "name": request.name,
            "email": request.email,
            "password_hash": hash_password(request.password),
            "is_active": True
        }
        user = user_service.create_user(user_data)
        token = generate_token(user["id"])
        return {
            "access_token": token,
            "user_id": user["id"],
            "email": user["email"]
        }
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Error during registration")

# Order endpoints
@app.post("/api/v1/orders/")
async def create_order(request: OrderRequest):
    """Create a new order"""
    try:
        # Get cart items for the session
        cart_data = cart_service.get_cart(request.session_id, request.user_id)
        
        # Prepare order data
        order_data = {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "status": "pending",
            "total_amount": request.total_amount,
            "tax_amount": request.tax_amount,
            "discount_amount": request.discount_amount,
            "final_amount": request.final_amount,
            "payment_status": "pending",
            "payment_method": request.payment_method,
            "shipping_address": request.shipping_address,
            "billing_address": request.billing_address,
            "notes": request.notes,
            "order_items": [
                {
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total_price": item["total_price"],
                    "selected_size": item.get("selected_size"),
                    "customizations": item.get("customizations"),
                    "notes": None
                }
                for item in cart_data["items"]
            ]
        }
        
        # Create order
        order = order_service.create_order(order_data)
        
        # Clear cart after successful order
        cart_service.clear_cart(request.session_id, request.user_id)
        
        return order
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Error creating order")

@app.get("/api/v1/orders/")
async def get_orders(user_id: Optional[int] = None):
    """Get orders for a user"""
    try:
        return order_service.get_orders(user_id)
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving orders")

@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: int):
    """Get specific order by ID"""
    try:
        order = order_service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving order")

# Categories endpoint
@app.get("/api/v1/categories/")
async def get_categories():
    """Get all categories"""
    try:
        return product_service.get_categories()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving categories")

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the FastAPI server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    
    args = parser.parse_args()
    
    print(f"Starting server on {args.host}:{args.port}")
    print(f"Database: {db_path}")
    uvicorn.run("main:app", host=args.host, port=args.port, reload=True)
