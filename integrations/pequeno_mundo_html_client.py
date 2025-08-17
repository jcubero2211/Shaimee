import asyncio
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup

load_dotenv()

class PequenoMundoClient:
    def __init__(self, timeout: int = 30000):
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS") 
        self.proxy_host = os.getenv("PROXY_HOST")
        self.proxy_port = os.getenv("PROXY_PORT")
        self.timeout = timeout

        if not all([self.proxy_user, self.proxy_pass, self.proxy_host, self.proxy_port]):
            logger.warning("⚠️  Proxy credentials not fully set - using direct connection")
            self.use_proxy = False
        else:
            self.use_proxy = True
            logger.info(f"🇨🇷 Pequeño Mundo HTML client with proxy: {self.proxy_host}:{self.proxy_port}")

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch products from Pequeño Mundo by parsing HTML content only
        Focus: Extract product data for rebranding pipeline
        """
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"🔍 Fetching HTML for Pequeño Mundo search: '{search_term}'")

        # Costa Rica browser headers to avoid geo-blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CR,es;q=0.9,es-419;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }

        # Session cookies
        cookies = {
            'store': 'default',
            'currency': 'CRC',
            'PHPSESSID': f'pm_{int(asyncio.get_event_loop().time()*1000)}'
        }

        try:
            # Configure proxy if available (using requests-style proxy format)
            proxy_url = None
            if self.use_proxy:
                proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
                logger.info("🌐 Using proxy for Costa Rica IP")

            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout/1000)

            async with aiohttp.ClientSession(connector=connector) as session:
                logger.info(f"📡 Fetching: {search_url}")
                
                async with session.get(
                    search_url,
                    headers=headers,
                    cookies=cookies,
                    proxy=proxy_url,
                    timeout=timeout,
                    allow_redirects=True
                ) as response:
                    
                    status = response.status
                    logger.info(f"📊 Response status: {status}")
                    
                    if status == 200:
                        html_content = await response.text()
                        logger.success(f"✅ Successfully fetched HTML ({len(html_content)} chars)")
                        
                        # Save HTML for debugging
                        debug_file = f"{search_term}_pm_html.html"
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        logger.info(f"💾 Saved HTML: {debug_file}")
                        
                        # Parse products from HTML
                        products = await self._extract_products_from_html(html_content, search_term, limit)
                        
                        if products:
                            logger.success(f"🎉 Extracted {len(products)} products for rebranding")
                            return products
                        else:
                            logger.warning(f"😞 No products found in HTML for '{search_term}'")
                            return None
                            
                    elif status == 403:
                        logger.error("🚫 403 Forbidden - Site is blocking our request")
                        if self.use_proxy:
                            logger.info("💡 Try: Different proxy IP or session rotation")
                        else:
                            logger.info("💡 Try: Enable proxy for Costa Rica IP")
                        return None
                        
                    elif status == 407:
                        logger.error("🔐 407 Proxy Authentication Failed")
                        logger.info("💡 Check proxy credentials in .env file")
                        return None
                        
                    else:
                        logger.error(f"❌ Unexpected HTTP status: {status}")
                        return None

        except Exception as e:
            logger.error(f"💥 Error fetching HTML: {str(e)}")
            return None

    async def _extract_products_from_html(self, html_content: str, search_term: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract product data from HTML for rebranding pipeline
        Returns: List of dicts with title, price, imageUrl, productUrl
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            seen_urls = set()
            
            logger.info("🔍 Parsing HTML for product data...")
            
            # Magento/e-commerce product selectors (most to least specific)
            product_selectors = [
                '.product-item',                    # Most common
                '.item.product',                    # Alternative
                '.product-item-info',               # Wrapper
                '.product-items > li',              # List format
                '.products-grid .item',             # Grid layout
                '.products.list .item',             # List layout
                '[data-product-id]',                # Data attribute
                '.catalog-product-item',            # Catalog view
                '.product-list .item'               # Generic list
            ]
            
            # Find all product containers
            all_containers = []
            for selector in product_selectors:
                containers = soup.select(selector)
                if containers:
                    logger.debug(f"🎯 Found {len(containers)} products with: {selector}")
                    all_containers.extend(containers)
            
            # Remove duplicates
            unique_containers = []
            seen_html = set()
            for container in all_containers:
                # Use first 150 chars as unique identifier
                container_key = str(container)[:150]
                if container_key not in seen_html:
                    seen_html.add(container_key)
                    unique_containers.append(container)
            
            logger.info(f"📦 Processing {len(unique_containers)} unique product containers")
            
            for container in unique_containers[:limit]:
                try:
                    # 1. Extract Product URL
                    product_url = self._extract_product_url(container)
                    if not product_url or product_url in seen_urls:
                        continue
                    seen_urls.add(product_url)
                    
                    # 2. Extract Title
                    title = self._extract_product_title(container)
                    if not title or title == 'No title':
                        continue
                    
                    # 3. Extract Price
                    price = self._extract_product_price(container)
                    
                    # 4. Extract Image URL
                    image_url = self._extract_product_image(container)
                    
                    # 5. Create product data for rebranding
                    product_data = {
                        'title': title.strip(),
                        'price': price.strip() if price else 'No price',
                        'imageUrl': image_url,
                        'productUrl': product_url
                    }
                    
                    products.append(product_data)
                    logger.debug(f"✅ Extracted: {title} - {price}")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error extracting product data: {e}")
                    continue
            
            logger.info(f"🎯 Successfully extracted {len(products)} products for rebranding")
            return products
            
        except Exception as e:
            logger.error(f"💥 Error parsing HTML: {e}")
            return []

    def _extract_product_url(self, container) -> Optional[str]:
        """Extract and normalize product URL"""
        link_elem = container.find('a', href=True)
        if not link_elem:
            return None
            
        url = link_elem['href']
        if url.startswith('/'):
            url = 'https://tienda.pequenomundo.com' + url
        elif not url.startswith('http'):
            return None
            
        return url

    def _extract_product_title(self, container) -> str:
        """Extract product title using multiple strategies"""
        # Try specific selectors first
        title_selectors = [
            '.product-item-name a',
            '.product-item-name',
            '.product-name',
            '.name',
            'h2',
            'h3',
            '.product-item-link'
        ]
        
        for selector in title_selectors:
            elem = container.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 3:  # Valid title
                    return title
        
        # Fallback to link text
        link_elem = container.find('a')
        if link_elem:
            title = link_elem.get_text(strip=True)
            if title and len(title) > 3:
                return title
            # Try title attribute
            title = link_elem.get('title', '')
            if title:
                return title
        
        return 'No title'

    def _extract_product_price(self, container) -> str:
        """Extract product price in Costa Rican colones or USD"""
        price_selectors = [
            '.price',
            '.product-price',
            '.price-box .price',
            '.special-price',
            '.final-price',
            '[data-price]',
            '.price-current'
        ]
        
        for selector in price_selectors:
            elem = container.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                # Check if it contains currency symbols or numbers
                if any(symbol in price_text for symbol in ['₡', '$', '¢']) or any(c.isdigit() for c in price_text):
                    return price_text
        
        return 'No price'

    def _extract_product_image(self, container) -> str:
        """Extract and normalize product image URL"""
        img_elem = container.find('img')
        if not img_elem:
            return 'No image'
        
        # Try different image attributes
        image_url = (img_elem.get('src') or 
                    img_elem.get('data-src') or 
                    img_elem.get('data-lazy') or 
                    img_elem.get('data-original') or 
                    'No image')
        
        if image_url == 'No image':
            return image_url
        
        # Normalize URL
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://tienda.pequenomundo.com' + image_url
        
        return image_url
