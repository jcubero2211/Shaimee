#!/usr/bin/env python3
"""
Complete Juguetes Rebranding Demo
Shows the full power of the Shaymee rebranding system across different toy categories
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from integrations.product_rebrander import ProductRebrander

# Configure logging
logger.add("complete_juguetes_demo.log", rotation="500 MB", level="INFO")

# Diverse toy mock data representing different categories
TOY_CATEGORIES = {
    "educativo": [
        {
            'title': 'Tablet Educativa Interactiva para Niños 3-7 años',
            'price': '₡28,500',
            'imageUrl': 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=400',
            'productUrl': 'https://demo.com/tablet-educativa'
        },
        {
            'title': 'Microscopio Científico Infantil con Accesorios',
            'price': '₡22,750',
            'imageUrl': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400',
            'productUrl': 'https://demo.com/microscopio-infantil'
        }
    ],
    "construccion": [
        {
            'title': 'Mega Set Bloques Magnéticos 150 Piezas',
            'price': '₡19,200',
            'imageUrl': 'https://images.unsplash.com/photo-1558060370-d644d8d95724?w=400',
            'productUrl': 'https://demo.com/bloques-magneticos'
        },
        {
            'title': 'Kit Constructor Robótica Básica',
            'price': '₡35,000',
            'imageUrl': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400',
            'productUrl': 'https://demo.com/kit-robotica'
        }
    ],
    "vehiculos": [
        {
            'title': 'Drone Cámara HD para Niños Control Remoto',
            'price': '₡42,000',
            'imageUrl': 'https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400',
            'productUrl': 'https://demo.com/drone-camara'
        },
        {
            'title': 'Carro Eléctrico Montable 12V con MP3',
            'price': '₡125,000',
            'imageUrl': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400',
            'productUrl': 'https://demo.com/carro-electrico'
        }
    ],
    "creatividad": [
        {
            'title': 'Set Completo Arte y Manualidades 120 Piezas',
            'price': '₡16,800',
            'imageUrl': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400',
            'productUrl': 'https://demo.com/set-arte'
        },
        {
            'title': 'Mesa Luz Dibujo Profesional A3 LED',
            'price': '₡28,900',
            'imageUrl': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=400',
            'productUrl': 'https://demo.com/mesa-luz'
        }
    ],
    "deportes": [
        {
            'title': 'Canasta Baloncesto Ajustable 1.2m-2.1m',
            'price': '₡18,500',
            'imageUrl': 'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=400',
            'productUrl': 'https://demo.com/canasta-baloncesto'
        },
        {
            'title': 'Set Completo Tenis Mesa Portátil',
            'price': '₡24,000',
            'imageUrl': 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400',
            'productUrl': 'https://demo.com/tenis-mesa'
        }
    ]
}

async def demo_complete_rebranding():
    """Complete demonstration of toy rebranding across categories"""
    load_dotenv()
    
    logger.info("🎪 Starting COMPLETE Shaymee Toy Rebranding Demo")
    logger.info("=" * 70)
    
    # Initialize rebrander
    rebrander = ProductRebrander(
        brand_name="Shaymee",
        target_profit_margin=0.38,  # 38% for premium toys
        shipping_cost=4.50  # Slightly higher for bigger toys
    )
    
    all_rebranded_toys = []
    category_stats = {}
    
    for category, toys in TOY_CATEGORIES.items():
        logger.info(f"\n🎯 Processing category: {category.upper()}")
        logger.info("-" * 50)
        
        try:
            # Rebrand toys in this category
            rebranded_toys = await rebrander.rebrand_products(toys, search_term=category)
            all_rebranded_toys.extend(rebranded_toys)
            
            # Calculate category stats
            total_cost = sum(t.get('pricing', {}).get('original_price', 0) for t in rebranded_toys)
            total_revenue = sum(t.get('pricing', {}).get('selling_price', 0) for t in rebranded_toys)
            total_profit = total_revenue - total_cost
            avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            category_stats[category] = {
                'toys': len(rebranded_toys),
                'cost': total_cost,
                'revenue': total_revenue,
                'profit': total_profit,
                'margin': avg_margin
            }
            
            # Show category results
            logger.success(f"✅ {category.capitalize()}: {len(rebranded_toys)} toys processed")
            for i, toy in enumerate(rebranded_toys, 1):
                pricing = toy.get('pricing', {})
                logger.info(f"  {i}. {toy.get('rebranded_name', 'N/A')}")
                logger.info(f"     Original: {toy.get('title', 'N/A')}")
                logger.info(f"     Price: ₡{pricing.get('original_price', 0):,.0f} → ₡{pricing.get('selling_price', 0):,.0f}")
                logger.info(f"     Profit: ₡{pricing.get('profit', 0):,.0f} ({pricing.get('profit_margin', 0)*100:.1f}%)")
                
                # Show key features
                if features := toy.get('key_features', []):
                    logger.info(f"     Features: {len(features)} destacadas")
                
                processed_image = toy.get('processed_image')
                if processed_image and os.path.exists(processed_image):
                    logger.info(f"     🖼️  Image: ✅ Processed")
                logger.info("")
            
            logger.info(f"📊 Category Summary - {category.capitalize()}:")
            logger.info(f"   💰 Revenue: ₡{total_revenue:,.2f}")
            logger.info(f"   📈 Profit: ₡{total_profit:,.2f} ({avg_margin:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ Error processing {category}: {e}")
    
    # Overall business analysis
    logger.info("\n" + "=" * 70)
    logger.info("📊 SHAYMEE TOY BUSINESS ANALYSIS")
    logger.info("=" * 70)
    
    total_toys = len(all_rebranded_toys)
    overall_cost = sum(category_stats[cat]['cost'] for cat in category_stats)
    overall_revenue = sum(category_stats[cat]['revenue'] for cat in category_stats)
    overall_profit = overall_revenue - overall_cost
    overall_margin = (overall_profit / overall_revenue * 100) if overall_revenue > 0 else 0
    
    logger.info(f"🧸 Total Products: {total_toys}")
    logger.info(f"📂 Categories: {len(category_stats)}")
    logger.info(f"💸 Total Investment: ₡{overall_cost:,.2f}")
    logger.info(f"💰 Total Revenue: ₡{overall_revenue:,.2f}")
    logger.info(f"📈 Total Profit: ₡{overall_profit:,.2f}")
    logger.info(f"🎯 Average Margin: {overall_margin:.1f}%")
    
    logger.info(f"\n📈 CATEGORY PERFORMANCE:")
    for category, stats in category_stats.items():
        logger.info(f"  🎪 {category.capitalize():12} | "
                   f"{stats['toys']:2} toys | "
                   f"₡{stats['profit']:7,.0f} profit | "
                   f"{stats['margin']:5.1f}% margin")
    
    # Best and worst performers
    best_category = max(category_stats.items(), key=lambda x: x[1]['margin'])
    worst_category = min(category_stats.items(), key=lambda x: x[1]['margin'])
    
    logger.info(f"\n🏆 Best Category: {best_category[0].capitalize()} ({best_category[1]['margin']:.1f}% margin)")
    logger.info(f"📉 Focus Area: {worst_category[0].capitalize()} ({worst_category[1]['margin']:.1f}% margin)")
    
    # Check folder organization
    logger.info(f"\n📁 FOLDER STRUCTURE:")
    for category in category_stats.keys():
        processed_dir = f"processed_images/{category}"
        cache_dir = f"image_cache/{category}"
        
        if os.path.exists(processed_dir):
            batches = len([d for d in os.listdir(processed_dir) if os.path.isdir(os.path.join(processed_dir, d))])
            logger.info(f"  📂 {category}: {batches} processing batches")
        
        if os.path.exists(cache_dir):
            cached_files = len([f for f in os.listdir(cache_dir) if f.endswith('.jpg')])
            logger.info(f"  🗂️  {category}: {cached_files} cached images")
    
    logger.success(f"\n🎉 DEMO COMPLETE! Shaymee processed {total_toys} toys across {len(category_stats)} categories")
    logger.info(f"💡 Ready for WhatsApp integration and customer orders!")

if __name__ == "__main__":
    asyncio.run(demo_complete_rebranding())
