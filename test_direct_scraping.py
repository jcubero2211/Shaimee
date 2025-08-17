#!/usr/bin/env python3
"""
Test direct scraping from Pequeño Mundo without proxy
Handle Cloudflare protection and see if we can get real product data
"""

import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup
from loguru import logger

class DirectScraperTest:
    def __init__(self):
        self.timeout = 30000  # 30 seconds
        
    async def test_direct_access(self, search_term: str = "juguetes"):
        """Test direct access to Pequeño Mundo"""
        
        search_url = f"https://tienda.pequenomundo.com/catalogsearch/result/?q={search_term.replace(' ', '%20')}"
        logger.info(f"🔍 Testing direct access to: {search_url}")
        
        # More comprehensive browser headers to avoid detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-CR,es;q=0.9,es-419;q=0.8,en;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # Session cookies
        cookies = {
            'store': 'default',
            'currency': 'CRC',
        }
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout/1000)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                logger.info("📡 Making request...")
                
                async with session.get(
                    search_url,
                    headers=headers,
                    cookies=cookies,
                    timeout=timeout,
                    allow_redirects=True
                ) as response:
                    
                    status = response.status
                    content = await response.text()
                    
                    logger.info(f"📊 Status: {status}")
                    logger.info(f"📄 Content length: {len(content)} chars")
                    
                    # Save for debugging
                    with open(f'direct_test_{search_term}.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Check what we got
                    if "Just a moment" in content and "Cloudflare" in content:
                        logger.warning("⚠️  Cloudflare challenge detected")
                        return "cloudflare_challenge"
                    elif "tienda.pequenomundo.com" in content and len(content) > 50000:
                        logger.success("✅ Got substantial content from site")
                        return await self._analyze_content(content, search_term)
                    elif status == 403:
                        logger.error("🚫 403 Forbidden - IP blocked")
                        return "blocked"
                    else:
                        logger.warning(f"🤔 Unexpected content (status: {status})")
                        return "unknown"
                        
        except Exception as e:
            logger.error(f"💥 Error: {e}")
            return "error"
    
    async def _analyze_content(self, html_content: str, search_term: str):
        """Analyze the content we received"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check page title
            title = soup.find('title')
            if title:
                logger.info(f"📝 Page title: {title.text}")
            
            # Look for products
            product_containers = soup.select('.product-item')
            if product_containers:
                logger.success(f"🎉 Found {len(product_containers)} products!")
                
                # Extract first product as example
                first_product = product_containers[0]
                
                # Title
                title_elem = (first_product.select_one('.product-name a') or 
                            first_product.select_one('.product-item-name a') or
                            first_product.find('a'))
                product_title = title_elem.text.strip() if title_elem else "No title"
                
                # Price
                price_elem = first_product.select_one('.price')
                product_price = price_elem.text.strip() if price_elem else "No price"
                
                logger.info(f"📦 Sample product: {product_title}")
                logger.info(f"💰 Sample price: {product_price}")
                
                return {
                    'status': 'success',
                    'product_count': len(product_containers),
                    'sample_title': product_title,
                    'sample_price': product_price
                }
            else:
                logger.warning("😞 No products found in HTML")
                
                # Check for no results message
                if "no results" in html_content.lower() or "sin resultados" in html_content.lower():
                    logger.info(f"📭 No results for '{search_term}'")
                    return {'status': 'no_results', 'search_term': search_term}
                else:
                    logger.warning("🤔 Page structure might be different")
                    return {'status': 'no_products_found'}
                    
        except Exception as e:
            logger.error(f"💥 Error analyzing content: {e}")
            return {'status': 'analysis_error', 'error': str(e)}

async def main():
    """Run direct scraping test"""
    print("🧪 TESTING DIRECT SCRAPING (NO PROXY)")
    print("="*50)
    
    tester = DirectScraperTest()
    
    # Test different search terms
    search_terms = ["juguetes", "reloj", "hogar"]
    
    for term in search_terms:
        print(f"\n🔍 Testing: '{term}'")
        print("-"*30)
        
        result = await tester.test_direct_access(term)
        
        if isinstance(result, dict) and result.get('status') == 'success':
            print(f"✅ SUCCESS: Found {result['product_count']} products")
            print(f"📦 Sample: {result['sample_title']}")
            print(f"💰 Price: {result['sample_price']}")
        else:
            print(f"❌ Result: {result}")
        
        # Small delay between requests
        await asyncio.sleep(2)
    
    print(f"\n💡 TIP: Check generated HTML files for debugging")
    print("📁 Files: direct_test_*.html")

if __name__ == "__main__":
    asyncio.run(main())
