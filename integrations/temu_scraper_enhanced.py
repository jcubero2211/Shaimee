import asyncio
import random
import time
from typing import Any, Dict, List, Optional
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from undetected_playwright import Malenia

class TemuScraperEnhanced:
    def __init__(self, timeout: int = 90000, use_proxy: bool = False):
        self.timeout = timeout
        self.use_proxy = use_proxy
        
        # Rotating user agents to avoid detection
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        # Multiple search URL patterns
        self.search_patterns = [
            "https://www.temu.com/search_result.html?search_key={}",
            "https://www.temu.com/search.html?search_key={}",
            "https://www.temu.com/search?q={}",
            "https://www.temu.com/s?q={}"
        ]
        
        # Product selectors that might change
        self.product_selectors = [
            "div[data-qa-gallery-type='list-gallery'] > div",
            ".product-item",
            ".item",
            "[data-product-id]",
            ".product-card",
            ".search-result-item"
        ]
        
        # Price selectors
        self.price_selectors = [
            "div[data-qa-id='ad-price']",
            ".price",
            ".product-price",
            "[data-price]",
            ".cost"
        ]
        
        # Title selectors
        self.title_selectors = [
            "p._x_line-clamp-2",
            ".product-title",
            ".title",
            ".name",
            "h3",
            "h4"
        ]

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Enhanced product scraping with multiple fallback strategies
        """
        logger.info(f"🚀 Starting enhanced Temu scraper for: '{search_term}'")
        
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(f"🔄 Attempt {attempt + 1} of {max_retries}")
            
            try:
                products = await self._scrape_attempt(search_term, limit, attempt)
                if products:
                    logger.success(f"✅ Successfully scraped {len(products)} products")
                    return products
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = random.uniform(2, 5)
                    logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
        
        logger.error("💥 All scraping attempts failed")
        return None

    async def _scrape_attempt(self, search_term: str, limit: int, attempt: int) -> Optional[List[Dict[str, Any]]]:
        """Single scraping attempt with enhanced anti-detection"""
        browser = None
        
        try:
            async with async_playwright() as p:
                # Launch browser with stealth options - use non-headless for better success
                browser = await p.chromium.launch(
                    headless=False,  # Changed to False to avoid detection
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',  # Disable images for faster loading
                        '--disable-javascript',  # Temporarily disable JS to see raw HTML
                        '--user-data-dir=/tmp/chrome-data'
                    ]
                )
                
                # Create context with random user agent
                user_agent = random.choice(self.user_agents)
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York',
                    ignore_https_errors=True,
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0',
                        'Referer': 'https://www.google.com/'
                    }
                )
                
                # Apply stealth mode
                await Malenia.apply_stealth(context)
                
                page = await context.new_page()
                
                # Add random delays and human-like behavior
                await self._simulate_human_behavior(page)
                
                # Try different search patterns
                for pattern in self.search_patterns:
                    try:
                        search_url = pattern.format(search_term.replace(' ', '%20'))
                        logger.info(f"🌐 Trying search pattern: {search_url}")
                        
                        # Navigate with random delay
                        await asyncio.sleep(random.uniform(1, 3))
                        await page.goto(search_url, timeout=self.timeout)
                        
                        # Wait for page load
                        await page.wait_for_timeout(random.uniform(3000, 5000))
                        
                        # Check if page loaded successfully
                        if await self._is_page_loaded(page):
                            logger.info("✅ Page loaded successfully")
                            break
                        else:
                            logger.warning("⚠️ Page didn't load properly, trying next pattern")
                            continue
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Pattern failed: {e}")
                        continue
                
                # Take screenshot for debugging
                await page.screenshot(path=f'temu_debug_attempt_{attempt}.png')
                logger.info(f"📸 Screenshot saved: temu_debug_attempt_{attempt}.png")
                
                # Save HTML content for debugging
                html_content = await page.content()
                with open(f'temu_debug_attempt_{attempt}.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"💾 HTML content saved: temu_debug_attempt_{attempt}.html")
                
                # Extract products using multiple selector strategies
                products = await self._extract_products(page, limit)
                
                if products:
                    await browser.close()
                    return products
                    
                # If no products found, try alternative extraction method
                logger.info("🔄 No products found with primary method, trying alternative...")
                products = await self._extract_products_alternative(page, limit)
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"💥 Scraping attempt failed: {e}")
            if browser:
                await browser.close()
            return None

    async def _simulate_human_behavior(self, page):
        """Simulate human-like browsing behavior"""
        # Random mouse movements
        await page.mouse.move(
            random.randint(100, 800),
            random.randint(100, 600)
        )
        
        # Random scroll
        await page.evaluate(f"window.scrollTo(0, {random.randint(100, 500)})")
        await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _is_page_loaded(self, page) -> bool:
        """Check if the page loaded successfully"""
        try:
            # Wait for any content to load
            await page.wait_for_timeout(3000)
            
            # Check if we have any content
            content = await page.content()
            if len(content) < 1000:  # Too short, probably error page
                return False
                
            # Check for common error indicators
            error_indicators = ['error', 'blocked', 'access denied', 'captcha']
            page_text = await page.inner_text('body')
            if any(indicator in page_text.lower() for indicator in error_indicators):
                return False
                
            return True
            
        except Exception:
            return False

    async def _extract_products(self, page, limit: int) -> List[Dict[str, Any]]:
        """Primary product extraction method"""
        products = []
        
        for selector in self.product_selectors:
            try:
                logger.info(f"🔍 Trying selector: {selector}")
                
                # Wait for selector with timeout
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                except:
                    continue
                
                # Get all product elements
                product_elements = await page.query_selector_all(selector)
                logger.info(f"📦 Found {len(product_elements)} elements with selector: {selector}")
                
                if not product_elements:
                    continue
                
                # Extract product information
                for element in product_elements[:limit]:
                    try:
                        product = await self._extract_single_product(element)
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
        
        return products

    async def _extract_single_product(self, element) -> Optional[Dict[str, Any]]:
        """Extract information from a single product element"""
        try:
            # Extract title
            title = 'N/A'
            for title_sel in self.title_selectors:
                try:
                    title_elem = await element.query_selector(title_sel)
                    if title_elem:
                        title = await title_elem.inner_text()
                        if title.strip():
                            break
                except:
                    continue
            
            # Extract price
            price = 'N/A'
            for price_sel in self.price_selectors:
                try:
                    price_elem = await element.query_selector(price_sel)
                    if price_elem:
                        price = await price_elem.inner_text()
                        if price.strip():
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
            
            # Extract product URL
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
                    'title': title.strip(),
                    'price': price.strip(),
                    'imageUrl': image_url,
                    'productUrl': product_url
                }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting product details: {e}")
        
        return None

    async def _extract_products_alternative(self, page, limit: int) -> List[Dict[str, Any]]:
        """Alternative extraction method using page content analysis"""
        try:
            # Get all links on the page
            links = await page.query_selector_all('a[href*="/product/"]')
            products = []
            
            for link in links[:limit]:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extract title from link text
                    title = await link.inner_text()
                    if not title.strip():
                        continue
                    
                    # Make URL absolute
                    if href.startswith('/'):
                        href = f"https://www.temu.com{href}"
                    
                    products.append({
                        'title': title.strip(),
                        'price': 'Price not available',
                        'imageUrl': 'Image not available',
                        'productUrl': href
                    })
                    
                except Exception as e:
                    logger.debug(f"⚠️ Error processing link: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"💥 Alternative extraction failed: {e}")
            return []

# Usage example
async def test_temu_scraper():
    """Test function for the enhanced Temu scraper"""
    scraper = TemuScraperEnhanced()
    
    # First test: Try to access Temu homepage
    logger.info("🧪 Testing Temu homepage access...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Try homepage first
            logger.info("🌐 Accessing Temu homepage...")
            await page.goto("https://www.temu.com", timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Take screenshot
            await page.screenshot(path='temu_homepage_test.png')
            logger.info("📸 Homepage screenshot saved: temu_homepage_test.png")
            
            # Save HTML
            html_content = await page.content()
            with open('temu_homepage_test.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("💾 Homepage HTML saved: temu_homepage_test.html")
            
            # Check page title
            title = await page.title()
            logger.info(f"📄 Page title: {title}")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Homepage test failed: {e}")
        return
    
    # Now test the product search
    logger.info("🔍 Testing product search...")
    products = await scraper.get_products("phone case", limit=5)
    
    if products:
        print(f"✅ Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['title']} - {product['price']}")
    else:
        print("❌ No products found")

async def simple_test():
    """Simple test to check basic Temu access"""
    logger.info("🧪 Simple Temu access test...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            logger.info("🌐 Going to Temu...")
            await page.goto("https://www.temu.com")
            await page.wait_for_timeout(5000)
            
            await page.screenshot(path='simple_test.png')
            logger.info("📸 Screenshot saved: simple_test.png")
            
            content = await page.content()
            logger.info(f"📄 Page content length: {len(content)} characters")
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"❌ Simple test failed: {e}")

if __name__ == "__main__":
    # Run simple test first
    asyncio.run(simple_test())
