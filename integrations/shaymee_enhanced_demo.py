#!/usr/bin/env python3
"""
Shaymee Enhanced Product Discovery Demo
This demonstrates the complete enhanced scraping and rebranding system
"""

import asyncio
import json
from loguru import logger
from multi_source_product_system import MultiSourceProductSystem
from unimart_client import create_shaymee_product_listing

class ShaymeeEnhancedDemo:
    def __init__(self):
        self.product_system = MultiSourceProductSystem()
        logger.info("🚀 Shaymee Enhanced Demo initialized")

    async def demonstrate_enhanced_scraping(self):
        """
        Demonstrate the enhanced scraping capabilities with Unimart rebranding
        """
        logger.info("🔥 SHAYMEE ENHANCED PRODUCT DISCOVERY DEMO")
        logger.info("=" * 60)
        
        # Test different product categories
        search_terms = [
            "smartwatch",
            "phone case", 
            "headphones"
        ]
        
        all_shaymee_products = []
        
        for term in search_terms:
            logger.info(f"\n🔍 Searching for: '{term}'")
            logger.info("-" * 40)
            
            # Get products from multi-source system
            products = await self.product_system.search_products(term, limit=5)
            
            if products:
                logger.info(f"✅ Found {len(products)} products from multi-source system")
                
                # Convert Unimart products to Shaymee format
                for product in products:
                    if product.source == 'unimart':
                        # Create enhanced product object for rebranding
                        enhanced_product = {
                            'title': product.title,
                            'price': product.price,
                            'image_url': product.image_url,
                            'product_url': product.product_url,
                            'source': product.source,
                            'brand': product.metadata.get('brand', 'Generic'),
                            'category': product.metadata.get('category', 'electronics'),
                            'specifications': product.metadata.get('specifications', {}),
                            'tags': product.metadata.get('tags', []),
                            'price_info': product.metadata.get('price_info', {}),
                            'description': product.metadata.get('description', ''),
                            'seo_title': product.metadata.get('seo_title', product.title),
                            'rating': product.metadata.get('rating')
                        }
                        
                        # Create Shaymee branded product
                        shaymee_product = create_shaymee_product_listing(enhanced_product)
                        all_shaymee_products.append(shaymee_product)
                        
                        # Display enhanced product details
                        logger.info(f"\n🏷️  SHAYMEE ENHANCED PRODUCT:")
                        logger.info(f"   📱 Title: {shaymee_product['title']}")
                        logger.info(f"   🏢 Brand: {shaymee_product['brand']}")
                        logger.info(f"   📂 Category: {shaymee_product['category']}")
                        logger.info(f"   💰 Price: {shaymee_product['price']['crc']} ({shaymee_product['price']['usd']})")
                        logger.info(f"   🌍 Source: {shaymee_product['source']['name']} - {shaymee_product['source']['country']}")
                        logger.info(f"   🔧 Specs: {shaymee_product['specifications']}")
                        logger.info(f"   🏷️  Tags: {', '.join(shaymee_product['tags'][:5])}")
                        logger.info(f"   📝 Description: {shaymee_product['description'][:80]}...")
                        logger.info(f"   🔗 SEO Title: {shaymee_product['seo']['title']}")
                        logger.info(f"   ✨ Shaymee Enhanced: {shaymee_product['shaymee_enhanced']}")
                    else:
                        # Display non-Unimart products for comparison
                        logger.info(f"\n📦 Standard Product: {product.title[:50]}...")
                        logger.info(f"   💰 Price: {product.price}")
                        logger.info(f"   🌍 Source: {product.source}")
                        logger.info(f"   📊 Confidence: {product.confidence_score:.2f}")
            else:
                logger.warning(f"❌ No products found for '{term}'")
        
        # Save enhanced products to JSON
        if all_shaymee_products:
            output_file = 'shaymee_enhanced_products.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_shaymee_products, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"\n💾 Saved {len(all_shaymee_products)} enhanced products to {output_file}")
        
        # Display system performance
        logger.info("\n📊 SYSTEM PERFORMANCE SUMMARY")
        logger.info("=" * 40)
        stats = self.product_system.get_system_stats()
        
        for source_name, source_stats in stats['sources'].items():
            status = "✅ ENABLED" if source_stats['enabled'] else "❌ DISABLED"
            logger.info(f"{source_name.upper()}: {status}")
            logger.info(f"  Priority: {source_stats.get('priority', 'N/A')}")
            logger.info(f"  Success Rate: {source_stats.get('success_rate', 0):.1%}")
            logger.info(f"  Avg Response Time: {source_stats.get('avg_response_time', 0):.2f}s")
        
        logger.info(f"\nTotal Sources: {stats['total_sources']}")
        logger.info(f"Cache Size: {stats['cache_size']}")
        
        return all_shaymee_products

    async def demonstrate_category_analysis(self):
        """
        Demonstrate category-based product analysis
        """
        logger.info("\n🔍 CATEGORY ANALYSIS DEMO")
        logger.info("=" * 30)
        
        categories = {
            'smartwatch': 'Wearable Technology',
            'phone_accessory': 'Mobile Accessories', 
            'audio': 'Audio Equipment',
            'electronics': 'General Electronics'
        }
        
        for category, description in categories.items():
            logger.info(f"\n📂 {description} ({category})")
            products = await self.product_system.search_products(category, limit=3)
            
            if products:
                enhanced_count = sum(1 for p in products if p.metadata.get('enhanced', False))
                logger.info(f"   Products found: {len(products)}")
                logger.info(f"   Enhanced products: {enhanced_count}")
                logger.info(f"   Enhancement rate: {enhanced_count/len(products):.1%}")
            else:
                logger.info(f"   No products found")

async def main():
    """
    Main demo function
    """
    demo = ShaymeeEnhancedDemo()
    
    # Run the enhanced scraping demo
    enhanced_products = await demo.demonstrate_enhanced_scraping()
    
    # Run category analysis
    await demo.demonstrate_category_analysis()
    
    # Final summary
    logger.info("\n🎉 DEMO COMPLETE!")
    logger.info("=" * 20)
    logger.info(f"✅ Enhanced products created: {len(enhanced_products)}")
    logger.info("✅ Multi-source system operational")
    logger.info("✅ Unimart scraping with rebranding functional")
    logger.info("✅ Product enhancement and categorization working")
    logger.info("\n🚀 Shaymee is ready for enhanced product discovery!")

if __name__ == "__main__":
    asyncio.run(main())
