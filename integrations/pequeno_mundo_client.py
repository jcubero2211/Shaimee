import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

class PequenoMundoClient:
    def __init__(self, timeout: int = 60000):
        self.timeout = timeout
        self.use_playwright = True  # Flag to determine which method to use

    async def get_products_with_aiohttp(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Alternative method using aiohttp directly"""
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"Trying aiohttp method for search term: '{search_term}'")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(f"HTTP {response.status} error from aiohttp method")
                        return None
                    
                    html_content = await response.text()
                    return await self.parse_html_content(html_content, search_term, limit)
                    
        except Exception as e:
            logger.error(f"Aiohttp method failed: {str(e)}")
            return None

    async def get_products_with_playwright(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Original method using Playwright"""
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"Starting Playwright scraper for search term: '{search_term}'")
        
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the search URL
                logger.info(f"Navigating to: {search_url}")
                await page.goto(search_url)
                
                # Handle cookie consent if present
                try:
                    await page.wait_for_selector('.cookie-consent-banner', timeout=3000)
                    await page.click('.cookie-consent-banner button')
                    logger.info("Accepted cookies")
                except:
                    pass
                
                # Take screenshot for debugging
                await page.screenshot(path="debug_screenshot.png")
                logger.info("Screenshot saved to debug_screenshot.png")
                
                # Save HTML for debugging
                html_content = await page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Page HTML saved to debug_page.html")
                
                # Wait for products to load
                logger.info("Waiting for any product elements to appear...")
                
                # Try to find any products on the page
                await page.wait_for_timeout(2000)  # Wait 2 seconds for page to fully load
                
                # Count products found
                product_elements = await page.query_selector_all(
                    '.product-item, .item.product, .product-item-info, [data-product-id]'
                )
                logger.info(f"Found {len(product_elements)} products")
                
                return await self.parse_html_content(html_content, search_term, limit)
                
        except PlaywrightTimeoutError:
            logger.error(f"Timeout error: The product grid did not appear in time on {search_url}")
            return None
        except Exception as e:
            logger.error(f"Playwright method failed: {e}")
            return None
        finally:
            if browser:
                await browser.close()

    async def parse_html_content(self, html_content: str, search_term: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Parse HTML content and extract product information"""
        try:
            # Save the HTML for debugging
            debug_filename = f"{search_term}_products.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved page HTML to {debug_filename}")
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            seen_products = set()
            
            # Try different product container selectors
            selectors = [
                '.product-item',
                '.item.product', 
                '.product-item-info',
                '.product-items > li',
                '.product-list > li',
                '.products-grid .item',
                '.products.list .item',
                '[data-product-id]',
                '.product-item-details',
                '.product.details',
                '.product-item-photo',
                '.product-item-name',
                '.product.name',
                '.product-info',
                '.product-item-link'
            ]
            
            product_containers = []
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    logger.debug(f"Found {len(containers)} elements with selector: {selector}")
                    product_containers.extend(containers)
            
            # Remove duplicates while preserving order
            unique_containers = []
            seen_containers = set()
            for container in product_containers:
                container_str = str(container)
                if container_str not in seen_containers:
                    seen_containers.add(container_str)
                    unique_containers.append(container)
            
            logger.info(f"Found {len(unique_containers)} unique product containers")
            
            # If no containers found, try fallback
            if not unique_containers:
                logger.warning("No product containers found. Trying fallback...")
                unique_containers = soup.find_all(True, class_=lambda x: x and any(
                    term in x.lower() for term in ['product', 'item', 'prod', 'prd']
                ))
                logger.info(f"Found {len(unique_containers)} elements with fallback")
            
            # Process each container
            for container in unique_containers:
                if len(products) >= limit:
                    break
                    
                try:
                    # Find product link
                    link_elem = container.find('a', href=True)
                    if not link_elem or not link_elem.get('href'):
                        continue
                        
                    product_url = link_elem['href']
                    if product_url in seen_products:
                        continue
                        
                    seen_products.add(product_url)
                    
                    # Extract title - try multiple approaches
                    title = 'No title'
                    title_elem = container.find(class_=lambda x: x and any(
                        term in x.lower() for term in ['name', 'title']
                    ))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    elif link_elem:
                        title = link_elem.get_text(strip=True) or link_elem.get('title', '')
                    
                    # Extract price
                    price = 'No price'
                    price_elem = container.find(class_=lambda x: x and 'price' in x.lower())
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                    
                    # Extract image
                    image_url = 'No image'
                    img_elem = container.find('img')
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src', 'No image')
                        
                        # Make absolute URL
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = 'https://tienda.pequenomundo.com' + image_url
                    
                    # Make product URL absolute
                    if product_url.startswith('/'):
                        product_url = 'https://tienda.pequenomundo.com' + product_url
                    
                    products.append({
                        'title': title,
                        'price': price,
                        'imageUrl': image_url,
                        'productUrl': product_url
                    })
                    
                    logger.debug(f"Extracted product: {title} - {price}")
                    
                except Exception as e:
                    logger.warning(f"Error processing product container: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(products)} products for '{search_term}'")
            return products if products else None
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            return None

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Main method that tries both approaches"""
        logger.info(f"Starting scraper for Pequeño Mundo with search term: '{search_term}'")
        
        # First try aiohttp (faster)
        products = await self.get_products_with_aiohttp(search_term, limit)
        
        # If that fails, try Playwright
        if not products and self.use_playwright:
            logger.info("Aiohttp failed, trying Playwright...")
            products = await self.get_products_with_playwright(search_term, limit)
        
        return products
