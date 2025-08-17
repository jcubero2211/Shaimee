#!/usr/bin/env python3
"""
Playwright scraper that can handle Cloudflare challenges
This mimics a real browser and can solve JavaScript challenges
"""

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def scrape_pequeno_mundo_with_playwright(search_term="juguetes"):
    """Scrape Pequeño Mundo using Playwright (real browser)"""
    
    print(f"🎭 PLAYWRIGHT SCRAPING: {search_term}")
    print("="*50)
    
    async with async_playwright() as p:
        # Launch browser with realistic settings
        browser = await p.chromium.launch(
            headless=True,  # Set to False to see the browser
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='es-CR',
            timezone_id='America/Costa_Rica',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # Set additional headers
        await page.set_extra_http_headers({
            'Accept-Language': 'es-CR,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        })
        
        try:
            search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term}"
            print(f"📡 Navigating to: {search_url}")
            
            # Navigate to the search page
            response = await page.goto(search_url, wait_until='networkidle', timeout=30000)
            print(f"📊 Response status: {response.status}")
            
            # Wait a bit for any JavaScript to execute
            await page.wait_for_timeout(3000)
            
            # Check if we hit a Cloudflare challenge
            title = await page.title()
            print(f"📝 Page title: {title}")
            
            if "Just a moment" in title or "checking your browser" in await page.content():
                print("⚠️  Cloudflare challenge detected - waiting for it to resolve...")
                
                # Wait for the challenge to complete (up to 15 seconds)
                try:
                    await page.wait_for_url("**/catalogsearch/result/**", timeout=15000)
                    print("✅ Challenge completed successfully!")
                except:
                    print("⏰ Challenge taking longer than expected...")
                    # Continue anyway, might still work
            
            # Get the final page content
            content = await page.content()
            print(f"📄 Final content length: {len(content)} chars")
            
            # Save for debugging
            with open(f'playwright_{search_term}.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for products
            products = []
            product_containers = soup.select('.product-item')
            
            if product_containers:
                print(f"🎉 Found {len(product_containers)} product containers!")
                
                for i, container in enumerate(product_containers[:5], 1):
                    try:
                        # Extract product details
                        title_elem = (container.select_one('.product-name a') or 
                                    container.select_one('.product-item-name a') or
                                    container.select_one('a[title]') or
                                    container.find('a'))
                        
                        title = title_elem.text.strip() if title_elem else "No title"
                        product_url = title_elem.get('href') if title_elem else ""
                        
                        # Fix relative URLs
                        if product_url and product_url.startswith('/'):
                            product_url = f"https://tienda.pequenomundo.com{product_url}"
                        
                        # Price
                        price_elem = container.select_one('.price')
                        price = price_elem.text.strip() if price_elem else "No price"
                        
                        # Image
                        img_elem = container.find('img')
                        image_url = ""
                        if img_elem:
                            image_url = img_elem.get('src') or img_elem.get('data-src') or ""
                            if image_url and image_url.startswith('/'):
                                image_url = f"https://tienda.pequenomundo.com{image_url}"
                        
                        product_data = {
                            'title': title,
                            'price': price,
                            'imageUrl': image_url,
                            'productUrl': product_url
                        }
                        
                        products.append(product_data)
                        print(f"{i}. 📦 {title}")
                        print(f"   💰 {price}")
                        print(f"   🔗 {product_url[:50]}...")
                        print()
                        
                    except Exception as e:
                        print(f"⚠️  Error extracting product {i}: {e}")
                        continue
            
            else:
                print("😞 No product containers found")
                
                # Check for specific messages
                if "sin resultados" in content.lower() or "no results" in content.lower():
                    print(f"📭 No results found for '{search_term}'")
                elif "tienda.pequenomundo.com" in content:
                    print("🤔 Got site content but no products - might be page structure issue")
                else:
                    print("❌ Still blocked or redirected")
            
            # Take a screenshot for debugging
            await page.screenshot(path=f'playwright_{search_term}.png', full_page=True)
            print(f"📸 Screenshot saved: playwright_{search_term}.png")
            
            return products
            
        except Exception as e:
            print(f"💥 Error during scraping: {e}")
            
            # Take screenshot of error state
            try:
                await page.screenshot(path=f'playwright_error_{search_term}.png', full_page=True)
                print(f"📸 Error screenshot: playwright_error_{search_term}.png")
            except:
                pass
                
            return []
            
        finally:
            await browser.close()

async def main():
    """Test Playwright scraping"""
    
    search_terms = ["juguetes", "reloj"]
    
    for term in search_terms:
        print(f"\\n🔍 Testing search term: '{term}'")
        print("-" * 40)
        
        products = await scrape_pequeno_mundo_with_playwright(term)
        
        if products:
            print(f"✅ SUCCESS! Found {len(products)} products for '{term}'")
            
            # Save results
            with open(f'scraped_products_{term}.json', 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved to: scraped_products_{term}.json")
            
        else:
            print(f"😞 No products found for '{term}'")
        
        # Small delay between searches
        await asyncio.sleep(3)
    
    print(f"\\n🎯 SUMMARY:")
    print("✅ Playwright can handle JavaScript challenges")
    print("📁 Check generated files: playwright_*.html, *.png, *.json")
    print("🚀 If this works, we can integrate it into the rebranding pipeline!")

if __name__ == "__main__":
    asyncio.run(main())
