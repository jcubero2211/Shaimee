import asyncio
import aiohttp
import random
from typing import Any, Dict, List, Optional
from loguru import logger
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import json
import re

class AliExpressClient:
    def __init__(self, timeout: int = 45):
        self.timeout = timeout
        self.base_url = "https://www.aliexpress.com"
        self.search_url = "https://www.aliexpress.com/wholesale"
        
        # Common headers to avoid detection
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Search for products on AliExpress
        """
        try:
            logger.info(f"🔍 Searching AliExpress for: {search_term}")
            
            # Prepare search URL
            encoded_term = quote_plus(search_term)
            search_url = f"{self.search_url}?SearchText={encoded_term}&SortType=total_tranpro_desc"
            
            # Prepare headers with random user agent
            headers = self.headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Add random delay to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 3))
                
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.error(f"❌ AliExpress returned status {response.status}")
                        return None
                    
                    html_content = await response.text()
                    logger.info(f"📄 Received {len(html_content)} characters from AliExpress")
                    
                    # Parse products
                    products = await self._parse_products(html_content, limit)
                    
                    if products:
                        logger.info(f"✅ Found {len(products)} products from AliExpress")
                        return products
                    else:
                        logger.warning("⚠️ No products found in AliExpress response")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error(f"⏰ AliExpress request timed out after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"💥 AliExpress scraping failed: {e}")
            return None

    async def _parse_products(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse product information from AliExpress HTML
        """
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # AliExpress often loads content via JavaScript, so we'll try multiple approaches
            
            # Method 1: Try to find JSON data in script tags
            script_tags = soup.find_all('script', type='text/javascript')
            for script in script_tags:
                if script.string and 'window.runParams' in script.string:
                    # Extract JSON data from the script
                    try:
                        json_match = re.search(r'window\.runParams\s*=\s*({.*?});', script.string, re.DOTALL)
                        if json_match:
                            json_data = json.loads(json_match.group(1))
                            products.extend(self._extract_from_json(json_data, limit))
                            break
                    except Exception as e:
                        logger.debug(f"Failed to parse JSON from script: {e}")
                        continue
            
            # Method 2: Try to find product cards in HTML (fallback)
            if not products:
                products.extend(self._extract_from_html(soup, limit))
            
            # Method 3: Look for specific AliExpress product selectors
            if not products:
                products.extend(self._extract_with_selectors(soup, limit))
                
        except Exception as e:
            logger.error(f"Error parsing AliExpress HTML: {e}")
        
        return products[:limit]

    def _extract_from_json(self, json_data: Dict, limit: int) -> List[Dict[str, Any]]:
        """
        Extract products from JSON data found in scripts
        """
        products = []
        
        try:
            # Navigate through the JSON structure to find products
            if 'mods' in json_data:
                for mod_key, mod_value in json_data['mods'].items():
                    if isinstance(mod_value, dict) and 'props' in mod_value:
                        props = mod_value['props']
                        if 'items' in props:
                            items = props['items']
                            for item in items[:limit]:
                                product = self._parse_json_product(item)
                                if product:
                                    products.append(product)
                                    
        except Exception as e:
            logger.debug(f"Error extracting from JSON: {e}")
            
        return products

    def _parse_json_product(self, item: Dict) -> Optional[Dict[str, Any]]:
        """
        Parse individual product from JSON item
        """
        try:
            product = {
                'title': item.get('title', {}).get('displayTitle', 'No title'),
                'price': self._extract_price_from_json(item),
                'image_url': self._extract_image_from_json(item),
                'product_url': self._extract_url_from_json(item),
                'rating': item.get('evaluation', {}).get('starRating', 0),
                'orders': item.get('trade', {}).get('tradeDesc', '0'),
                'shipping': item.get('logistics', {}).get('logisticsDesc', 'Unknown')
            }
            
            # Validate required fields
            if product['title'] != 'No title' and product['price'] and product['product_url']:
                return product
                
        except Exception as e:
            logger.debug(f"Error parsing JSON product: {e}")
            
        return None

    def _extract_price_from_json(self, item: Dict) -> str:
        """Extract price from JSON item"""
        try:
            if 'prices' in item:
                prices = item['prices']
                if isinstance(prices, list) and prices:
                    return prices[0].get('formattedPrice', 'N/A')
                elif isinstance(prices, dict):
                    return prices.get('formattedPrice', 'N/A')
        except:
            pass
        return 'N/A'

    def _extract_image_from_json(self, item: Dict) -> str:
        """Extract image URL from JSON item"""
        try:
            if 'image' in item:
                image_data = item['image']
                if isinstance(image_data, dict):
                    return image_data.get('imgUrl', '')
                elif isinstance(image_data, str):
                    return image_data
        except:
            pass
        return ''

    def _extract_url_from_json(self, item: Dict) -> str:
        """Extract product URL from JSON item"""
        try:
            if 'productDetailUrl' in item:
                url = item['productDetailUrl']
                if not url.startswith('http'):
                    url = f"https:{url}" if url.startswith('//') else f"{self.base_url}{url}"
                return url
        except:
            pass
        return ''

    def _extract_from_html(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Extract products from HTML elements (fallback method)
        """
        products = []
        
        # Common AliExpress product selectors
        product_selectors = [
            '.list-item',
            '.product-item',
            '.item-wrap',
            '[data-spm-anchor-id]'
        ]
        
        for selector in product_selectors:
            items = soup.select(selector)[:limit]
            if items:
                logger.info(f"Found {len(items)} items with selector: {selector}")
                
                for item in items:
                    product = self._parse_html_product(item)
                    if product:
                        products.append(product)
                        
                if products:
                    break
                    
        return products

    def _extract_with_selectors(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Try specific selectors for AliExpress products
        """
        products = []
        
        # Look for any elements that might contain product info
        potential_products = soup.find_all(['div', 'article', 'li'], limit=limit*2)
        
        for element in potential_products[:limit]:
            # Check if this element looks like a product
            if self._looks_like_product(element):
                product = self._parse_html_product(element)
                if product:
                    products.append(product)
                    
        return products

    def _looks_like_product(self, element) -> bool:
        """
        Check if an element looks like it contains product information
        """
        text = element.get_text().lower()
        
        # Look for price indicators
        price_indicators = ['$', '€', '£', 'usd', 'price', 'cost']
        has_price = any(indicator in text for indicator in price_indicators)
        
        # Look for product indicators
        product_indicators = ['buy', 'add to cart', 'order', 'shipping']
        has_product_info = any(indicator in text for indicator in product_indicators)
        
        return has_price or has_product_info

    def _parse_html_product(self, element) -> Optional[Dict[str, Any]]:
        """
        Parse product information from HTML element
        """
        try:
            # Extract title
            title_selectors = ['h1', 'h2', 'h3', '.title', '[title]', 'a']
            title = 'No title'
            
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get('title') or title_elem.get_text().strip()
                    if title and len(title) > 5:  # Reasonable title length
                        break
            
            # Extract price
            price_selectors = ['.price', '.cost', '[class*="price"]', '[class*="cost"]']
            price = 'N/A'
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    if any(char in price_text for char in ['$', '€', '£']):
                        price = price_text
                        break
            
            # Extract image
            img_elem = element.select_one('img')
            image_url = ''
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or ''
                if image_url and not image_url.startswith('http'):
                    if image_url.startswith('//'):
                        image_url = f"https:{image_url}"
                    elif image_url.startswith('/'):
                        image_url = f"{self.base_url}{image_url}"
            
            # Extract product URL
            link_elem = element.select_one('a')
            product_url = ''
            if link_elem:
                product_url = link_elem.get('href', '')
                if product_url and not product_url.startswith('http'):
                    if product_url.startswith('//'):
                        product_url = f"https:{product_url}"
                    elif product_url.startswith('/'):
                        product_url = f"{self.base_url}{product_url}"
            
            # Create product dict
            product = {
                'title': title,
                'price': price,
                'image_url': image_url,
                'product_url': product_url,
                'rating': 0,
                'orders': 'Unknown',
                'shipping': 'Unknown'
            }
            
            # Validate that we have minimum required info
            if title != 'No title' and (price != 'N/A' or product_url):
                return product
                
        except Exception as e:
            logger.debug(f"Error parsing HTML product: {e}")
            
        return None


async def test_aliexpress_client():
    """
    Test the AliExpress client
    """
    client = AliExpressClient()
    
    search_terms = ['phone case', 'bluetooth headphones', 'laptop stand']
    
    for term in search_terms:
        logger.info(f"🧪 Testing search for: {term}")
        products = await client.get_products(term, limit=5)
        
        if products:
            logger.info(f"✅ Found {len(products)} products for '{term}'")
            for i, product in enumerate(products, 1):
                logger.info(f"  {i}. {product['title'][:50]}... - {product['price']}")
        else:
            logger.warning(f"⚠️ No products found for '{term}'")
        
        # Small delay between searches
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(test_aliexpress_client())
