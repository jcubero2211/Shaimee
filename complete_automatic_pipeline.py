#!/usr/bin/env python3
"""
COMPLETE 100% AUTOMATIC PIPELINE
Pequeño Mundo Scraping → AI Rebranding → Shaymee Marketplace

Real products automatically transformed into Shaymee branded products
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add integrations to path
sys.path.append('integrations')

# Import our custom modules
from stealth_scraper import StealthScraper
from product_rebrander import ProductRebrander

class AutomaticPipeline:
    def __init__(self):
        self.scraper = StealthScraper()
        self.rebrander = None  # Will initialize if API key available
        
    async def run_complete_pipeline(self):
        """Run the complete automatic pipeline"""
        
        print("🚀 SHAYMEE COMPLETE AUTOMATIC PIPELINE")
        print("="*60)
        print("📦 Pequeño Mundo → AI Rebranding → Shaymee Marketplace")
        print("="*60)
        
        # Step 1: Scrape real products
        print("\n🥷 STEP 1: SCRAPING REAL PRODUCTS")
        print("-" * 40)
        
        scraped_products = await self._scrape_products()
        
        if not scraped_products:
            print("❌ No products scraped - pipeline cannot continue")
            return
        
        print(f"✅ Successfully scraped {len(scraped_products)} real products!")
        
        # Step 2: AI Rebranding (if API key available)
        print("\n🎨 STEP 2: AI REBRANDING WITH SHAYMEE BRANDING")
        print("-" * 40)
        
        rebranded_products = await self._rebrand_products(scraped_products)
        
        # Step 3: Generate marketplace data
        print("\n🏪 STEP 3: SHAYMEE MARKETPLACE READY")
        print("-" * 40)
        
        await self._generate_marketplace_data(rebranded_products)
        
        # Step 4: Business analytics
        print("\n📊 STEP 4: BUSINESS ANALYTICS")
        print("-" * 40)
        
        self._generate_business_analytics(rebranded_products)
        
        print(f"\n🎉 PIPELINE COMPLETE!")
        print(f"📱 Ready for WhatsApp integration")
        print(f"🛒 Ready for customer orders")
        
    async def _scrape_products(self):
        """Scrape products from Pequeño Mundo"""
        
        # Focus on profitable categories
        search_terms = [
            "juguetes",      # Toys - high margin potential
            "reloj",         # Watches - good profit margins  
            "electronico",   # Electronics - popular category
            "casa",          # Home goods - steady demand
            "cocina"         # Kitchen - practical items
        ]
        
        all_products = []
        
        for term in search_terms:
            print(f"🔍 Scraping: '{term}'...")
            
            products = await self.scraper.bypass_cloudflare_and_scrape(term)
            
            if products:
                print(f"  ✅ Found {len(products)} products")
                all_products.extend(products)
            else:
                print(f"  😞 No products found")
            
            # Human-like delay
            await asyncio.sleep(3)
        
        return all_products
    
    async def _rebrand_products(self, scraped_products):
        """Rebrand products with AI or use mock rebranding"""
        
        try:
            # Try to initialize rebrander with API key
            self.rebrander = ProductRebrander()
            print("🤖 Using AI rebranding with OpenAI")
        except:
            print("⚠️  OpenAI API key not available - using mock rebranding")
            return self._mock_rebrand_products(scraped_products)
        
        rebranded_products = []
        
        for i, product in enumerate(scraped_products[:10], 1):  # Limit to 10 for demo
            print(f"🎨 Rebranding {i}/{min(10, len(scraped_products))}: {product['title'][:30]}...")
            
            try:
                rebranded = await self.rebrander.rebrand_product(
                    title=product['title'],
                    price=product['price'],
                    image_url=product['imageUrl'],
                    product_url=product['productUrl'],
                    original_source="Pequeño Mundo (Costa Rica)"
                )
                
                if rebranded:
                    rebranded_products.append(rebranded)
                    print(f"  ✅ Rebranded: {rebranded['title'][:40]}...")
                else:
                    print(f"  ❌ Failed to rebrand")
                    
            except Exception as e:
                print(f"  💥 Error: {e}")
                continue
        
        return rebranded_products
    
    def _mock_rebrand_products(self, scraped_products):
        """Mock rebranding for demonstration"""
        
        print("🎭 Using mock AI rebranding (for demo)")
        
        rebranded_products = []
        
        for i, product in enumerate(scraped_products[:10], 1):
            # Convert Costa Rican colones to USD (approximate)
            price_text = product['price'].replace('₡', '').replace(',', '').replace(' ', '')
            try:
                price_crc = float(price_text.split('.')[0])  # Get integer part
                price_usd = price_crc / 500  # Rough conversion rate
                shaymee_price = price_usd * 1.4  # 40% markup
            except:
                price_usd = 10.0
                shaymee_price = 14.0
            
            # Mock rebranded product
            mock_rebranded = {
                'title': f"Shaymee {product['title'][:50]}",
                'price': f"${shaymee_price:.2f}",
                'original_price': product['price'],
                'margin': '40',
                'imageUrl': product['imageUrl'],
                'productUrl': product['productUrl'],
                'shaymee_description': f"Premium quality {product['title'].lower()} - Curated by Shaymee for exceptional value and style.",
                'category': product['searchTerm'],
                'source': product['source'],
                'brand': 'Shaymee',
                'whatsapp_ready': True
            }
            
            rebranded_products.append(mock_rebranded)
            print(f"  ✅ {i}. Mock rebranded: {mock_rebranded['title'][:40]}... - {mock_rebranded['price']}")
        
        return rebranded_products
    
    async def _generate_marketplace_data(self, rebranded_products):
        """Generate marketplace-ready data"""
        
        if not rebranded_products:
            print("😞 No rebranded products to process")
            return
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Group by category
        by_category = {}
        for product in rebranded_products:
            category = product.get('category', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(product)
        
        print(f"📦 Marketplace catalog generated:")
        for category, products in by_category.items():
            print(f"   📂 {category}: {len(products)} products")
        
        # Save marketplace catalog
        catalog_file = f'shaymee_catalog_{timestamp}.json'
        with open(catalog_file, 'w', encoding='utf-8') as f:
            json.dump(rebranded_products, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Catalog saved: {catalog_file}")
        
        # Generate WhatsApp-ready messages
        whatsapp_messages = []
        for product in rebranded_products[:5]:  # First 5 products
            message = f"""🛍️ *{product['title']}*
            
💰 Precio: {product['price']}
📦 Categoría: {product.get('category', 'General').title()}
✨ {product.get('shaymee_description', 'Producto premium de Shaymee')}

📱 ¡Ordena ahora por WhatsApp!"""
            
            whatsapp_messages.append(message)
        
        # Save WhatsApp messages
        whatsapp_file = f'whatsapp_messages_{timestamp}.txt'
        with open(whatsapp_file, 'w', encoding='utf-8') as f:
            f.write('\n\n' + '='*50 + '\n\n'.join(whatsapp_messages))
        
        print(f"📱 WhatsApp messages: {whatsapp_file}")
    
    def _generate_business_analytics(self, rebranded_products):
        """Generate business analytics and insights"""
        
        if not rebranded_products:
            print("📊 No products for analytics")
            return
        
        # Calculate metrics
        total_products = len(rebranded_products)
        
        # Margins
        margins = []
        for product in rebranded_products:
            try:
                margin = float(product.get('margin', '0'))
                margins.append(margin)
            except:
                continue
        
        avg_margin = sum(margins) / len(margins) if margins else 0
        
        # Prices
        prices = []
        for product in rebranded_products:
            try:
                price_str = product.get('price', '$0').replace('$', '')
                price = float(price_str)
                prices.append(price)
            except:
                continue
        
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Categories
        categories = {}
        for product in rebranded_products:
            cat = product.get('category', 'general')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"💼 SHAYMEE BUSINESS ANALYTICS")
        print(f"   📊 Total products ready: {total_products}")
        print(f"   📈 Average margin: {avg_margin:.1f}%")
        print(f"   💰 Average price: ${avg_price:.2f}")
        print(f"   📂 Categories:")
        for cat, count in categories.items():
            print(f"      - {cat}: {count} products")
        
        # Revenue projection
        if prices:
            daily_orders = 5  # Conservative estimate
            monthly_revenue = sum(prices) * daily_orders * 30 / len(prices)
            print(f"   💵 Monthly revenue potential: ${monthly_revenue:.2f}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. ✅ Products scraped and rebranded")
        print(f"   2. ✅ Catalog and WhatsApp messages ready") 
        print(f"   3. 🔄 Deploy to WhatsApp Business API")
        print(f"   4. 📈 Start marketing and taking orders")
        print(f"   5. 🔄 Scale scraping to more categories")

async def main():
    """Run the complete automatic pipeline"""
    
    pipeline = AutomaticPipeline()
    await pipeline.run_complete_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
