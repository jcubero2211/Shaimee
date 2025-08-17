import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from integrations.pequeno_mundo_client import PequenoMundoClient
from integrations.product_rebrander import ProductRebrander

# Configure logging
logger.add("shaymee_workflow.log", rotation="500 MB", level="INFO")

async def main():
    # Load environment
    load_dotenv()
    
    logger.info("🚀 Starting Shaymee E-commerce Automation Workflow")
    
    # Initialize clients
    scraper = PequenoMundoClient()
    rebrander = ProductRebrander(
        brand_name=os.getenv("BRAND_NAME", "Shaymee"),
        target_profit_margin=float(os.getenv("TARGET_PROFIT_MARGIN", 0.35)),
        shipping_cost=float(os.getenv("SHIPPING_COST", 5.00))
    )
    
    try:
        # Step 1: Scrape products
        search_term = "Relojes"  # Example search term
        logger.info(f"🔍 Searching for: {search_term}")
        products = await scraper.get_products(search_term, limit=3)  # Limit to 3 for testing
        
        if not products:
            logger.error("❌ No products found. Exiting...")
            return
            
        # Step 2: Rebrand products with search term for organized storage
        logger.info("🎨 Processing products with AI...")
        rebranded_products = await rebrander.rebrand_products(products, search_term=search_term)
        
        # Display results
        logger.success("\n✨ Rebranding Complete! Here are your products:")
        for i, product in enumerate(rebranded_products, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🆔 Product #{i}")
            logger.info(f"📦 Original: {product.get('title')}")
            logger.info(f"🏷️  Rebranded: {product.get('rebranded_name')}")
            logger.info(f"💬 Description: {product.get('description')}")
            
            # Pricing info
            pricing = product.get('pricing', {})
            logger.info(f"💰 Price: ${pricing.get('original_price'):.2f} → ${pricing.get('selling_price'):.2f}")
            logger.info(f"📈 Profit: ${pricing.get('profit'):.2f} ({pricing.get('profit_margin', 0)*100:.1f}%)")
            
            # Product features
            if features := product.get('key_features'):
                logger.info("\n🌟 Key Features:")
                for feature in features:
                    logger.info(f"   • {feature}")
            
            logger.info(f"🖼️  Image: {product.get('processed_image')}")
        
        # Show summary
        stats = rebrander.calculate_total_profit(rebranded_products)
        logger.info("\n📊 Summary:")
        logger.info(f"Total Products: {stats['total_products']}")
        logger.info(f"Total Cost: ${stats['total_cost']:.2f}")
        logger.info(f"Total Revenue: ${stats['total_revenue']:.2f}")
        logger.info(f"Total Profit: ${stats['total_profit']:.2f}")
        logger.info(f"Avg. Profit Margin: {stats['average_profit_margin']*100:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("\n🏁 Workflow completed!")

if __name__ == "__main__":
    asyncio.run(main())
