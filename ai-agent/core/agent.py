import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from loguru import logger

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.schema import AgentAction, AgentFinish

from .product_search import ProductSearchEngine
from .conversation_manager import ConversationManager
from .payment_processor import PaymentProcessor
from integrations.temu_client import TemuClient
from integrations.correos_client import CorreosClient
from integrations.sinpe_client import SinpeClient
from utils.database import get_db
from utils.auth import verify_token

class ShaymeeAgent:
    """
    Main AI Agent for Shaymee store that orchestrates all interactions
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize components
        self.product_search = ProductSearchEngine()
        self.conversation_manager = ConversationManager()
        self.payment_processor = PaymentProcessor()
        self.temu_client = TemuClient()
        self.correos_client = CorreosClient()
        self.sinpe_client = SinpeClient()
        
        # Initialize memory for conversations
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent_executor = self._initialize_agent()
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        logger.info("Shaymee AI Agent initialized successfully")
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize tools for the agent"""
        tools = [
            Tool(
                name="search_products",
                func=self._search_products_tool,
                description="Search for products in the catalog. Use this when user asks for products or wants to buy something."
            ),
            Tool(
                name="get_categories",
                func=self._get_categories_tool,
                description="Get available product categories. Use this when user asks about categories or wants to browse."
            ),
            Tool(
                name="create_order",
                func=self._create_order_tool,
                description="Create a new order for products. Use this when user wants to purchase items."
            ),
            Tool(
                name="generate_payment",
                func=self._generate_payment_tool,
                description="Generate payment link for SINPE. Use this when user is ready to pay."
            ),
            Tool(
                name="track_order",
                func=self._track_order_tool,
                description="Track order status and shipment. Use this when user asks about their order status."
            ),
            Tool(
                name="get_user_info",
                func=self._get_user_info_tool,
                description="Get user information and preferences. Use this to personalize responses."
            )
        ]
        return tools
    
    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the agent executor"""
        prompt = PromptTemplate(
            input_variables=["input", "chat_history", "agent_scratchpad"],
            template=self.prompts["agent_prompt"]
        )
        
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=self._parse_agent_output,
            stop=["\nObservation:"],
            allowed_tools=[tool.name for tool in self.tools]
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory
        )
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates"""
        return {
            "agent_prompt": """You are Shaymee, a friendly and helpful AI assistant for an online store in Costa Rica. You help customers find products, make purchases, and track their orders.

Your personality:
- Always be polite and courteous in Spanish
- Use "usted" form for respect
- Be helpful and patient
- Provide clear and concise information
- Always mention that you're from Shaymee store

Available tools:
{tools}

Current conversation:
{chat_history}

Human: {input}
{agent_scratchpad}

Assistant: Let me help you with that. I'll use the appropriate tool to assist you.""",
            
            "greeting_prompt": """¡Hola! Soy Shaymee, tu asistente virtual de la tienda Shaymee. 

¿En qué puedo ayudarte hoy? Puedo:
• Ayudarte a encontrar productos
• Mostrarte nuestras categorías
• Procesar tu compra
• Dar seguimiento a tus pedidos

¿Qué te gustaría hacer?""",
            
            "product_search_prompt": """Basándome en tu descripción, aquí tienes algunos productos que podrían interesarte:

{products}

¿Te gustaría ver más detalles de algún producto o necesitas ayuda con algo más?""",
            
            "payment_prompt": """Perfecto, he generado tu link de pago SINPE:

🔗 Link de Pago: {payment_link}
💰 Total: ₡{amount}
📦 Pedido: #{order_id}

Una vez que realices el pago, te enviaré la confirmación y comenzaremos a procesar tu pedido.

¿Necesitas ayuda con el pago?""",
            
            "order_confirmation_prompt": """¡Excelente! Tu pedido ha sido confirmado:

📦 Pedido: #{order_id}
✅ Estado: Confirmado
📅 Fecha: {date}
🚚 Envío: En proceso

Te mantendremos informado sobre el estado de tu pedido. ¿Hay algo más en lo que pueda ayudarte?"""
        }
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process user message and generate response"""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Add context to message
            if context:
                message = f"Context: {json.dumps(context)}\nUser message: {message}"
            
            # Process with agent
            response = await self.agent_executor.arun(message)
            
            # Store conversation
            await self.conversation_manager.store_conversation(
                user_id=user_id,
                message=message,
                response=response,
                session_id=session_id
            )
            
            return {
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentarlo de nuevo?",
                "session_id": session_id,
                "error": str(e)
            }
    
    async def create_order(
        self,
        user_id: str,
        products: List[Dict[str, Any]],
        shipping_address: Dict[str, str],
        payment_method: str = "sinpe"
    ) -> Dict[str, Any]:
        """Create a new order"""
        try:
            order_id = str(uuid.uuid4())
            
            # Calculate total
            total = sum(product.get("price", 0) for product in products)
            
            # Create order in database
            order_data = {
                "order_id": order_id,
                "user_id": user_id,
                "products": products,
                "total": total,
                "shipping_address": shipping_address,
                "payment_method": payment_method,
                "status": "pending_payment",
                "created_at": datetime.now().isoformat()
            }
            
            # Store order
            await self._store_order(order_data)
            
            # Generate payment link
            payment_link = await self.payment_processor.generate_payment_link(
                order_id=order_id,
                amount=total,
                currency="CRC",
                payment_method=payment_method
            )
            
            return {
                "order_id": order_id,
                "total": total,
                "payment_link": payment_link,
                "status": "pending_payment"
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise e
    
    async def process_order_background(self, order_id: str):
        """Process order in background after payment confirmation"""
        try:
            # Get order details
            order = await self._get_order(order_id)
            
            if not order:
                logger.error(f"Order {order_id} not found")
                return
            
            # Update status to processing
            await self._update_order_status(order_id, "processing")
            
            # Purchase from Temu
            temu_order = await self.temu_client.create_order(
                products=order["products"],
                shipping_address=order["shipping_address"]
            )
            
            # Update order with Temu reference
            await self._update_order_temu_reference(order_id, temu_order["temu_order_id"])
            
            # Update status to purchased
            await self._update_order_status(order_id, "purchased")
            
            # Notify user
            await self._notify_user_order_update(order["user_id"], order_id, "purchased")
            
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {str(e)}")
            await self._update_order_status(order_id, "error")
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get system analytics"""
        try:
            # Get conversation stats
            conversation_stats = await self.conversation_manager.get_stats()
            
            # Get order stats
            order_stats = await self._get_order_stats()
            
            # Get product stats
            product_stats = await self.product_search.get_stats()
            
            return {
                "conversations": conversation_stats,
                "orders": order_stats,
                "products": product_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {"error": str(e)}
    
    # Tool functions
    async def _search_products_tool(self, query: str) -> str:
        """Search products tool"""
        try:
            products = await self.product_search.search(query=query, limit=5)
            return f"Found {len(products)} products: {json.dumps(products, indent=2)}"
        except Exception as e:
            return f"Error searching products: {str(e)}"
    
    async def _get_categories_tool(self) -> str:
        """Get categories tool"""
        try:
            categories = await self.temu_client.get_categories()
            return f"Available categories: {json.dumps(categories, indent=2)}"
        except Exception as e:
            return f"Error getting categories: {str(e)}"
    
    async def _create_order_tool(self, order_data: str) -> str:
        """Create order tool"""
        try:
            data = json.loads(order_data)
            order = await self.create_order(**data)
            return f"Order created: {json.dumps(order, indent=2)}"
        except Exception as e:
            return f"Error creating order: {str(e)}"
    
    async def _generate_payment_tool(self, payment_data: str) -> str:
        """Generate payment tool"""
        try:
            data = json.loads(payment_data)
            payment_link = await self.payment_processor.generate_payment_link(**data)
            return f"Payment link generated: {payment_link}"
        except Exception as e:
            return f"Error generating payment: {str(e)}"
    
    async def _track_order_tool(self, order_id: str) -> str:
        """Track order tool"""
        try:
            order = await self._get_order(order_id)
            if order:
                return f"Order status: {json.dumps(order, indent=2)}"
            else:
                return "Order not found"
        except Exception as e:
            return f"Error tracking order: {str(e)}"
    
    async def _get_user_info_tool(self, user_id: str) -> str:
        """Get user info tool"""
        try:
            user_info = await self._get_user_info(user_id)
            return f"User info: {json.dumps(user_info, indent=2)}"
        except Exception as e:
            return f"Error getting user info: {str(e)}"
    
    def _parse_agent_output(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse agent output"""
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        # Parse tool usage
        if "Action:" in text and "Action Input:" in text:
            action = text.split("Action:")[1].split("\n")[0].strip()
            action_input = text.split("Action Input:")[1].split("\n")[0].strip()
            return AgentAction(tool=action, tool_input=action_input, log=text)
        
        return AgentFinish(return_values={"output": text}, log=text)
    
    # Database helper methods
    async def _store_order(self, order_data: Dict[str, Any]):
        """Store order in database"""
        # Implementation depends on your database setup
        pass
    
    async def _get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order from database"""
        # Implementation depends on your database setup
        pass
    
    async def _update_order_status(self, order_id: str, status: str):
        """Update order status"""
        # Implementation depends on your database setup
        pass
    
    async def _update_order_temu_reference(self, order_id: str, temu_order_id: str):
        """Update order with Temu reference"""
        # Implementation depends on your database setup
        pass
    
    async def _get_order_stats(self) -> Dict[str, Any]:
        """Get order statistics"""
        # Implementation depends on your database setup
        pass
    
    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information"""
        # Implementation depends on your database setup
        pass
    
    async def _notify_user_order_update(self, user_id: str, order_id: str, status: str):
        """Notify user about order update"""
        # Implementation depends on your notification system
        pass 