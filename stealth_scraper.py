#!/usr/bin/env python3
"""
Stealth Playwright scraper with advanced Cloudflare bypass
100% automatic product scraping from Pequeño Mundo
"""

import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import time

class StealthScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
    
    async def bypass_cloudflare_and_scrape(self, search_term: str = "juguetes"):
        """Advanced Cloudflare bypass with stealth techniques"""
        
        print(f"🥷 STEALTH SCRAPING: {search_term}")
        print("="*50)
        
        async with async_playwright() as p:
            # Launch with stealth settings
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
                    '--disable-blink-features=AutomationControlled',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    '--enable-features=NetworkService,NetworkServiceLogging',
                    '--disable-features=TranslateUI,VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins'
                ]
            )
            
            # Create stealth context
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                locale='es-CR',
                timezone_id='America/Costa_Rica',
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
                ignore_https_errors=True,
                java_script_enabled=True
            )
            
            # Add stealth headers
            await context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-CR,es;q=0.9,es-419;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
                'Upgrade-Insecure-Requests': '1'
            })
            
            page = await context.new_page()
            
            # Add stealth JavaScript injection
            await page.add_init_script("""
                // Stealth mode: hide automation indicators
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['es-CR', 'es', 'en']});
                window.chrome = {runtime: {}};
                
                // Mock human-like behavior
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({state: Deniedpub}) :
                    originalQuery(parameters)
                );
            """)
            
            try:
                # Step 1: Visit homepage first (like a real user)
                print("🏠 Step 1: Visiting homepage...")
                await page.goto('https://tienda.pequenomundo.com/', 
                              wait_until='domcontentloaded', timeout=15000)
                
                # Random human delay
                await page.wait_for_timeout(random.randint(1000, 3000))
                
                # Check if homepage loaded
                home_title = await page.title()
                print(f"🏠 Homepage title: {home_title}")
                
                if "Just a moment" in home_title:
                    print("⚠️  Cloudflare challenge on homepage - waiting...")
                    await self._handle_cloudflare_challenge(page)
                
                # Step 2: Simulate human navigation to search
                print(f"🔍 Step 2: Searching for '{search_term}'...")
                
                # Try to find and use the search box (more human-like)
                search_box = await page.query_selector('input[name="q"], .search-field input, #search')
                
                if search_box:
                    print("🔍 Found search box - typing like human...")
                    await search_box.click()
                    await page.wait_for_timeout(random.randint(500, 1000))
                    
                    # Type with human-like delays
                    for char in search_term:
                        await search_box.type(char)
                        await page.wait_for_timeout(random.randint(50, 150))
                    
                    # Submit search
                    await page.keyboard.press('Enter')
                    
                else:
                    print("🔍 No search box found - using direct URL...")
                    search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term}"
                    await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                
                # Wait for search results
                await page.wait_for_timeout(random.randint(2000, 4000))
                
                # Check for Cloudflare challenge on search page
                search_title = await page.title()
                print(f"📝 Search page title: {search_title}")
                
                if "Just a moment" in search_title:
                    print("⚠️  Cloudflare challenge on search page - handling...")
                    success = await self._handle_cloudflare_challenge(page)
                    if not success:
                        print("❌ Failed to bypass Cloudflare challenge")
                        return []
                
                # Take screenshot for debugging
                await page.screenshot(path=f'stealth_{search_term}_final.png', full_page=True)
                
                # Extract products
                return await self._extract_products_from_page(page, search_term)
                
            except Exception as e:
                print(f"💥 Error during stealth scraping: {e}")
                await page.screenshot(path=f'stealth_error_{search_term}.png', full_page=True)
                return []
            
            finally:
                await browser.close()
    
    async def _handle_cloudflare_challenge(self, page, max_wait=30):
        """Handle Cloudflare challenge with patience"""
        
        print("🛡️  Handling Cloudflare challenge...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check current page state
                title = await page.title()
                content = await page.content()
                
                if "Just a moment" not in title and "checking your browser" not in content:
                    print("✅ Challenge completed!")
                    return True
                
                # Wait and check again
                print(f"⏳ Still waiting... ({int(time.time() - start_time)}s)")
                await page.wait_for_timeout(2000)
                
                # Sometimes clicking helps
                try:
                    await page.click('body')
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️  Challenge handling error: {e}")
                continue
        
        print("❌ Challenge timeout - proceeding anyway")
        return False
    
    async def _extract_products_from_page(self, page, search_term):
        """Extract product data from the current page"""
        
        print("📦 Extracting products from page...")
        
        try:
            content = await page.content()
            
            # Save HTML for debugging
            with open(f'stealth_{search_term}_content.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Multiple product selectors to try
            selectors = [
                '.product-item',
                '.item.product',
                '.product-item-info',
                '.catalog-product-item',
                '[data-product-id]'
            ]
            
            products = []
            
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    print(f"🎯 Found {len(containers)} products with selector: {selector}")
                    
                    for i, container in enumerate(containers[:10], 1):  # Limit to 10 products
                        try:
                            # Title
                            title_selectors = [
                                '.product-name a',
                                '.product-item-name a',
                                '.product-title a',
                                'a[title]'
                            ]
                            
                            title = ""
                            product_url = ""
                            
                            for t_sel in title_selectors:
                                elem = container.select_one(t_sel)
                                if elem:
                                    title = elem.text.strip()
                                    product_url = elem.get('href', '')
                                    break
                            
                            if not title:
                                # Fallback to any link
                                link = container.find('a')
                                if link:
                                    title = link.text.strip()
                                    product_url = link.get('href', '')
                            
                            # Price
                            price_selectors = ['.price', '.regular-price', '.price-final', '.special-price']
                            price = ""
                            
                            for p_sel in price_selectors:
                                elem = container.select_one(p_sel)
                                if elem:
                                    price = elem.text.strip()
                                    break
                            
                            # Image
                            img = container.find('img')
                            image_url = ""
                            if img:
                                image_url = img.get('src') or img.get('data-src') or ""
                            
                            # Fix relative URLs
                            if product_url and product_url.startswith('/'):
                                product_url = f"https://tienda.pequenomundo.com{product_url}"
                            if image_url and image_url.startswith('/'):
                                image_url = f"https://tienda.pequenomundo.com{image_url}"
                            
                            if title and title != "":
                                product_data = {
                                    'title': title,
                                    'price': price or 'No price',
                                    'imageUrl': image_url,
                                    'productUrl': product_url,
                                    'source': 'Pequeño Mundo',
                                    'searchTerm': search_term
                                }
                                
                                products.append(product_data)
                                print(f"✅ {i}. {title[:50]}... - {price}")
                        
                        except Exception as e:
                            print(f"⚠️  Error extracting product {i}: {e}")
                            continue
                    
                    break  # Stop after first successful selector
            
            if not products:
                print("😞 No products found - checking for error messages...")
                
                if "sin resultados" in content.lower() or "no results" in content.lower():
                    print(f"📭 No results found for '{search_term}'")
                elif "tienda.pequenomundo.com" in content.lower():
                    print("🤔 Got site content but couldn't find products")
                else:
                    print("❌ Still blocked or unknown page structure")
            
            return products
            
        except Exception as e:
            print(f"💥 Error extracting products: {e}")
            return []

async def main():
    """Run stealth scraping for multiple search terms"""
    
    print("🥷 100% AUTOMATIC STEALTH SCRAPING")
    print("="*50)
    
    scraper = StealthScraper()
    search_terms = ["juguetes", "reloj", "hogar", "cocina"]
    
    all_products = []
    
    for term in search_terms:
        print(f"\n🎯 Scraping: '{term}'")
        print("-" * 30)
        
        products = await scraper.bypass_cloudflare_and_scrape(term)
        
        if products:
            print(f"✅ SUCCESS! Found {len(products)} products for '{term}'")
            all_products.extend(products)
            
            # Save individual results
            with open(f'stealth_products_{term}.json', 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
        else:
            print(f"😞 No products found for '{term}'")
        
        # Human-like delay between searches
        delay = random.randint(5, 10)
        print(f"⏳ Waiting {delay}s before next search...")
        await asyncio.sleep(delay)
    
    # Save all results
    if all_products:
        with open('all_scraped_products.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 TOTAL SUCCESS: {len(all_products)} products scraped!")
        print(f"📁 Saved to: all_scraped_products.json")
        print(f"🚀 Ready for AI rebranding pipeline!")
    else:
        print(f"\n😞 No products scraped from any search terms")
        print(f"🔍 Check debug files: stealth_*.html, *.png")

if __name__ == "__main__":
    asyncio.run(main())
