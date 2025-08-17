import asyncio
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

load_dotenv()

class PequenoMundoClient:
    def __init__(self, timeout: int = 60000):
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")
        self.proxy_host = os.getenv("PROXY_HOST")
        self.proxy_port = os.getenv("PROXY_PORT")

        if not all([self.proxy_user, self.proxy_pass, self.proxy_host, self.proxy_port]):
            raise ValueError("Proxy credentials not fully set in environment variables.")
            
        self.timeout = timeout
        logger.info(f"🇨🇷 Pequeño Mundo client initialized with working proxy format")

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch products from Pequeño Mundo using the SAME proxy format that works for Temu
        """
        logger.info(f"🔍 Starting Pequeño Mundo scraper for: '{search_term}'")
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"

        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                # Use the SAME proxy format that works for Temu
                context = await browser.new_context(
                    proxy={
                        "server": f"http://{self.proxy_host}:{self.proxy_port}",
                        "username": self.proxy_user,
                        "password": self.proxy_pass
                    },
                    ignore_https_errors=True,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    # Costa Rica locale
                    locale='es-CR',
                    timezone_id='America/Costa_Rica'
                )
                
                page = await context.new_page()
                
                # Add Costa Rica-specific headers
                await page.set_extra_http_headers({
                    'Accept-Language': 'es-CR,es;q=0.9,es-419;q=0.8,en;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
                })

                logger.info(f"🌐 Navigating to: {search_url}")
                await page.goto(search_url, timeout=self.timeout)

                # Handle potential cookie banner
                try:
                    await page.wait_for_selector('.cookie-consent, .cookie-banner', timeout=3000)
                    await page.click('.cookie-consent button, .cookie-banner button')
                    logger.info("✅ Handled cookie consent")
                except:
                    pass  # No cookie banner or already handled

                # Wait for page to load
                await page.wait_for_timeout(3000)
                
                # Take screenshot for debugging
                await page.screenshot(path='pm_debug.png')
                logger.info("📸 Screenshot saved: pm_debug.png")

                # Get page content
                html_content = await page.content()
                
                # Save HTML for analysis
                debug_filename = f"{search_term}_pm_success.html"
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"💾 Saved HTML: {debug_filename}")
                
                # Parse products
                products = await self._parse_products(html_content, limit)
                
                await browser.close()
                
                if products:
                    logger.success(f"🎉 Successfully found {len(products)} products for '{search_term}'")
                    return products
                else:
                    logger.warning(f"😞 No products found for '{search_term}'")
                    return None

        except PlaywrightTimeoutError:
            logger.error(f"⏰ Timeout error for {search_url}")
            if browser:
                await browser.close()
            return None
        except Exception as e:
            logger.error(f"💥 Error during scraping: {e}")
            if browser:
                await browser.close()
            return None

    async def _parse_products(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse HTML content to extract product information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            seen_products = set()
            
            # Comprehensive selectors for Magento-based sites like Pequeño Mundo
            selectors = [
                '.product-item',
                '.item.product',
                '.product-item-info',
                '.product-items > li',
                '.products-grid .item',
                '[data-product-id]',
                '.catalog-product-view',
                '.product-list .item'
            ]
            
            # Find product containers
            product_containers = []
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    logger.debug(f"🎯 Found {len(containers)} products with: {selector}")
                    product_containers.extend(containers)
            
            # Remove duplicates
            unique_containers = []
            seen_html = set()
            for container in product_containers:
                container_key = str(container)[:100]
                if container_key not in seen_html:
                    seen_html.add(container_key)
                    unique_containers.append(container)
            
            logger.info(f"📦 Processing {len(unique_containers)} unique product containers")
            
            for container in unique_containers[:limit]:
                try:
                    # Extract product URL
                    link_elem = container.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    product_url = link_elem['href']
                    if product_url.startswith('/'):
                        product_url = 'https://tienda.pequenomundo.com' + product_url
                    
                    if product_url in seen_products:
                        continue
                    seen_products.add(product_url)
                    
                    # Extract title
                    title = 'No title'
                    title_selectors = [
                        '.product-item-name', '.product-name', '.name', 
                        'h2', 'h3', '.product-item-link'
                    ]
                    
                    for title_sel in title_selectors:
                        title_elem = container.select_one(title_sel)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            break
                    
                    # Fallback to link text
                    if title == 'No title' and link_elem:
                        title = link_elem.get_text(strip=True) or link_elem.get('title', 'No title')
                    
                    # Extract price
                    price = 'No price'
                    price_selectors = [
                        '.price', '.product-price', '.price-box .price',
                        '.special-price', '[data-price]'
                    ]
                    
                    for price_sel in price_selectors:
                        price_elem = container.select_one(price_sel)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            if '₡' in price_text or '$' in price_text or any(c.isdigit() for c in price_text):
                                price = price_text
                                break
                    
                    # Extract image
                    image_url = 'No image'
                    img_elem = container.find('img')
                    if img_elem:
                        image_url = (img_elem.get('src') or 
                                   img_elem.get('data-src') or 
                                   img_elem.get('data-lazy', 'No image'))
                        
                        # Make absolute URL
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = 'https://tienda.pequenomundo.com' + image_url
                    
                    # Only add valid products
                    if title != 'No title' and title.strip():
                        products.append({
                            'title': title,
                            'price': price,
                            'imageUrl': image_url,
                            'productUrl': product_url
                        })
                        
                        logger.debug(f"✅ Found: {title} - {price}")
                
                except Exception as e:
                    logger.warning(f"⚠️  Error processing product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"💥 Error parsing HTML: {e}")
            return []
