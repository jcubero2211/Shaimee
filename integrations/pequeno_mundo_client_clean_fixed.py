from typing import Any, Dict, List, Optional
from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
import asyncio

class PequenoMundoClient:
    def __init__(self, timeout: int = 30000):
        self.timeout = timeout

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch products from Pequeño Mundo website by search term.
        
        Args:
            search_term: The search term to look for
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries with title, price, imageUrl, and productUrl
        """
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"Searching Pequeño Mundo for: '{search_term}'")
        
        # Headers to mimic a real browser and avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-419,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://tienda.pequenomundo.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        
        # Cookies that help bypass bot detection
        cookies = {
            'store': 'default',
            'PHPSESSID': f'visitor_{int(asyncio.get_event_loop().time()*1000)}',
            'form_key': f'key_{int(asyncio.get_event_loop().time())}',
            'mage-cache-storage': '{}',
            'mage-cache-storage-section-invalidation': '{}',
            'mage-messages': '',
        }
        
        try:
            # Try alternative URLs if main one fails
            urls_to_try = [
                search_url,
                f"https://tienda.pequenomundo.com/catalogsearch/result/index/?q={search_term.replace(' ', '+')}"
            ]
            
            html_content = None
            successful_url = None
            
            # Try each URL until success
            for url in urls_to_try:
                try:
                    logger.info(f"Trying URL: {url}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            url, 
                            headers=headers,
                            cookies=cookies,
                            timeout=aiohttp.ClientTimeout(total=self.timeout/1000),
                            allow_redirects=True
                        ) as response:
                            status = response.status
                            logger.info(f"Response status: {status}")
                            
                            if status == 200:
                                html_content = await response.text()
                                successful_url = url
                                logger.success(f"Successfully fetched from: {url}")
                                break
                            else:
                                logger.warning(f"URL {url} returned HTTP {status}")
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {str(e)}")
                    continue
            
            if not html_content:
                logger.error("All URLs failed")
                return None
                
            # Save the HTML for debugging with search term in filename
            debug_filename = f"{search_term}_products.html"
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved page HTML to {debug_filename}")
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            seen_products = set()
            
            # Try different product container selectors
            product_containers = []
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
            
            # Find all product containers using the selectors
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
            
            # If no containers found, try a more aggressive approach
            if not unique_containers:
                logger.warning("No product containers found with standard selectors. Trying fallback...")
                unique_containers = soup.find_all(True, class_=lambda x: x and any(
                    term in x.lower() for term in ['product', 'item', 'prod', 'prd']
                ))
                logger.info(f"Found {len(unique_containers)} elements with fallback selectors")
            
            # Process each container to extract product info
            for container in unique_containers:
                if len(products) >= limit:
                    break
                    
                try:
                    # Find the product link
                    link_elem = container.find('a', href=True)
                    if not link_elem or not link_elem.get('href'):
                        continue
                        
                    product_url = link_elem['href']
                    
                    # Skip if we've already seen this product
                    if product_url in seen_products:
                        continue
                        
                    seen_products.add(product_url)
                    
                    # Extract title
                    title = 'No title'
                    title_elem = container.find(class_=lambda x: x and any(
                        term in x.lower() for term in ['name', 'title']
                    ))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    elif link_elem:
                        title = link_elem.get_text(strip=True) or link_elem.get('title', 'No title')
                    
                    # Extract price
                    price = 'No price'
                    price_elem = container.find(class_=lambda x: x and 'price' in x.lower())
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                    
                    # Extract image URL
                    image_url = 'No image'
                    img_elem = container.find('img')
                    if img_elem:
                        image_url = img_elem.get('src') or img_elem.get('data-src', 'No image')
                        
                        # Make image URL absolute if it's relative
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
                    logger.warning(f"Error processing product: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(products)} products for '{search_term}'")
            return products if products else None
                    
        except Exception as e:
            logger.error(f"Error fetching or parsing page: {str(e)}")
            return None
