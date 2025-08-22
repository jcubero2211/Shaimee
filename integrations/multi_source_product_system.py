import asyncio
import random
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from datetime import datetime
import json

# Import our existing scrapers
from pequeno_mundo_client_clean import PequenoMundoClient
from aliexpress_client import AliExpressClient
from unimart_client import UnimartClient

@dataclass
class ProductSource:
    """Represents a product source with metadata"""
    name: str
    priority: int  # Lower number = higher priority
    enabled: bool = True
    last_success: Optional[datetime] = None
    success_rate: float = 0.0
    avg_response_time: float = 0.0

@dataclass
class ProductResult:
    """Standardized product result from any source"""
    title: str
    price: str
    image_url: str
    product_url: str
    source: str
    confidence_score: float = 0.0
    extracted_at: datetime = None
    metadata: Dict[str, Any] = None

class MultiSourceProductSystem:
    """
    Intelligent multi-source product aggregation system for Shaymee
    """
    
    def __init__(self):
        self.sources = {
            'pequeno_mundo': ProductSource(
                name='Pequeño Mundo',
                priority=1,
                enabled=True
            ),
            'unimart': ProductSource(
                name='Unimart',
                priority=1,
                enabled=True
            ),
            'aliexpress': ProductSource(
                name='AliExpress',
                priority=2,
                enabled=True
            ),
            'manual_fallback': ProductSource(
                name='Manual Fallback',
                priority=3,
                enabled=True
            )
        }
        
        # Initialize scrapers
        self.pequeno_mundo_client = PequenoMundoClient()
        self.aliexpress_client = AliExpressClient()
        self.unimart_client = UnimartClient()
        
        # Product cache for performance
        self.product_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Load configuration
        self.config = self._load_config()
        
        logger.info("🚀 Multi-Source Product System initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        try:
            with open('product_system_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            config = {
                'max_products_per_source': 20,
                'min_confidence_score': 0.3,
                'enable_caching': True,
                'parallel_scraping': True,
                'retry_attempts': 3,
                'timeout_per_source': 30,
                'sources': {
                    'pequeno_mundo': {
                        'enabled': True,
                        'priority': 1,
                        'max_products': 25
                    },
                    'aliexpress': {
                        'enabled': True,
                        'priority': 2,
                        'max_products': 20
                    }
                }
            }
            
            # Save default config
            with open('product_system_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            return config

    async def search_products(self, search_term: str, limit: int = 20, 
                            sources: Optional[List[str]] = None) -> List[ProductResult]:
        """
        Search for products across multiple sources with intelligent fallback
        """
        logger.info(f"🔍 Multi-source search for: '{search_term}' (limit: {limit})")
        
        # Use specified sources or all enabled sources
        if sources is None:
            sources = [name for name, source in self.sources.items() if source.enabled]
        
        # Sort sources by priority
        sources = sorted(sources, key=lambda s: self.sources[s].priority)
        
        # Check cache first
        cache_key = f"{search_term.lower()}_{limit}"
        enable_caching = self.config.get('system_settings', {}).get('cache_ttl_seconds', 0) > 0
        if enable_caching and cache_key in self.product_cache:
            cached_result = self.product_cache[cache_key]
            if (datetime.now() - cached_result['timestamp']).seconds < self.cache_ttl:
                logger.info("✅ Returning cached results")
                return cached_result['products']
        
        # Collect products from all sources
        all_products = []
        
        parallel_scraping = self.config.get('system_settings', {}).get('parallel_scraping', True)
        if parallel_scraping:
            # Parallel scraping for better performance
            tasks = []
            for source_name in sources:
                task = self._scrape_source(source_name, search_term, limit)
                tasks.append(task)
            
            # Execute all scraping tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = sources[i]
                if isinstance(result, Exception):
                    logger.error(f"❌ {source_name} failed: {result}")
                    self._update_source_stats(source_name, success=False)
                else:
                    all_products.extend(result)
                    self._update_source_stats(source_name, success=True, 
                                           product_count=len(result))
        else:
            # Sequential scraping (more reliable but slower)
            for source_name in sources:
                try:
                    products = await self._scrape_source(source_name, search_term, limit)
                    all_products.extend(products)
                    self._update_source_stats(source_name, success=True, 
                                           product_count=len(products))
                except Exception as e:
                    logger.error(f"❌ {source_name} failed: {e}")
                    self._update_source_stats(source_name, success=False)
        
        # Process and rank products
        processed_products = self._process_and_rank_products(all_products, search_term)
        
        # Apply limit and deduplication
        final_products = self._deduplicate_and_limit(processed_products, limit)
        
        # Cache results
        if enable_caching:
            self.product_cache[cache_key] = {
                'products': final_products,
                'timestamp': datetime.now()
            }
        
        logger.info(f"✅ Multi-source search completed: {len(final_products)} products found")
        return final_products

    async def _scrape_source(self, source_name: str, search_term: str, 
                            limit: int) -> List[ProductResult]:
        """Scrape products from a specific source"""
        start_time = datetime.now()
        
        try:
            if source_name == 'pequeno_mundo':
                return await self._scrape_pequeno_mundo(search_term, limit)
            elif source_name == 'aliexpress':
                return await self._scrape_aliexpress(search_term, limit)
            elif source_name == 'unimart':
                return await self._scrape_unimart(search_term, limit)
            elif source_name == 'manual_fallback':
                return await self._get_manual_fallback(search_term, limit)
            else:
                logger.warning(f"⚠️ Unknown source: {source_name}")
                return []
                
        except Exception as e:
            logger.error(f"💥 Error scraping {source_name}: {e}")
            raise
        finally:
            # Update response time
            response_time = (datetime.now() - start_time).total_seconds()
            self.sources[source_name].avg_response_time = (
                (self.sources[source_name].avg_response_time + response_time) / 2
            )

    async def _scrape_pequeno_mundo(self, search_term: str, limit: int) -> List[ProductResult]:
        """Scrape products from Pequeño Mundo"""
        logger.info(f"🇨🇷 Scraping Pequeño Mundo for: {search_term}")
        
        try:
            raw_products = await self.pequeno_mundo_client.get_products(search_term, limit)
            
            if not raw_products:
                return []
            
            # Convert to standardized format
            products = []
            for raw_product in raw_products:
                product = ProductResult(
                    title=raw_product.get('title', 'N/A'),
                    price=raw_product.get('price', 'N/A'),
                    image_url=raw_product.get('imageUrl', 'N/A'),
                    product_url=raw_product.get('productUrl', 'N/A'),
                    source='Pequeño Mundo',
                    confidence_score=0.9,  # High confidence for working scraper
                    extracted_at=datetime.now(),
                    metadata={'raw_data': raw_product}
                )
                products.append(product)
            
            logger.info(f"✅ Pequeño Mundo: {len(products)} products found")
            return products
            
        except Exception as e:
            logger.error(f"💥 Pequeño Mundo scraping failed: {e}")
            return []

    async def _scrape_aliexpress(self, search_term: str, limit: int) -> List[ProductResult]:
        """Scrape products from AliExpress using AliExpressClient"""
        logger.info(f"🌏 Scraping AliExpress for: {search_term}")
        
        try:
            # Use the actual AliExpress client
            products = await self.aliexpress_client.get_products(search_term, limit)
            
            if not products:
                logger.warning("⚠️ No products returned from AliExpress")
                return []
            
            # Convert to ProductResult objects
            results = []
            for product in products:
                result = ProductResult(
                    title=product.get('title', 'No title'),
                    price=product.get('price', 'N/A'),
                    image_url=product.get('image_url', ''),
                    product_url=product.get('product_url', ''),
                    source='aliexpress',
                    confidence_score=0.8,  # AliExpress is generally reliable
                    extracted_at=datetime.now(),
                    metadata={
                        'rating': product.get('rating', 0),
                        'orders': product.get('orders', 'Unknown'),
                        'shipping': product.get('shipping', 'Unknown'),
                        'source_type': 'scraped'
                    }
                )
                results.append(result)
            
            logger.info(f"✅ AliExpress returned {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"💥 AliExpress scraping failed: {e}")
            return []

    async def _scrape_unimart(self, search_term: str, limit: int) -> List[ProductResult]:
        """Scrape products from Unimart using UnimartClient"""
        logger.info(f"🇨🇷 Scraping Unimart for: {search_term}")
        
        try:
            # Use the Unimart client
            products = await self.unimart_client.get_products(search_term, limit)
            
            if not products:
                logger.warning("⚠️ No products returned from Unimart")
                return []
            
            # Convert to ProductResult objects with enhanced data
            results = []
            for product in products:
                # Use enhanced data if available
                metadata = {
                    'rating': product.get('rating', 0),
                    'source_type': 'scraped',
                    'local_retailer': True,
                    'country': 'Costa Rica',
                    'brand': product.get('brand', 'Generic'),
                    'category': product.get('category', 'electronics'),
                    'specifications': product.get('specifications', {}),
                    'tags': product.get('tags', []),
                    'price_info': product.get('price_info', {}),
                    'description': product.get('description', ''),
                    'seo_title': product.get('seo_title', ''),
                    'enhanced': product.get('brand') is not None  # Flag for enhanced products
                }
                
                result = ProductResult(
                    title=product.get('seo_title', product.get('title', 'No title')),
                    price=product.get('price_info', {}).get('formatted_crc', product.get('price', 'N/A')),
                    image_url=product.get('image_url', ''),
                    product_url=product.get('product_url', ''),
                    source='unimart',
                    confidence_score=0.95 if metadata['enhanced'] else 0.9,  # Higher score for enhanced products
                    extracted_at=datetime.now(),
                    metadata=metadata
                )
                results.append(result)
            
            logger.info(f"✅ Unimart returned {len(results)} products")
            return results
            
        except Exception as e:
            logger.error(f"💥 Unimart scraping failed: {e}")
            return []

    async def _get_manual_fallback(self, search_term: str, limit: int) -> List[ProductResult]:
        """Get manual fallback products (placeholder data)"""
        logger.info(f"📝 Getting manual fallback for: {search_term}")
        
        # Placeholder manual products - in real implementation, this could be:
        # - Database of manually curated products
        # - API calls to other services
        # - Integration with WhatsApp Business catalog
        
        fallback_products = [
            ProductResult(
                title=f"Manual Product - {search_term}",
                price="Contact for pricing",
                image_url="https://via.placeholder.com/150x150?text=Manual+Product",
                product_url="https://shaymee.com/contact",
                source="Manual Fallback",
                confidence_score=0.5,
                extracted_at=datetime.now(),
                metadata={'type': 'manual_fallback', 'requires_contact': True}
            )
        ]
        
        return fallback_products[:limit]

    def _process_and_rank_products(self, products: List[ProductResult], 
                                 search_term: str) -> List[ProductResult]:
        """Process and rank products by relevance and quality"""
        logger.info(f"🔍 Processing and ranking {len(products)} products")
        
        for product in products:
            # Calculate confidence score based on data quality
            confidence = 0.0
            
            # Title quality
            if product.title and product.title != 'N/A':
                title_lower = product.title.lower()
                search_lower = search_term.lower()
                
                # Exact match bonus
                if search_term.lower() in title_lower:
                    confidence += 0.4
                
                # Word overlap bonus
                search_words = set(search_lower.split())
                title_words = set(title_lower.split())
                overlap = len(search_words.intersection(title_words))
                confidence += min(overlap * 0.1, 0.3)
            
            # Price quality
            if product.price and product.price != 'N/A':
                confidence += 0.2
            
            # Image quality
            if product.image_url and product.image_url != 'N/A':
                confidence += 0.1
            
            # URL quality
            if product.product_url and product.product_url != 'N/A':
                confidence += 0.1
            
            # Source reliability bonus
            if product.source == 'Pequeño Mundo':
                confidence += 0.1
            
            product.confidence_score = min(confidence, 1.0)
        
        # Sort by confidence score (highest first)
        products.sort(key=lambda p: p.confidence_score, reverse=True)
        
        logger.info(f"✅ Products ranked by confidence score")
        return products

    def _deduplicate_and_limit(self, products: List[ProductResult], 
                              limit: int) -> List[ProductResult]:
        """Remove duplicates and apply limit"""
        logger.info(f"🔄 Deduplicating and limiting to {limit} products")
        
        # Simple deduplication based on title similarity
        unique_products = []
        seen_titles = set()
        
        for product in products:
            # Normalize title for comparison
            normalized_title = product.title.lower().strip()
            
            # Check if similar title already exists
            is_duplicate = False
            for seen_title in seen_titles:
                if self._calculate_similarity(normalized_title, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_products.append(product)
                seen_titles.add(normalized_title)
                
                if len(unique_products) >= limit:
                    break
        
        logger.info(f"✅ Deduplication complete: {len(unique_products)} unique products")
        return unique_products

    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles (simple implementation)"""
        if not title1 or not title2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    def _update_source_stats(self, source_name: str, success: bool, 
                           product_count: int = 0):
        """Update source statistics"""
        if source_name not in self.sources:
            return
        
        source = self.sources[source_name]
        
        if success:
            source.last_success = datetime.now()
            # Update success rate (simple moving average)
            source.success_rate = (source.success_rate * 0.9) + 0.1
        else:
            source.success_rate = source.success_rate * 0.9

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        stats = {
            'total_sources': len(self.sources),
            'enabled_sources': len([s for s in self.sources.values() if s.enabled]),
            'cache_size': len(self.product_cache),
            'sources': {}
        }
        
        for name, source in self.sources.items():
            stats['sources'][name] = {
                'enabled': source.enabled,
                'priority': source.priority,
                'success_rate': source.success_rate,
                'avg_response_time': source.avg_response_time,
                'last_success': source.last_success.isoformat() if source.last_success else None
            }
        
        return stats

    def enable_source(self, source_name: str, enabled: bool = True):
        """Enable or disable a source"""
        if source_name in self.sources:
            self.sources[source_name].enabled = enabled
            logger.info(f"✅ {source_name} {'enabled' if enabled else 'disabled'}")

    def set_source_priority(self, source_name: str, priority: int):
        """Set priority for a source (lower number = higher priority)"""
        if source_name in self.sources:
            self.sources[source_name].priority = priority
            logger.info(f"✅ {source_name} priority set to {priority}")

# Test function
async def test_multi_source_system():
    """Test the multi-source product system"""
    logger.info("🧪 Testing Multi-Source Product System...")
    
    system = MultiSourceProductSystem()
    
    # Test search
    products = await system.search_products("phone case", limit=10)
    
    if products:
        print(f"✅ Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.title}")
            print(f"   Source: {product.source}")
            print(f"   Price: {product.price}")
            print(f"   Confidence: {product.confidence_score:.2f}")
            print()
    else:
        print("❌ No products found")
    
    # Show system stats
    stats = system.get_system_stats()
    print("📊 System Statistics:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(test_multi_source_system())
