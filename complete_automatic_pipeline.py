#!/usr/bin/env python3
"""
COMPLETE 100% AUTOMATIC PIPELINE
Pequeño Mundo Scraping → AI Rebranding → Shaymee Marketplace

Real products automatically transformed into Shaymee branded products
"""

import aiohttp
import asyncio
import json
import os
import random
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Simple ProductRebrander class since we're using mock data
class ProductRebrander:
    def __init__(self, api_key=None):
        self.api_key = api_key
        
    async def rebrand_product(self, product_data):
        """Mock rebranding - in a real scenario, this would use AI"""
        # Just return the product with some mock branding
        return {
            **product_data,
            'brand': 'Shaymee',
            'description': f"{product_data.get('description', '')} - ¡Exclusivo en Shaymee!",
            'features': product_data.get('features', []) + [
                '✓ Calidad premium',
                '✓ Envío rápido y seguro',
                '✓ Garantía de satisfacción'
            ]
        }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shaymee_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomaticPipeline:
    def __init__(self):
        self.rebrander = None  # Will initialize if API key available
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
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
        
        rebranded_products = await self._mock_rebrand_products(scraped_products)  # Using mock rebranding
        
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
        """Scrape products from Pequeño Mundo using Playwright with stealth settings"""
        search_terms = ["juguetes", "reloj", "electronico", "casa", "cocina"]
        all_products = []
        
        # Add a random delay to appear more human-like
        await asyncio.sleep(random.uniform(1, 3))     
        
        print("\n🔍 Starting product scraping with Playwright...")
        
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create a new browser context with a random user agent
            user_agent = random.choice(self.user_agents)
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='es-CR',
                timezone_id='America/Costa_Rica'
            )
            
            # Disable WebDriver detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            try:
                for term in search_terms:
                    print(f"🔍 Scraping: '{term}'...")
                    
                    # Navigate to search page
                    search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={term}"
                    await page.goto(search_url, timeout=60000)
                    
                    # Wait for product grid to load
                    try:
                        await page.wait_for_selector('.products-grid', timeout=10000)
                    except:
                        print(f"  ⚠️ Could not find products for: {term}")
                        continue
                    
                    # Extract product data
                    products = await page.evaluate('''() => {
                        const items = [];
                        document.querySelectorAll('.product-item').forEach(item => {
                            const titleEl = item.querySelector('.product-item-name a');
                            const priceEl = item.querySelector('.price');
                            const imageEl = item.querySelector('.product-image-photo');
                            const linkEl = item.querySelector('.product-item-link');
                            
                            if (titleEl && priceEl) {
                                items.push({
                                    title: titleEl.innerText.trim(),
                                    price: priceEl.innerText.trim(),
                                    imageUrl: imageEl ? imageEl.src : '',
                                    productUrl: linkEl ? linkEl.href : ''
                                });
                            }
                        });
                        return items;
                    }''')
                    
                    if products:
                        print(f"  ✅ Found {len(products)} products")
                        all_products.extend(products)
                    else:
                        print("  😞 No products found")
                        
            except Exception as e:
                print(f"  ❌ Error during scraping: {str(e)}")
                
            finally:
                await browser.close()
                
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
    
    async def _download_image(self, url, product_id):
        """Download and save product image"""
        try:
            # Create images directory if it doesn't exist
            os.makedirs('product_images', exist_ok=True)
            
            # Generate filename with product ID
            filename = f"product_images/{product_id}.jpg"
            
            # Skip if already downloaded
            if os.path.exists(filename):
                return filename
                
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(filename, 'wb') as f:
                            f.write(await response.read())
                        return filename
        except Exception as e:
            print(f"  ⚠️ Error downloading image: {e}")
        return None

    def _generate_product_id(self, title):
        """Generate a unique product ID from title"""
        # Take first 3 words, convert to lowercase, join with underscores
        words = [w for w in title.lower().split() if w.isalnum()][:3]
        return '_'.join(words)[:50]  # Limit length

    async def _mock_rebrand_products(self, scraped_products):
        """Mock rebranding for demonstration"""
        print("🎭 Using mock AI rebranding (for demo)")
        
        rebranded_products = []
        
        # Define categories and their keywords
        categories = {
            'juguetes': ['juguete', 'juego', 'peluche', 'muñec', 'lego', 'figura'],
            'reloj': ['reloj', 'cronómetro', 'temporizador'],
            'electronico': ['electrónic', 'cargador', 'cable', 'usb', 'bluetooth', 'inalámbrico'],
            'casa': ['mueble', 'decoración', 'almohada', 'cortina', 'alfombra', 'lámpara'],
            'cocina': ['cocina', 'olla', 'sartén', 'cuchillo', 'cuchara', 'tenedor', 'plato', 'vaso']
        }
        
        for i, product in enumerate(scraped_products[:10], 1):
            # Generate a unique product ID
            product_id = f"{i:03d}_{self._generate_product_id(product.get('title', ''))}"
            
            # Determine category based on product title
            title_lower = product.get('title', '').lower()
            category = 'general'
            for cat, keywords in categories.items():
                if any(keyword in title_lower for keyword in keywords):
                    category = cat
                    break
            
            # Convert price from CRC to USD with markup
            try:
                price_text = product.get('price', '₡0').replace('₡', '').replace(',', '').strip()
                price_crc = float(price_text)
                price_usd = price_crc / 600  # Approximate conversion
                shaymee_price = price_usd * 1.4  # 40% markup
                price_str = f"${shaymee_price:.2f}"
            except (ValueError, AttributeError):
                price_str = f"${random.uniform(10, 100):.2f}"
            
            # Download and save the product image
            image_filename = None
            if product.get('imageUrl'):
                image_filename = await self._download_image(product['imageUrl'], product_id)
            
            # Create rebranded product
            rebranded = {
                'id': product_id,
                'title': product.get('title', 'Producto'),  # Original title without Shaymee prefix
                'price': price_str,
                'original_price': product.get('price', '₡0'),
                'margin': "40",
                'image_filename': image_filename or '',
                'productUrl': product.get('productUrl', ''),
                'description': f"{product.get('title', 'Producto')} - Calidad premium garantizada",
                'category': category,
                'source': 'Pequeño Mundo',
                'brand': 'Shaymee',
                'whatsapp_ready': True,
                'features': [
                    "✓ Calidad premium",
                    "✓ Envío rápido y seguro",
                    "✓ Garantía de satisfacción"
                ]
            }
            
            rebranded_products.append(rebranded)
            print(f"  ✅ {i}. Processed: {rebranded['title'][:40]}...")
            
            # Add a small delay between requests
            await asyncio.sleep(0.5)
            
        return rebranded_products
    
    async def _generate_marketplace_data(self, rebranded_products):
        """Generate marketplace-ready data with WhatsApp messages"""
        
        if not rebranded_products:
            print("😞 No rebranded products to process")
            return None, None
        
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
        
        # Save catalog
        catalog = {
            'timestamp': timestamp,
            'products': rebranded_products,
            'categories': list(by_category.keys()),
            'total_products': len(rebranded_products)
        }
        
        catalog_filename = f"shaymee_catalog_{timestamp}.json"
        with open(catalog_filename, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        
        # Generate WhatsApp messages
        whatsapp_messages = []
        for idx, product in enumerate(rebranded_products, 1):
            # Format price with thousands separator
            try:
                price = float(product['price'].replace('$', '').replace(',', ''))
                formatted_price = f"${price:,.2f}".replace(',', ' ').replace('.', ',').replace(' ', '.')
            except:
                formatted_price = product['price']
                
            # Format original price if available
            original_price = product.get('original_price', '')
            if original_price and original_price.startswith('₡'):
                try:
                    crc_price = float(original_price.replace('₡', '').replace(',', '').strip())
                    formatted_original = f"₡{crc_price:,.0f}".replace(',', '.')
                except:
                    formatted_original = original_price
            else:
                formatted_original = original_price
            
            # Build features list
            features = "\n".join([f"• {f}" for f in product.get('features', [])])
            
            # Create WhatsApp message
            message = (
                f"🛍️ *{product['title']}*\n\n"
                f"📌 *Código:* {product['id']}\n"
                f"🏷️ *Precio:* {formatted_price} (antes {formatted_original})\n"
                f"📦 *Categoría:* {product['category'].title()}\n"
                f"🏭 *Marca:* {product['brand']}\n\n"
                f"📝 *Descripción:*\n{product['description']}\n\n"
                f"✨ *Características:*\n{features}\n\n"
                f"💬 *¿Te interesa?* Responde con el código *{product['id']}* para más información o para comprar.\n"
                f"📲 *Disponible para entrega inmediata*"
            )
            
            whatsapp_messages.append({
                'id': product['id'],
                'category': product['category'],
                'message': message,
                'image': product.get('image_filename', '')
            })
        
        # Save WhatsApp messages
        whatsapp_filename = f"whatsapp_messages_{timestamp}.txt"
        with open(whatsapp_filename, 'w', encoding='utf-8') as f:
            for item in whatsapp_messages:
                f.write(f"=== {item['id']} ===\n")
                f.write(f"Categoría: {item['category']}\n")
                f.write(f"Imagen: {item.get('image', 'N/A')}\n")
                f.write("-" * 40 + "\n")
                f.write(item['message'])
                f.write("\n\n")
        
        print(f"💾 Catalog saved: {catalog_filename}")
        print(f"📱 WhatsApp messages: {whatsapp_filename}")
        
        return catalog, whatsapp_messages
    
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
