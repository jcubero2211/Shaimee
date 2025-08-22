import asyncio
import aiohttp
import random
from typing import Any, Dict, List, Optional
from loguru import logger
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from datetime import datetime
import re

class UnimartClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "https://www.unimart.com"
        self.search_url = "https://www.unimart.com/search"
        
        # Headers to avoid detection
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.unimart.com/'
        }
        
        # Rotate user agents
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Search for products on Unimart
        """
        try:
            logger.info(f"🇨🇷 Searching Unimart for: {search_term}")
            
            # Prepare search URL
            encoded_term = quote_plus(search_term)
            search_url = f"{self.search_url}?q={encoded_term}"
            
            # Prepare headers with random user agent
            headers = self.headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Add random delay to avoid rate limiting
                await asyncio.sleep(random.uniform(1, 2))
                
                async with session.get(search_url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Unimart returned status {response.status}")
                        return None
                    
                    html_content = await response.text()
                    logger.info(f"📄 Received {len(html_content)} characters from Unimart")
                    
                    # Parse products
                    products = await self._parse_products(html_content, limit)
                    
                    if products:
                        logger.info(f"✅ Found {len(products)} products from Unimart")
                        return products
                    else:
                        logger.warning("⚠️ No products found in Unimart response")
                        return []
                        
        except asyncio.TimeoutError:
            logger.error(f"⏰ Unimart request timed out after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"💥 Unimart scraping failed: {e}")
            return None

    async def get_smartwatches(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get smartwatches from Unimart's smartwatch collection
        """
        try:
            logger.info(f"⌚ Getting smartwatches from Unimart collection")
            
            # Direct URL to smartwatch collection
            collection_url = "https://www.unimart.com/collections/smartwatches"
            
            # Prepare headers with random user agent
            headers = self.headers.copy()
            headers['User-Agent'] = random.choice(self.user_agents)
            
            # Create session with timeout
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Add random delay
                await asyncio.sleep(random.uniform(1, 2))
                
                async with session.get(collection_url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Unimart smartwatch collection returned status {response.status}")
                        return None
                    
                    html_content = await response.text()
                    logger.info(f"📄 Received {len(html_content)} characters from Unimart smartwatch collection")
                    
                    # Parse smartwatch products
                    products = await self._parse_smartwatch_collection(html_content, limit)
                    
                    if products:
                        logger.info(f"✅ Found {len(products)} smartwatches from Unimart")
                        return products
                    else:
                        logger.warning("⚠️ No smartwatches found in collection")
                        return []
                        
        except Exception as e:
            logger.error(f"💥 Unimart smartwatch collection failed: {e}")
            return None

    async def _parse_products(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse product information from Unimart search results
        """
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Try to extract from JavaScript data (FastSimon integration)
            products.extend(self._extract_from_javascript_data(html_content, limit))
            
            # Method 2: Look for product cards in search results
            if not products:
                product_selectors = [
                    '.product-item',
                    '.product-card',
                    '[data-product-id]',
                    '.product',
                    '.item',
                    '.product-grid-item',
                    '.grid-item'
                ]
                
                for selector in product_selectors:
                    items = soup.select(selector)[:limit*2]  # Get more to filter
                    if items:
                        logger.info(f"Found {len(items)} items with selector: {selector}")
                        
                        for item in items:
                            product = self._parse_product_item(item)
                            if product:
                                products.append(product)
                                
                        if products:
                            break
            
            # Method 3: Try to extract from the page structure
            if not products:
                logger.info("Trying alternative parsing method...")
                products.extend(self._extract_products_from_page_structure(soup, limit))
                
        except Exception as e:
            logger.error(f"Error parsing Unimart HTML: {e}")
        
        return products[:limit]

    async def _parse_smartwatch_collection(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse smartwatch products from the collection page
        """
        products = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Based on the HTML structure I can see, look for product elements
            # The page shows products with prices in colones (₡)
            
            # Look for price patterns (₡ followed by numbers)
            price_pattern = r'₡([\d,]+)'
            
            # Find all text elements that might contain product info
            text_elements = soup.find_all(string=True)
            
            current_product = {}
            for text in text_elements:
                text = text.strip()
                if not text:
                    continue
                
                # Look for price
                price_match = re.search(price_pattern, text)
                if price_match:
                    if current_product and 'title' in current_product:
                        # Complete the product
                        current_product['price'] = f"₡{price_match.group(1)}"
                        products.append(current_product)
                        current_product = {}
                    else:
                        # Start new product
                        current_product = {'price': f"₡{price_match.group(1)}"}
                
                # Look for product titles (smartwatch names)
                elif any(keyword in text.lower() for keyword in ['smartwatch', 'watch', 'garmin', 'samsung', 'apple', 'xiaomi', 'huawei']):
                    if len(text) > 10 and len(text) < 100:  # Reasonable title length
                        if current_product:
                            current_product['title'] = text
                        else:
                            current_product = {'title': text}
                
                # Look for product URLs
                elif text.startswith('http') or text.startswith('/'):
                    if current_product:
                        current_product['product_url'] = text if text.startswith('http') else urljoin(self.base_url, text)
            
            # Add any remaining product
            if current_product and 'title' in current_product and 'price' in current_product:
                products.append(current_product)
                
        except Exception as e:
            logger.error(f"Error parsing smartwatch collection: {e}")
        
        return products[:limit]

    def _parse_product_item(self, item) -> Optional[Dict[str, Any]]:
        """
        Parse individual product from HTML item
        """
        try:
            product = {}
            
            # Extract title
            title_selectors = ['h1', 'h2', 'h3', '.title', '.product-title', '[title]', 'a']
            for selector in title_selectors:
                title_elem = item.select_one(selector)
                if title_elem:
                    title = title_elem.get('title') or title_elem.get_text().strip()
                    if title and len(title) > 5:
                        product['title'] = title
                        break
            
            # Extract price
            price_selectors = ['.price', '.cost', '[class*="price"]', '[class*="cost"]']
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    if '₡' in price_text or '$' in price_text:
                        product['price'] = price_text
                        break
            
            # Extract image
            img_elem = item.select_one('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or ''
                if image_url:
                    if not image_url.startswith('http'):
                        image_url = urljoin(self.base_url, image_url)
                    product['image_url'] = image_url
            
            # Extract product URL
            link_elem = item.select_one('a')
            if link_elem:
                product_url = link_elem.get('href', '')
                if product_url:
                    if not product_url.startswith('http'):
                        product_url = urljoin(self.base_url, product_url)
                    product['product_url'] = product_url
            
            # Extract rating if available
            rating_elem = item.select_one('.rating, .stars, [class*="rating"]')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    product['rating'] = float(rating_match.group(1))
            
            # Validate required fields
            if 'title' in product and 'price' in product:
                return product
                
        except Exception as e:
            logger.debug(f"Error parsing product item: {e}")
            
        return None

    def _extract_with_generic_selectors(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Generic extraction method when specific selectors fail
        """
        products = []
        
        # Look for any elements that might contain product info
        potential_products = soup.find_all(['div', 'article', 'li'], limit=limit*3)
        
        for element in potential_products[:limit*2]:
            # Check if this element looks like a product
            if self._looks_like_product(element):
                product = self._parse_product_item(element)
                if product:
                    products.append(product)
                    
        return products

    def _looks_like_product(self, element) -> bool:
        """
        Check if an element looks like it contains product information
        """
        text = element.get_text().lower()
        
        # Look for price indicators (Costa Rican colones)
        price_indicators = ['₡', '$', 'price', 'precio', 'costo']
        has_price = any(indicator in text for indicator in price_indicators)
        
        # Look for product indicators
        product_indicators = ['smartwatch', 'watch', 'phone', 'celular', 'laptop', 'tablet']
        has_product_info = any(indicator in text for indicator in product_indicators)
        
        return has_price or has_product_info

    def _extract_from_javascript_data(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract products from JavaScript data embedded in the HTML (FastSimon integration)
        """
        products = []
        
        try:
            # Look for FastSimon data in the HTML
            # Pattern: "fastSimonResult":{"uuid":...,"items":[...]}
            import re
            import json
            
            # Find the fastSimonResult section - use a more flexible pattern
            fastsimon_match = re.search(r'"fastSimonResult":\s*({[^}]+"items":\s*\[[^\]]+\][^}]*})', html_content)
            if fastsimon_match:
                try:
                    # Extract the JSON-like data
                    fastsimon_data = fastsimon_match.group(1)
                    logger.info(f"Found FastSimon data: {len(fastsimon_data)} characters")
                    
                    # Look for the items array
                    items_match = re.search(r'"items":\s*(\[[^\]]+\])', fastsimon_data)
                    if items_match:
                        items_str = items_match.group(1)
                        logger.info(f"Found items array: {len(items_str)} characters")
                        
                        # Parse each item individually - look for the basic structure
                        # Each item starts with {"l":"title","c":"currency","u":"url","p":"price"
                        # Try multiple patterns to catch different item formats
                        item_patterns = [
                            r'\{"l":"([^"]+)","c":"([^"]+)","u":"([^"]+)","p":"([^"]+)"[^}]*"t":"([^"]+)"',
                            r'\{"l":"([^"]+)","c":"([^"]+)","u":"([^"]+)","p":"([^"]+)"',
                            r'\{"l":"([^"]+)","p":"([^"]+)"[^}]*"u":"([^"]+)"[^}]*"t":"([^"]+)"'
                        ]
                        
                        item_matches = []
                        for pattern in item_patterns:
                            matches = re.findall(pattern, items_str)
                            if matches:
                                item_matches = matches
                                logger.info(f"Found {len(item_matches)} item matches with pattern: {pattern[:50]}...")
                                break
                        
                        for item_match in item_matches[:limit]:
                            try:
                                # Handle different pattern formats
                                if len(item_match) == 5:  # Full pattern: title, currency, url, price, image
                                    title, currency, url, price, image = item_match
                                elif len(item_match) == 4:  # Pattern without image: title, currency, url, price
                                    title, currency, url, price = item_match
                                    image = ''
                                elif len(item_match) == 4:  # Alternative pattern: title, price, url, image
                                    title, price, url, image = item_match
                                else:
                                    logger.debug(f"Skipping item with {len(item_match)} fields: {item_match}")
                                    continue
                                
                                if title and price:
                                    # Enhanced product data extraction (sync version)
                                    product = self._enhance_product_data_sync({
                                        'title': title,
                                        'price': f"₡{price}",
                                        'product_url': urljoin(self.base_url, url) if url else '',
                                        'image_url': image if image else '',
                                        'source': 'unimart',
                                        'currency': currency if len(item_match) >= 4 else 'CRC',
                                        'raw_price': price
                                    })
                                    
                                    products.append(product)
                                    logger.debug(f"Extracted product: {product['title'][:30]}... - {product['price']}")
                                    
                            except Exception as e:
                                logger.debug(f"Error parsing individual item: {e}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error parsing FastSimon data: {e}")
            
            # If FastSimon didn't work, try to find other JavaScript data
            if not products:
                # Look for any JSON-like product data
                json_patterns = [
                    r'"products":\s*(\[[^\]]+\])',
                    r'"items":\s*(\[[^\]]+\])',
                    r'"results":\s*(\[[^\]]+\])'
                ]
                
                for pattern in json_patterns:
                    json_match = re.search(pattern, html_content)
                    if json_match:
                        try:
                            # Try to extract basic product info
                            products.extend(self._extract_basic_product_info(json_match.group(1), limit))
                            if products:
                                break
                        except Exception as e:
                            logger.debug(f"Error with JSON pattern {pattern}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error extracting from JavaScript data: {e}")
        
        return products

    def _extract_basic_product_info(self, json_str: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract basic product information from JSON-like strings
        """
        products = []
        
        try:
            # Look for product-like patterns in the string
            # This is a fallback method that doesn't require full JSON parsing
            
            # Find product blocks
            product_blocks = re.findall(r'\{[^}]+\}', json_str)
            
            for block in product_blocks[:limit]:
                try:
                    # Extract basic fields
                    title_match = re.search(r'"title":\s*"([^"]+)"', block)
                    price_match = re.search(r'"price":\s*\{[^}]*"amount":\s*"([^"]+)"', block)
                    url_match = re.search(r'"url":\s*"([^"]+)"', block)
                    image_match = re.search(r'"image":\s*"([^"]+)"', block)
                    
                    if title_match and price_match:
                        product = {
                            'title': title_match.group(1),
                            'price': f"₡{price_match.group(1)}",
                            'product_url': urljoin(self.base_url, url_match.group(1)) if url_match else '',
                            'image_url': image_match.group(1) if image_match else '',
                            'source': 'unimart'
                        }
                        products.append(product)
                        
                except Exception as e:
                    logger.debug(f"Error parsing product block: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error in basic product info extraction: {e}")
        
        return products

    def _extract_products_from_page_structure(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """
        Extract products by analyzing the page structure and looking for patterns
        """
        products = []
        
        try:
            # Look for any elements that contain both price and product-like text
            # This is a more flexible approach for sites with complex structures
            
            # Find all elements that might contain product info
            potential_containers = soup.find_all(['div', 'article', 'li', 'section'], limit=limit*5)
            
            for container in potential_containers:
                text_content = container.get_text()
                
                # Skip if too short or too long
                if len(text_content) < 20 or len(text_content) > 1000:
                    continue
                
                # Look for price patterns (Costa Rican colones or dollars)
                price_match = re.search(r'[₡$]?([\d,]+(?:\.\d{2})?)', text_content)
                if not price_match:
                    continue
                
                # Look for product indicators
                product_indicators = [
                    'smartwatch', 'watch', 'phone', 'celular', 'laptop', 'tablet',
                    'headphone', 'audífono', 'camera', 'cámara', 'tv', 'televisor'
                ]
                
                has_product = any(indicator in text_content.lower() for indicator in product_indicators)
                if not has_product:
                    continue
                
                # Try to extract a reasonable title
                title = self._extract_title_from_text(text_content)
                if not title:
                    continue
                
                # Create product object
                product = {
                    'title': title,
                    'price': f"₡{price_match.group(1)}" if '₡' in text_content else f"${price_match.group(1)}",
                    'image_url': '',
                    'product_url': '',
                    'source': 'unimart'
                }
                
                # Try to find image and URL in the container
                img_elem = container.find('img')
                if img_elem:
                    img_src = img_elem.get('src') or img_elem.get('data-src')
                    if img_src:
                        product['image_url'] = img_src if img_src.startswith('http') else urljoin(self.base_url, img_src)
                
                link_elem = container.find('a')
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        product['product_url'] = href if href.startswith('http') else urljoin(self.base_url, href)
                
                products.append(product)
                
                if len(products) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Error in page structure extraction: {e}")
        
        return products

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """
        Extract a reasonable product title from text content
        """
        try:
            # Clean the text
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Look for patterns that look like product names
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 10 and len(line) < 100:
                    # Check if it looks like a product name
                    if any(keyword in line.lower() for keyword in ['smartwatch', 'watch', 'phone', 'laptop', 'tablet']):
                        return line
            
            # If no specific pattern found, try to get a reasonable length line
            for line in lines:
                line = line.strip()
                if 15 <= len(line) <= 80:
                    return line
                    
        except Exception as e:
            logger.debug(f"Error extracting title: {e}")
        
        return None

    def _enhance_product_data_sync(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance product data with additional information and standardize format
        """
        try:
            # Extract brand from title
            brand = self._extract_brand(product['title'])
            
            # Categorize product
            category = self._categorize_product(product['title'])
            
            # Extract specifications
            specs = self._extract_specifications(product['title'])
            
            # Standardize pricing
            price_info = self._standardize_pricing(product['raw_price'], product['currency'])
            
            # Enhanced product object
            enhanced_product = {
                **product,
                'brand': brand,
                'category': category,
                'specifications': specs,
                'price_info': price_info,
                'availability': 'in_stock',  # Assume in stock if listed
                'rating': None,  # Will be extracted if available
                'description': self._generate_description(product['title'], brand, specs),
                'tags': self._generate_tags(product['title'], brand, category),
                'seo_title': self._generate_seo_title(product['title'], brand),
                'condition': 'new'
            }
            
            return enhanced_product
            
        except Exception as e:
            logger.debug(f"Error enhancing product data: {e}")
            return product

    def _extract_brand(self, title: str) -> str:
        """Extract brand from product title"""
        # Common brands in Costa Rica electronics market
        brands = [
            'Samsung', 'Apple', 'Xiaomi', 'Huawei', 'Garmin', 'Miomu', 
            'Hifuture', 'Amazfit', 'Haylou', 'Mibro', 'Cubitt', 'Argom',
            'Case Logic', 'Belkin', 'Anker', 'JBL', 'Sony', 'LG', 'HP',
            'Dell', 'Lenovo', 'Asus', 'Acer', 'Canon', 'Nikon', 'GoPro'
        ]
        
        title_upper = title.upper()
        for brand in brands:
            if brand.upper() in title_upper:
                return brand
        
        # Try to extract first word as potential brand
        words = title.split()
        if words and len(words[0]) > 2:
            return words[0].title()
        
        return 'Generic'

    def _categorize_product(self, title: str) -> str:
        """Categorize product based on title"""
        title_lower = title.lower()
        
        categories = {
            'smartwatch': ['smartwatch', 'reloj inteligente', 'smart watch', 'watch'],
            'phone_accessory': ['case', 'funda', 'protector', 'cable', 'cargador', 'charger'],
            'audio': ['audífono', 'headphone', 'speaker', 'parlante', 'earphone'],
            'computer': ['laptop', 'desktop', 'monitor', 'teclado', 'mouse', 'keyboard'],
            'tablet': ['tablet', 'ipad'],
            'camera': ['cámara', 'camera', 'gopro'],
            'gaming': ['gaming', 'game', 'console', 'joystick'],
            'home': ['smart home', 'casa inteligente', 'alexa', 'google home'],
            'fitness': ['fitness', 'deportivo', 'sport', 'exercise'],
            'electronics': ['electronic', 'electrónico', 'tech', 'tecnología']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'electronics'

    def _extract_specifications(self, title: str) -> Dict[str, str]:
        """Extract technical specifications from title"""
        specs = {}
        
        # Screen size
        screen_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:inch|pulgada|")', title, re.IGNORECASE)
        if screen_match:
            specs['screen_size'] = f"{screen_match.group(1)}\""
        
        # Storage capacity
        storage_match = re.search(r'(\d+)\s*(GB|TB)', title, re.IGNORECASE)
        if storage_match:
            specs['storage'] = f"{storage_match.group(1)}{storage_match.group(2)}"
        
        # RAM
        ram_match = re.search(r'(\d+)\s*GB\s*RAM', title, re.IGNORECASE)
        if ram_match:
            specs['ram'] = f"{ram_match.group(1)}GB"
        
        # Color
        colors = ['negro', 'black', 'blanco', 'white', 'azul', 'blue', 'rojo', 'red', 
                 'verde', 'green', 'rosa', 'pink', 'gris', 'gray', 'dorado', 'gold']
        for color in colors:
            if color in title.lower():
                specs['color'] = color.title()
                break
        
        # Connectivity
        if any(conn in title.lower() for conn in ['wifi', 'bluetooth', '5g', '4g', 'lte']):
            connectivity = []
            if 'wifi' in title.lower():
                connectivity.append('WiFi')
            if 'bluetooth' in title.lower():
                connectivity.append('Bluetooth')
            if '5g' in title.lower():
                connectivity.append('5G')
            elif '4g' in title.lower() or 'lte' in title.lower():
                connectivity.append('4G LTE')
            specs['connectivity'] = ', '.join(connectivity)
        
        return specs

    def _standardize_pricing(self, raw_price: str, currency: str) -> Dict[str, Any]:
        """Standardize pricing information"""
        try:
            # Clean price string
            price_clean = re.sub(r'[^\d.]', '', raw_price)
            price_float = float(price_clean)
            
            # Convert to USD (approximate rate: 1 USD = 500 CRC)
            if currency == 'CRC':
                price_usd = round(price_float / 500, 2)
            else:
                price_usd = price_float
            
            return {
                'original_price': price_float,
                'original_currency': currency,
                'usd_price': price_usd,
                'formatted_crc': f"₡{price_float:,.0f}",
                'formatted_usd': f"${price_usd:.2f}"
            }
        except:
            return {
                'original_price': 0,
                'original_currency': currency,
                'usd_price': 0,
                'formatted_crc': f"₡{raw_price}",
                'formatted_usd': 'Contact for price'
            }

    def _generate_description(self, title: str, brand: str, specs: Dict[str, str]) -> str:
        """Generate product description for rebranding"""
        description_parts = [f"Discover the {title} from {brand}."]
        
        if specs.get('screen_size'):
            description_parts.append(f"Features a {specs['screen_size']} display.")
        
        if specs.get('storage'):
            description_parts.append(f"Comes with {specs['storage']} of storage.")
        
        if specs.get('connectivity'):
            description_parts.append(f"Supports {specs['connectivity']} connectivity.")
        
        description_parts.append("Available now in Costa Rica with fast shipping.")
        description_parts.append("Perfect for tech enthusiasts and everyday users alike.")
        
        return " ".join(description_parts)

    def _generate_tags(self, title: str, brand: str, category: str) -> List[str]:
        """Generate tags for product categorization"""
        tags = [brand.lower(), category]
        
        # Add common tags based on category
        category_tags = {
            'smartwatch': ['wearable', 'fitness', 'health', 'smart', 'watch'],
            'phone_accessory': ['mobile', 'phone', 'accessory', 'protection'],
            'audio': ['sound', 'music', 'audio', 'entertainment'],
            'computer': ['pc', 'computing', 'work', 'productivity'],
            'electronics': ['tech', 'gadget', 'electronic']
        }
        
        if category in category_tags:
            tags.extend(category_tags[category])
        
        # Add tags from title
        title_words = re.findall(r'\w+', title.lower())
        relevant_words = [word for word in title_words if len(word) > 3 and word not in ['para', 'con', 'the', 'and', 'with']]
        tags.extend(relevant_words[:5])
        
        return list(set(tags))  # Remove duplicates

    def _generate_seo_title(self, title: str, brand: str) -> str:
        """Generate SEO-optimized title"""
        # Clean title and add brand if not present
        clean_title = title.strip()
        if brand.lower() not in clean_title.lower():
            clean_title = f"{brand} {clean_title}"
        
        # Add location for local SEO
        if 'costa rica' not in clean_title.lower():
            clean_title += " - Costa Rica"
        
        return clean_title[:60]  # SEO title length limit


async def test_unimart_client():
    """
    Test the Unimart client
    """
    client = UnimartClient()
    
    # Test 1: Search for products
    logger.info("🧪 Testing Unimart search...")
    search_terms = ['smartwatch', 'phone case', 'laptop']
    
    for term in search_terms:
        logger.info(f"🔍 Testing search for: {term}")
        products = await client.get_products(term, limit=3)
        
        if products:
            logger.info(f"✅ Found {len(products)} products for '{term}'")
            for i, product in enumerate(products, 1):
                logger.info(f"  {i}. {product.get('title', 'No title')[:50]}... - {product.get('price', 'N/A')}")
        else:
            logger.warning(f"⚠️ No products found for '{term}'")
        
        await asyncio.sleep(1)
    
    # Test 2: Get smartwatches from collection
    logger.info("\n🧪 Testing Unimart smartwatch collection...")
    smartwatches = await client.get_smartwatches(limit=5)
    
    if smartwatches:
        logger.info(f"✅ Found {len(smartwatches)} smartwatches")
        for i, watch in enumerate(smartwatches, 1):
            logger.info(f"  {i}. {watch.get('title', 'No title')[:50]}... - {watch.get('price', 'N/A')}")
    else:
        logger.warning("⚠️ No smartwatches found in collection")

    # Test enhanced product data extraction
    logger.info("\n🧪 Testing enhanced product data extraction...")
    enhanced_products = await client.get_products("smartwatch", limit=2)
    
    if enhanced_products:
        logger.info(f"✅ Found {len(enhanced_products)} enhanced products")
        for i, product in enumerate(enhanced_products, 1):
            logger.info(f"\n📱 Product {i}: {product.get('seo_title', 'No title')}")
            logger.info(f"   Brand: {product.get('brand', 'N/A')}")
            logger.info(f"   Category: {product.get('category', 'N/A')}")
            logger.info(f"   Price: {product.get('price_info', {}).get('formatted_crc', 'N/A')} ({product.get('price_info', {}).get('formatted_usd', 'N/A')})")
            logger.info(f"   Specs: {product.get('specifications', {})}")
            logger.info(f"   Tags: {', '.join(product.get('tags', [])[:5])}")
            logger.info(f"   Description: {product.get('description', 'N/A')[:100]}...")
    else:
        logger.warning("⚠️ No enhanced products found")


def create_shaymee_product_listing(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Shaymee-branded product listing from Unimart data
    """
    return {
        'id': f"shaymee_{hash(product.get('product_url', ''))}", 
        'title': product.get('seo_title', product.get('title', 'Product')),
        'brand': product.get('brand', 'Generic'),
        'category': product.get('category', 'electronics'),
        'description': product.get('description', ''),
        'price': {
            'crc': product.get('price_info', {}).get('formatted_crc', 'Contact for price'),
            'usd': product.get('price_info', {}).get('formatted_usd', 'Contact for price'),
            'original': product.get('price_info', {}).get('original_price', 0)
        },
        'images': [product.get('image_url', '')] if product.get('image_url') else [],
        'specifications': product.get('specifications', {}),
        'availability': product.get('availability', 'in_stock'),
        'condition': product.get('condition', 'new'),
        'tags': product.get('tags', []),
        'source': {
            'name': 'Unimart',
            'url': product.get('product_url', ''),
            'local': True,
            'country': 'Costa Rica'
        },
        'seo': {
            'title': product.get('seo_title', ''),
            'keywords': ', '.join(product.get('tags', [])[:10])
        },
        'shaymee_enhanced': True,
        'created_at': datetime.now().isoformat(),
        'rating': product.get('rating', None)
    }


async def test_shaymee_rebranding():
    """
    Test the Shaymee rebranding system
    """
    logger.info("🔄 Testing Shaymee Product Rebranding...")
    
    client = UnimartClient()
    raw_products = await client.get_products("smartwatch", limit=3)
    
    if raw_products:
        logger.info(f"📦 Converting {len(raw_products)} products to Shaymee format...")
        
        shaymee_products = []
        for product in raw_products:
            shaymee_product = create_shaymee_product_listing(product)
            shaymee_products.append(shaymee_product)
            
            # Display rebranded product
            logger.info(f"\n🏷️  Shaymee Product: {shaymee_product['title']}")
            logger.info(f"   ID: {shaymee_product['id']}")
            logger.info(f"   Brand: {shaymee_product['brand']} | Category: {shaymee_product['category']}")
            logger.info(f"   Price: {shaymee_product['price']['crc']} ({shaymee_product['price']['usd']})")
            logger.info(f"   Source: {shaymee_product['source']['name']} ({shaymee_product['source']['country']})")
            logger.info(f"   SEO Title: {shaymee_product['seo']['title']}")
            logger.info(f"   Tags: {', '.join(shaymee_product['tags'][:5])}")
        
        logger.info(f"\n✅ Successfully rebranded {len(shaymee_products)} products for Shaymee!")
        return shaymee_products
    else:
        logger.warning("⚠️ No products to rebrand")
        return []


if __name__ == "__main__":
    asyncio.run(test_unimart_client())
    print("\n" + "="*50)
    asyncio.run(test_shaymee_rebranding())
