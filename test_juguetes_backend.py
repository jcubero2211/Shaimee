#!/usr/bin/env python3
"""
Backend-only test for juguetes (toys) scraping and rebranding
Uses aiohttp + BeautifulSoup approach - no browser automation
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from integrations.pequeno_mundo_client_clean_fixed import PequenoMundoClient
from integrations.product_rebrander import ProductRebrander

# Configure logging
logger.add("juguetes_backend_test.log", rotation="500 MB", level="INFO")

async def test_juguetes_backend():
    """Test the backend scraping approach for toys"""
    load_dotenv()
    
    logger.info("🧸 Testing juguetes with backend scraping approach...")
    
    # Initialize clients
    pm_client = PequenoMundoClient()
    rebrander = ProductRebrander(
        brand_name="Shaymee",
        target_profit_margin=0.35,
        shipping_cost=3.50
    )
    
    search_term = "juguetes"
    
    try:
        # Step 1: Try to scrape juguetes from PM
        logger.info(f"🔍 Scraping '{search_term}' from Pequeño Mundo...")
        products = await pm_client.get_products(search_term, limit=5)
        
        if products:
            logger.success(f"✅ Successfully scraped {len(products)} toys!")
            
            # Show what we found
            for i, product in enumerate(products, 1):
                logger.info(f"📦 Toy #{i}:")
                logger.info(f"  Title: {product.get('title', 'N/A')}")
                logger.info(f"  Price: {product.get('price', 'N/A')}")
                logger.info(f"  Image: {product.get('imageUrl', 'N/A')}")
                logger.info(f"  URL: {product.get('productUrl', 'N/A')}")
                print()
            
            # Step 2: Rebrand the first 3 toys
            logger.info("🎨 Rebranding toys with AI...")
            selected_toys = products[:3]  # Take first 3
            rebranded_toys = await rebrander.rebrand_products(selected_toys, search_term=search_term)
            
            # Step 3: Show results
            logger.success("🎉 Rebranding completed!")
            total_cost = 0
            total_revenue = 0
            
            for i, toy in enumerate(rebranded_toys, 1):
                logger.info(f"\n{'='*50}")
                logger.info(f"🧸 REBRANDED TOY #{i}")
                logger.info(f"📦 Original: {toy.get('title', 'N/A')}")
                logger.info(f"🏷️  New Name: {toy.get('rebranded_name', 'N/A')}")
                logger.info(f"💬 Description: {toy.get('description', 'N/A')}")
                
                # Pricing info
                pricing = toy.get('pricing', {})
                original_price = pricing.get('original_price', 0)
                selling_price = pricing.get('selling_price', 0)
                profit = pricing.get('profit', 0)
                margin = pricing.get('profit_margin', 0)
                
                logger.info(f"💰 Price: ₡{original_price:,.0f} → ₡{selling_price:,.0f}")
                logger.info(f"📈 Profit: ₡{profit:,.0f} ({margin*100:.1f}%)")
                logger.info(f"⚖️  Weight: {toy.get('weight_class', 'unknown')}")
                
                total_cost += original_price
                total_revenue += selling_price
                
                # Features
                if features := toy.get('key_features', []):
                    logger.info("🌟 Key Features:")
                    for feature in features:
                        logger.info(f"   • {feature}")
                
                # Image processing
                processed_image = toy.get('processed_image')
                if processed_image:
                    logger.info(f"🖼️  Image: {processed_image}")
                    if os.path.exists(processed_image):
                        logger.info("✅ Image file exists")
                    else:
                        logger.warning("⚠️  Image file not found")
            
            # Summary
            total_profit = total_revenue - total_cost
            avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            logger.info(f"\n📊 BUSINESS SUMMARY:")
            logger.info(f"🧸 Total Toys: {len(rebranded_toys)}")
            logger.info(f"💸 Total Cost: ₡{total_cost:,.2f}")
            logger.info(f"💰 Total Revenue: ₡{total_revenue:,.2f}")
            logger.info(f"📈 Total Profit: ₡{total_profit:,.2f}")
            logger.info(f"🎯 Avg Margin: {avg_margin:.1f}%")
            
        else:
            # Fallback to mock data if scraping fails
            logger.warning("⚠️  No toys found from scraping, using mock data...")
            
            mock_toys = [
                {
                    'title': 'Carro de Control Remoto Monster Truck',
                    'price': '₡18,500',
                    'imageUrl': 'https://images.unsplash.com/photo-1558618666-fbd29c5cd2c0?w=400',
                    'productUrl': 'https://tienda.pequenomundo.com/mock/carro-rc'
                },
                {
                    'title': 'Set de Bloques Construcción Castillo 300pcs',
                    'price': '₡15,200',
                    'imageUrl': 'https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=400',
                    'productUrl': 'https://tienda.pequenomundo.com/mock/bloques-castillo'
                }
            ]
            
            logger.info("📦 Processing mock toys...")
            rebranded_toys = await rebrander.rebrand_products(mock_toys, search_term=search_term)
            
            for i, toy in enumerate(rebranded_toys, 1):
                logger.info(f"🧸 Mock Toy #{i}: {toy.get('rebranded_name', 'N/A')}")
        
        logger.success("✅ Backend juguetes test completed!")
        
    except Exception as e:
        logger.error(f"❌ Error during test: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_juguetes_backend())
