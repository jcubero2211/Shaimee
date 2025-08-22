#!/usr/bin/env python3
"""
Shaymee AI Agent Integration Example
This shows how the AI agent can use the multi-source product system
"""

import asyncio
from loguru import logger
from multi_source_product_system import MultiSourceProductSystem

class ShaymeeProductAgent:
    """
    Example integration of multi-source product system with Shaymee AI Agent
    """
    
    def __init__(self):
        self.product_system = MultiSourceProductSystem()
        logger.info("🤖 Shaymee Product Agent initialized")
    
    async def search_products_for_user(self, user_query: str, max_results: int = 10):
        """
        Main method that Shaymee AI Agent would call to search for products
        """
        logger.info(f"👤 User query: '{user_query}'")
        
        # Extract search terms from user query (in real implementation, this would use NLP)
        search_term = self._extract_search_terms(user_query)
        logger.info(f"🔍 Extracted search term: '{search_term}'")
        
        # Search across all available sources
        products = await self.product_system.search_products(search_term, limit=max_results)
        
        if products:
            logger.info(f"✅ Found {len(products)} products for user")
            return self._format_response_for_user(products, user_query)
        else:
            logger.warning("⚠️ No products found")
            return self._no_products_response(user_query)
    
    def _extract_search_terms(self, user_query: str) -> str:
        """
        Extract search terms from user query (simplified version)
        In real implementation, this would use advanced NLP
        """
        # Simple keyword extraction
        query_lower = user_query.lower()
        
        # Remove common words
        stop_words = {'i', 'need', 'want', 'looking', 'for', 'a', 'an', 'the', 'some', 'any', 'buy', 'get', 'find'}
        words = query_lower.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return ' '.join(keywords)
    
    def _format_response_for_user(self, products, original_query: str) -> str:
        """
        Format the product results for the user in a conversational way
        """
        response = f"🛍️ I found {len(products)} products for '{original_query}':\n\n"
        
        for i, product in enumerate(products, 1):
            source_emoji = {
                'pequeno_mundo': '🇨🇷',
                'aliexpress': '🌏',
                'manual_fallback': '📝',
                'temu': '🛒'
            }.get(product.source, '🔍')
            
            response += f"{i}. **{product.title}**\n"
            response += f"   💰 Price: {product.price}\n"
            response += f"   {source_emoji} Source: {product.source.replace('_', ' ').title()}\n"
            response += f"   🎯 Confidence: {product.confidence_score:.1f}/10\n"
            
            if product.product_url:
                response += f"   🔗 Link: {product.product_url}\n"
            
            response += "\n"
        
        # Add system stats for transparency
        stats = self.product_system.get_system_stats()
        enabled_sources = [name for name, info in stats['sources'].items() if info['enabled']]
        response += f"📊 Searched across {len(enabled_sources)} sources: {', '.join(enabled_sources)}\n"
        
        return response
    
    def _no_products_response(self, original_query: str) -> str:
        """
        Response when no products are found
        """
        return f"""
😔 I couldn't find any products for '{original_query}' right now.

This could be because:
• The product sources are temporarily unavailable
• The search term might need adjustment
• The product might not be available in our current sources

💡 Try:
• Using different keywords
• Being more specific (e.g., "iPhone 14 case" instead of "phone case")
• Asking me to search for similar products

I'm constantly working to improve my search capabilities! 🚀
"""

    async def get_system_health(self) -> str:
        """
        Check the health of all product sources
        """
        stats = self.product_system.get_system_stats()
        
        health_report = "🏥 **System Health Report**\n\n"
        
        for source_name, source_info in stats['sources'].items():
            status_emoji = "✅" if source_info['enabled'] else "❌"
            success_rate = source_info['success_rate'] * 100
            
            health_report += f"{status_emoji} **{source_name.replace('_', ' ').title()}**\n"
            health_report += f"   📊 Success Rate: {success_rate:.1f}%\n"
            health_report += f"   ⚡ Avg Response: {source_info['avg_response_time']:.2f}s\n"
            health_report += f"   🔄 Priority: {source_info.get('priority', 'N/A')}\n\n"
        
        health_report += f"💾 Cache Size: {stats['cache_size']} entries\n"
        health_report += f"🔌 Total Sources: {stats['total_sources']}\n"
        
        return health_report


async def demo_shaymee_integration():
    """
    Demonstrate how Shaymee AI Agent would use the multi-source system
    """
    logger.info("🎬 Starting Shaymee Integration Demo...")
    
    agent = ShaymeeProductAgent()
    
    # Simulate different user queries
    user_queries = [
        "I need a phone case for my iPhone",
        "Looking for bluetooth headphones under $50",
        "Want to buy a laptop stand for work",
        "Find me wireless earbuds"
    ]
    
    for query in user_queries:
        logger.info(f"\n" + "="*60)
        logger.info(f"🗣️ User says: '{query}'")
        logger.info("="*60)
        
        response = await agent.search_products_for_user(query, max_results=5)
        print(response)
        
        # Small delay between queries
        await asyncio.sleep(1)
    
    # Show system health
    logger.info(f"\n" + "="*60)
    logger.info("🏥 Checking System Health...")
    logger.info("="*60)
    
    health_report = await agent.get_system_health()
    print(health_report)


if __name__ == "__main__":
    asyncio.run(demo_shaymee_integration())
