import asyncio
import random
import time
from typing import Any, Dict, List, Optional
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from undetected_playwright import Malenia

class TemuScraperSmart:
    def __init__(self, timeout: int = 90000):
        self.timeout = timeout
        
        # Realistic user agents
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Smart scraping that mimics real user behavior
        """
        logger.info(f"🧠 Starting smart Temu scraper for: '{search_term}'")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Visible browser for better success
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York',
                    ignore_https_errors=True
                )
                
                # Apply stealth
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                
                # Step 1: Go to homepage first (like a real user)
                logger.info("🏠 Step 1: Going to Temu homepage...")
                await page.goto("https://www.temu.com", timeout=30000)
                await page.wait_for_timeout(random.uniform(3000, 5000))
                
                # Take screenshot of homepage
                await page.screenshot(path='step1_homepage.png')
                logger.info("📸 Homepage screenshot saved")
                
                # Step 2: Look for search box and type search term
                logger.info("🔍 Step 2: Looking for search box...")
                
                # Try different search box selectors
                search_selectors = [
                    'input[type="search"]',
                    'input[placeholder*="search"]',
                    'input[name="q"]',
                    'input[aria-label*="search"]',
                    '.search-input',
                    '#search',
                    '[data-testid="search-input"]'
                ]
                
                search_box = None
                for selector in search_selectors:
                    try:
                        search_box = await page.wait_for_selector(selector, timeout=5000)
                        if search_box:
                            logger.info(f"✅ Found search box with selector: {selector}")
                            break
                    except:
                        continue
                
                if not search_box:
                    logger.warning("⚠️ No search box found, trying to navigate directly...")
                    # Fallback: try direct search URL
                    search_url = f"https://www.temu.com/search_result.html?search_key={search_term.replace(' ', '%20')}"
                    await page.goto(search_url, timeout=30000)
                else:
                    # Clear search box and type search term
                    await search_box.click()
                    await search_box.fill("")
                    await page.wait_for_timeout(500)
                    
                    # Type search term character by character (like a human)
                    for char in search_term:
                        await search_box.type(char)
                        await page.wait_for_timeout(random.uniform(100, 300))
                    
                    await page.wait_for_timeout(1000)
                    
                    # Press Enter or click search button
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(random.uniform(2000, 4000))
                
                # Step 3: Wait for search results and extract products
                logger.info("📦 Step 3: Waiting for search results...")
                
                # Take screenshot of search results
                await page.screenshot(path='step3_search_results.png')
                logger.info("📸 Search results screenshot saved")
                
                # Save HTML for analysis
                html_content = await page.content()
                with open('search_results.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info("💾 HTML content saved: search_results.html")
                
                # Extract products
                products = await self._extract_products_smart(page, limit)
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"💥 Smart scraping failed: {e}")
            return None

    async def _extract_products_smart(self, page, limit: int) -> List[Dict[str, Any]]:
        """Smart product extraction with multiple strategies"""
        products = []
        
        # Strategy 1: Look for product cards
        logger.info("🔍 Strategy 1: Looking for product cards...")
        
        # Common product selectors
        selectors = [
            '.product-item',
            '.item',
            '[data-product-id]',
            '.product-card',
            '.search-result-item',
            '.product',
            'div[class*="product"]',
            'div[class*="item"]'
        ]
        
        for selector in selectors:
            try:
                # Wait a bit for elements to load
                await page.wait_for_timeout(2000)
                
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements[:limit]:
                        try:
                            product = await self._extract_product_info(element)
                            if product and product not in products:
                                products.append(product)
                                if len(products) >= limit:
                                    break
                        except Exception as e:
                            logger.debug(f"⚠️ Error extracting product: {e}")
                            continue
                    
                    if products:
                        break
                        
            except Exception as e:
                logger.debug(f"⚠️ Selector {selector} failed: {e}")
                continue
        
        # Strategy 2: Look for any links that might be products
        if not products:
            logger.info("🔄 Strategy 2: Looking for product links...")
            try:
                links = await page.query_selector_all('a[href*="/product/"]')
                logger.info(f"🔗 Found {len(links)} product links")
                
                for link in links[:limit]:
                    try:
                        href = await link.get_attribute('href')
                        title = await link.inner_text()
                        
                        if href and title.strip():
                            if href.startswith('/'):
                                href = f"https://www.temu.com{href}"
                            
                            products.append({
                                'title': title.strip(),
                                'price': 'Price not available',
                                'imageUrl': 'Image not available',
                                'productUrl': href
                            })
                            
                            if len(products) >= limit:
                                break
                                
                    except Exception as e:
                        logger.debug(f"⚠️ Error processing link: {e}")
                        continue
        
            except Exception as e:
                logger.debug(f"⚠️ Link strategy failed: {e}")
        
        # Strategy 3: Look for any text that might be product titles
        if not products:
            logger.info("🔄 Strategy 3: Looking for product titles in text...")
            try:
                # Get all text content and look for patterns
                page_text = await page.inner_text('body')
                
                # Look for lines that might be product titles
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if len(line) > 10 and len(line) < 100:  # Reasonable title length
                        if any(keyword in line.lower() for keyword in ['case', 'phone', 'cover', 'protector']):
                            products.append({
                                'title': line,
                                'price': 'Price not available',
                                'imageUrl': 'Image not available',
                                'productUrl': 'https://www.temu.com'
                            })
                            
                            if len(products) >= limit:
                                break
                                
            except Exception as e:
                logger.debug(f"⚠️ Text strategy failed: {e}")
        
        logger.info(f"📊 Total products found: {len(products)}")
        return products

    async def _extract_product_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract product information from an element"""
        try:
            # Extract title
            title = 'N/A'
            title_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '.title', '.name', '.product-title',
                'p', 'span', 'div'
            ]
            
            for sel in title_selectors:
                try:
                    title_elem = await element.query_selector(sel)
                    if title_elem:
                        text = await title_elem.inner_text()
                        if text and len(text.strip()) > 3:
                            title = text.strip()
                            break
                except:
                    continue
            
            # Extract price
            price = 'N/A'
            price_selectors = [
                '.price', '.cost', '.amount',
                '[data-price]', '[class*="price"]'
            ]
            
            for sel in price_selectors:
                try:
                    price_elem = await element.query_selector(sel)
                    if price_elem:
                        text = await price_elem.inner_text()
                        if text and any(char.isdigit() for char in text):
                            price = text.strip()
                            break
                except:
                    continue
            
            # Extract image
            image_url = 'N/A'
            try:
                img_elem = await element.query_selector('img')
                if img_elem:
                    image_url = await img_elem.get_attribute('src')
                    if not image_url:
                        image_url = await img_elem.get_attribute('data-src')
            except:
                pass
            
            # Extract URL
            product_url = '#'
            try:
                link_elem = await element.query_selector('a')
                if link_elem:
                    product_url = await link_elem.get_attribute('href')
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.temu.com{product_url}"
            except:
                pass
            
            # Only return valid products
            if title != 'N/A' and title.strip():
                return {
                    'title': title,
                    'price': price,
                    'imageUrl': image_url,
                    'productUrl': product_url
                }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting product info: {e}")
        
        return None

# Test function
async def test_smart_scraper():
    """Test the smart Temu scraper"""
    logger.info("🧪 Testing Smart Temu Scraper...")
    
    scraper = TemuScraperSmart()
    products = await scraper.get_products("phone case", limit=5)
    
    if products:
        print(f"✅ Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['title']}")
            print(f"   Price: {product['price']}")
            print(f"   URL: {product['productUrl']}")
            print(f"   Image: {product['imageUrl']}")
            print()
    else:
        print("❌ No products found")
        
    print("📸 Check the generated screenshots and HTML files for debugging")

if __name__ == "__main__":
    asyncio.run(test_smart_scraper())
