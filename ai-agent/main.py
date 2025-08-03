from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import core modules
from core.agent import ShaymeeAgent
from core.product_search import ProductSearchEngine
from core.conversation_manager import ConversationManager
from core.payment_processor import PaymentProcessor
from integrations.temu_client import TemuClient
from integrations.correos_client import CorreosClient
from integrations.sinpe_client import SinpeClient
from utils.database import get_db
from utils.auth import verify_token

# Initialize FastAPI app
app = FastAPI(
    title="Shaymee AI Agent",
    description="AI Agent for Shaymee store with WhatsApp, Temu, and Correos de Costa Rica integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize core services
agent = ShaymeeAgent()
product_search = ProductSearchEngine()
conversation_manager = ConversationManager()
payment_processor = PaymentProcessor()
temu_client = TemuClient()
correos_client = CorreosClient()
sinpe_client = SinpeClient()

# Pydantic models
class MessageRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ProductSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    limit: int = 10

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "CRC"
    payment_method: str = "sinpe"

class OrderRequest(BaseModel):
    user_id: str
    products: List[Dict[str, Any]]
    shipping_address: Dict[str, str]
    payment_method: str = "sinpe"

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "Shaymee AI Agent",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# AI Agent endpoints
@app.post("/agent/process-message")
async def process_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
):
    """Process user message through AI agent"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Process message with AI agent
        response = await agent.process_message(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        # Store conversation in background
        background_tasks.add_task(
            conversation_manager.store_conversation,
            user_id=request.user_id,
            message=request.message,
            response=response,
            session_id=request.session_id
        )
        
        return {
            "success": True,
            "response": response,
            "session_id": response.get("session_id")
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/search-products")
async def search_products(
    request: ProductSearchRequest,
    token: str = Depends(security)
):
    """Search products using AI-powered semantic search"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Search products
        products = await product_search.search(
            query=request.query,
            category=request.category,
            price_range=request.price_range,
            limit=request.limit
        )
        
        return {
            "success": True,
            "products": products,
            "total": len(products)
        }
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/generate-payment")
async def generate_payment(
    request: PaymentRequest,
    token: str = Depends(security)
):
    """Generate payment link using SINPE"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Generate payment link
        payment_link = await payment_processor.generate_payment_link(
            order_id=request.order_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method
        )
        
        return {
            "success": True,
            "payment_link": payment_link,
            "order_id": request.order_id
        }
    except Exception as e:
        logger.error(f"Error generating payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/create-order")
async def create_order(
    request: OrderRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
):
    """Create order and initiate purchase process"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Create order
        order = await agent.create_order(
            user_id=request.user_id,
            products=request.products,
            shipping_address=request.shipping_address,
            payment_method=request.payment_method
        )
        
        # Process order in background
        background_tasks.add_task(
            agent.process_order_background,
            order_id=order["order_id"]
        )
        
        return {
            "success": True,
            "order": order
        }
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Temu integration endpoints
@app.get("/temu/products")
async def get_temu_products(
    category: Optional[str] = None,
    limit: int = 20,
    token: str = Depends(security)
):
    """Get products from Temu API"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Get products from Temu
        products = await temu_client.get_products(
            category=category,
            limit=limit
        )
        
        return {
            "success": True,
            "products": products
        }
    except Exception as e:
        logger.error(f"Error getting Temu products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/temu/categories")
async def get_temu_categories(token: str = Depends(security)):
    """Get available categories from Temu"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Get categories
        categories = await temu_client.get_categories()
        
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"Error getting Temu categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Correos de Costa Rica integration endpoints
@app.post("/correos/create-shipment")
async def create_shipment(
    order_id: str,
    recipient_info: Dict[str, str],
    token: str = Depends(security)
):
    """Create shipment with Correos de Costa Rica"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Create shipment
        shipment = await correos_client.create_shipment(
            order_id=order_id,
            recipient_info=recipient_info
        )
        
        return {
            "success": True,
            "shipment": shipment
        }
    except Exception as e:
        logger.error(f"Error creating shipment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/correos/track-shipment/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    token: str = Depends(security)
):
    """Track shipment with Correos de Costa Rica"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Track shipment
        tracking_info = await correos_client.track_shipment(tracking_number)
        
        return {
            "success": True,
            "tracking_info": tracking_info
        }
    except Exception as e:
        logger.error(f"Error tracking shipment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# SINPE integration endpoints
@app.post("/sinpe/verify-payment")
async def verify_payment(
    transaction_id: str,
    token: str = Depends(security)
):
    """Verify SINPE payment"""
    try:
        # Verify token
        user_data = verify_token(token.credentials)
        
        # Verify payment
        payment_status = await sinpe_client.verify_payment(transaction_id)
        
        return {
            "success": True,
            "payment_status": payment_status
        }
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/admin/conversations/{user_id}")
async def get_user_conversations(
    user_id: str,
    limit: int = 50,
    token: str = Depends(security)
):
    """Get user conversation history"""
    try:
        # Verify token (admin only)
        user_data = verify_token(token.credentials)
        
        # Get conversations
        conversations = await conversation_manager.get_user_conversations(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "conversations": conversations
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/analytics")
async def get_analytics(token: str = Depends(security)):
    """Get system analytics"""
    try:
        # Verify token (admin only)
        user_data = verify_token(token.credentials)
        
        # Get analytics
        analytics = await agent.get_analytics()
        
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 