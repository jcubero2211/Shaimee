from typing import Any, Dict, List, Optional
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import os
from dotenv import load_dotenv

class PequenoMundoClient:
    def __init__(self, timeout: int = 30000):
        self.timeout = timeout
        load_dotenv()
        
        # Load proxy configuration
        self.proxy_host = os.getenv('PROXY_HOST')
        self.proxy_port = int(os.getenv('PROXY_PORT', 33335))
        self.proxy_user = os.getenv('PROXY_USER')
        self.proxy_pass = os.getenv('PROXY_PASS')
        
        if all([self.proxy_host, self.proxy_user, self.proxy_pass]):
            # Add Costa Rica country targeting and session ID for geo-location
            import random
            session_id = random.randint(100000, 999999)
            
            # Format: username-country-cr-session-<random> for Costa Rica targeting
            proxy_user_cr = f"{self.proxy_user}-country-cr-session-{session_id}"
            self.proxy_url = f"http://{proxy_user_cr}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
            
            logger.info(f"🇨🇷 Proxy configured for COSTA RICA: {self.proxy_host}:{self.proxy_port}")
            logger.info(f"🎯 Using session: {session_id}")
        else:
            self.proxy_url = None
            logger.warning("⚠️  No proxy configured - may face blocking issues")

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch products from Pequeño Mundo website by search term using proxy.
        
        Args:
            search_term: The search term to look for
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries with title, price, imageUrl, and productUrl
        """
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"🔍 Searching Pequeño Mundo for: '{search_term}' (with proxy)")
        
        # Enhanced headers to look like a real browser from Costa Rica
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-CR,es;q=0.9,es-419;q=0.8,en;q=0.7',  # Costa Rica Spanish
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Session cookies to look more legitimate
        cookies = {
            'store': 'default',
            'PHPSESSID': f'pm_session_{int(asyncio.get_event_loop().time()*1000)}',
            'form_key': f'pm_form_{int(asyncio.get_event_loop().time())}',
            'currency': 'CRC',
            'frontend': 'frontend',
            'frontend_cid': '1',
        }
        
        try:
            # Configure proxy settings
            connector = aiohttp.TCPConnector(ssl=False)
            
            if self.proxy_url:
                logger.info(f"🔄 Using proxy: {self.proxy_host}:{self.proxy_port}")
            
            # Try multiple URL variants
            urls_to_try = [
                search_url,
                f"https://tienda.pequenomundo.com/catalogsearch/result/index/?q={search_term.replace(' ', '+')}"
            ]
            
            html_content = None
            successful_url = None
            
            # Create session with proxy
            async with aiohttp.ClientSession(connector=connector) as session:
                for url in urls_to_try:
                    try:
                        logger.info(f"🌐 Trying URL: {url}")
                        
                        # Use proxy if configured
                        proxy_param = self.proxy_url if self.proxy_url else None
                        
                        async with session.get(
                            url, 
                            headers=headers,
                            cookies=cookies,
                            proxy=proxy_param,
                            timeout=aiohttp.ClientTimeout(total=self.timeout/1000),
                            allow_redirects=True,
                            ssl=False  # Sometimes helps with proxy issues
                        ) as response:
                            status = response.status
                            logger.info(f"📡 Response status: {status}")
                            
                            if status == 200:
                                html_content = await response.text()
                                successful_url = url
                                logger.success(f"✅ Successfully fetched from: {url}")
                                break
                            elif status == 403:
                                logger.warning(f"🚫 Still getting 403 from {url} - proxy may need time to rotate")
                            else:
                                logger.warning(f"⚠️  URL {url} returned HTTP {status}")
                    except Exception as e:
                        logger.warning(f"❌ Failed to fetch {url}: {str(e)}")
                        continue
            
            if not html_content:
                logger.error("💥 All URLs failed even with proxy")
                return None
                
            # Save the HTML for debugging with search term in filename
            debug_filename = f"{search_term}_products_proxy.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"💾 Saved page HTML to {debug_filename}")
            
            # Parse the HTML
            return await self._parse_html_content(html_content, search_term, limit)
                    
        except Exception as e:
            logger.error(f"💥 Error fetching or parsing page: {str(e)}")
            return None

    async def _parse_html_content(self, html_content: str, search_term: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Parse HTML content and extract product information"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            seen_products = set()
            
            # Comprehensive product selectors for Magento/e-commerce sites
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
                '.product-item-link',
                '.catalog-product-item',
                '.products-item',
                '.item-product'
            ]
            
            # Find all product containers
            product_containers = []
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    logger.debug(f"🎯 Found {len(containers)} elements with selector: {selector}")
                    product_containers.extend(containers)
            
            # Remove duplicates while preserving order
            unique_containers = []
            seen_containers = set()
            for container in product_containers:
                container_str = str(container)[:100]  # Use first 100 chars as key
                if container_str not in seen_containers:
                    seen_containers.add(container_str)
                    unique_containers.append(container)
            
            logger.info(f"📦 Found {len(unique_containers)} unique product containers")
            
            # If no containers found, try more aggressive fallback
            if not unique_containers:
                logger.warning("🔍 No product containers found. Trying aggressive search...")
                
                # Look for any element containing product-like patterns
                all_elements = soup.find_all(True)
                for element in all_elements:
                    classes = ' '.join(element.get('class', []))
                    if any(term in classes.lower() for term in ['product', 'item', 'prod']):
                        unique_containers.append(element)
                        if len(unique_containers) >= limit:
                            break
                
                logger.info(f"🔎 Found {len(unique_containers)} elements with aggressive search")
            
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
                    
                    # Extract title - multiple approaches
                    title = 'No title'
                    
                    # Try title from various places
                    title_selectors = [
                        '.product-item-name',
                        '.product-name',
                        '.name',
                        '[data-product-name]',
                        'h2', 'h3', 'h4'  # Common heading tags
                    ]
                    
                    for title_selector in title_selectors:
                        title_elem = container.select_one(title_selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            break
                    
                    # Fallback: use link text
                    if title == 'No title' and link_elem:
                        title = link_elem.get_text(strip=True) or link_elem.get('title', 'No title')
                    
                    # Extract price
                    price = 'No price'
                    price_selectors = [
                        '.price',
                        '.product-price',
                        '.price-box .price',
                        '.special-price',
                        '.final-price',
                        '[data-price]'
                    ]
                    
                    for price_selector in price_selectors:
                        price_elem = container.select_one(price_selector)
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
                                   img_elem.get('data-lazy') or 
                                   'No image')
                        
                        # Make image URL absolute
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif image_url.startswith('/'):
                            image_url = 'https://tienda.pequenomundo.com' + image_url
                    
                    # Make product URL absolute
                    if product_url.startswith('/'):
                        product_url = 'https://tienda.pequenomundo.com' + product_url
                    
                    # Only add if we got meaningful data
                    if title != 'No title' or price != 'No price':
                        products.append({
                            'title': title,
                            'price': price,
                            'imageUrl': image_url,
                            'productUrl': product_url
                        })
                        
                        logger.debug(f"✅ Extracted: {title} - {price}")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error processing product container: {str(e)}")
                    continue
            
            if products:
                logger.success(f"🎉 Successfully extracted {len(products)} products for '{search_term}'")
                return products
            else:
                logger.warning(f"😞 No valid products found for '{search_term}'")
                # Save HTML for debugging
                with open(f"debug_{search_term}_empty.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                return None
                
        except Exception as e:
            logger.error(f"💥 Error parsing HTML content: {str(e)}")
            return None
