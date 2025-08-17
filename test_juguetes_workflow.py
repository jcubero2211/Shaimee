#!/usr/bin/env python3
"""
Test script for Shaymee toy rebranding workflow
Searches for 'juguetes' and processes them through the rebranding pipeline
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from integrations.pequeno_mundo_client_clean import PequenoMundoClient
from integrations.product_rebrander import ProductRebrander

# Configure logging
logger.add("juguetes_workflow.log", rotation="500 MB", level="INFO")

# Mock toy data for testing if scraping fails
MOCK_TOY_DATA = [
    {
        'title': 'Carro de Control Remoto 4x4',
        'price': '₡15,500',
        'imageUrl': 'https://via.placeholder.com/300x300/FF6B6B/FFFFFF?text=Carro+RC',
        'productUrl': 'https://tienda.pequenomundo.com/producto/carro-rc'
    },
    {
        'title': 'Muñeca Princesa con Vestido Brillante',
        'price': '₡8,750',
        'imageUrl': 'https://via.placeholder.com/300x300/4ECDC4/FFFFFF?text=Muñeca',
        'productUrl': 'https://tienda.pequenomundo.com/producto/muneca-princesa'
    },
    {
        'title': 'Set de Bloques de Construcción 500 piezas',
        'price': '₡12,900',
        'imageUrl': 'https://via.placeholder.com/300x300/45B7D1/FFFFFF?text=Bloques',
        'productUrl': 'https://tienda.pequenomundo.com/producto/bloques-construccion'
    },
    {
        'title': 'Pelota de Fútbol Profesional Tamaño 5',
        'price': '₡6,200',
        'imageUrl': 'https://via.placeholder.com/300x300/96CEB4/FFFFFF?text=Pelota',
        'productUrl': 'https://tienda.pequenomundo.com/producto/pelota-futbol'
    },
    {
        'title': 'Robot Educativo Programable',
        'price': '₡25,000',
        'imageUrl': 'https://via.placeholder.com/300x300/FFEAA7/000000?text=Robot',
        'productUrl': 'https://tienda.pequenomundo.com/producto/robot-educativo'
    }
]

async def search_toys_pm():
    """Try to search for toys from Pequeño Mundo"""
    try:
        client = PequenoMundoClient()
        products = await client.get_products('juguetes', limit=10)
        
        if products and len(products) > 0:
            logger.info(f"✅ Successfully scraped {len(products)} toys from Pequeño Mundo")
            return products
        else:
            logger.warning("⚠️ No toys found or scraping failed")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error scraping PM: {e}")
        return None

async def main():
    """Main workflow for processing toys"""
    # Load environment
    load_dotenv()
    
    logger.info("🧸 Starting Shaymee Toy Rebranding Workflow")
    
    # Initialize rebrander
    rebrander = ProductRebrander(
        brand_name=os.getenv("BRAND_NAME", "Shaymee"),
        target_profit_margin=float(os.getenv("TARGET_PROFIT_MARGIN", 0.35)),
        shipping_cost=float(os.getenv("SHIPPING_COST", 3.50))  # Lower shipping for toys
    )
    
    try:
        # Step 1: Try to scrape real toys
        logger.info("🔍 Searching for toys on Pequeño Mundo...")
        products = await search_toys_pm()
        
        # Step 2: Use mock data if scraping fails
        if not products:
            logger.info("📦 Using mock toy data for demonstration")
            products = MOCK_TOY_DATA[:3]  # Use first 3 toys
        
        # Step 3: Rebrand products with search term for organized storage
        logger.info("🎨 Processing toys with AI rebranding...")
        search_term = "juguetes"
        rebranded_toys = await rebrander.rebrand_products(products, search_term=search_term)
        
        # Display results
        logger.success(f"\\n🎉 Toy Rebranding Complete! Processed {len(rebranded_toys)} toys:")
        
        for i, toy in enumerate(rebranded_toys, 1):
            logger.info(f"\\n{'='*70}")
            logger.info(f"🧸 Toy #{i}")
            logger.info(f"📦 Original: {toy.get('title')}")
            logger.info(f"🏷️  Rebranded: {toy.get('rebranded_name')}")
            logger.info(f"💬 Description: {toy.get('description')}")
            
            # Pricing info
            pricing = toy.get('pricing', {})
            logger.info(f"💰 Price: ₡{pricing.get('original_price', 0):,.0f} → ₡{pricing.get('selling_price', 0):,.0f}")
            logger.info(f"📈 Profit: ₡{pricing.get('profit', 0):,.0f} ({pricing.get('profit_margin', 0)*100:.1f}%)")
            logger.info(f"⚖️  Weight Class: {toy.get('weight_class', 'unknown')}")
            
            # Product features
            if features := toy.get('key_features'):
                logger.info("\\n🌟 Key Features:")
                for feature in features:
                    logger.info(f"   • {feature}")
            
            # Image processing info
            processed_image = toy.get('processed_image')
            if processed_image and os.path.exists(processed_image):
                logger.info(f"🖼️  Processed image: {processed_image}")
            else:
                logger.warning(f"⚠️  Image processing may have failed")
        
        # Show summary
        stats = rebrander.calculate_total_profit(rebranded_toys)
        logger.info("\\n📊 Toy Business Summary:")
        logger.info(f"🧸 Total Toys: {stats['total_products']}")
        logger.info(f"💸 Total Cost: ₡{stats['total_cost']:,.2f}")
        logger.info(f"💰 Total Revenue: ₡{stats['total_revenue']:,.2f}")
        logger.info(f"📈 Total Profit: ₡{stats['total_profit']:,.2f}")
        logger.info(f"🎯 Avg. Profit Margin: {stats['average_profit_margin']*100:.1f}%")
        
        # Check folder structure
        logger.info("\\n📁 Checking folder structure...")
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Check processed images
        processed_dir = os.path.join(project_root, 'processed_images', 'juguetes')
        if os.path.exists(processed_dir):
            subdirs = [d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))]
            logger.info(f"📂 Found {len(subdirs)} processing batches in juguetes folder")
            
        # Check image cache
        cache_dir = os.path.join(project_root, 'image_cache', 'juguetes')
        if os.path.exists(cache_dir):
            cached_files = [f for f in os.listdir(cache_dir) if f.endswith('.jpg')]
            logger.info(f"🗂️  Found {len(cached_files)} cached toy images")
        
        logger.success("\\n✅ Toy workflow completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ An error occurred: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
