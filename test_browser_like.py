#!/usr/bin/env python3
"""
Test browser-like scraping that can handle JavaScript challenges
"""

import asyncio
import time
from requests_html import AsyncHTMLSession
from loguru import logger

async def test_browser_like_scraping():
    """Test with requests-html that renders JavaScript"""
    
    print("🌐 Testing Browser-Like Scraping with JavaScript Rendering")
    print("="*60)
    
    # Create session that can render JavaScript
    session = AsyncHTMLSession()
    
    # Set realistic browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-CR,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    })
    
    urls_to_test = [
        ("homepage", "https://tienda.pequenomundo.com/"),
        ("juguetes", "https://tienda.pequenomundo.com/catalogsearch/result/?q=juguetes"),
        ("reloj", "https://tienda.pequenomundo.com/catalogsearch/result/?q=reloj")
    ]
    
    for name, url in urls_to_test:
        try:
            print(f"\n🔍 Testing: {name}")
            print("-" * 30)
            
            logger.info(f"Fetching: {url}")
            
            # Get the page
            r = await session.get(url)
            
            print(f"📊 Status: {r.status_code}")
            print(f"📄 Content length: {len(r.text)} chars")
            
            # Check for Cloudflare challenge
            if "Just a moment" in r.text and "cf-mitigated" in r.text:
                print("⚠️  Cloudflare challenge detected - trying JavaScript rendering...")
                
                # Render JavaScript (this can handle Cloudflare challenges)
                await r.html.arender(wait=3, timeout=15)
                
                print(f"📄 After JS render: {len(r.html.text)} chars")
                
                # Save rendered content
                with open(f'browser_like_{name}.html', 'w', encoding='utf-8') as f:
                    f.write(r.html.html)
                
                # Check if we now have real content
                if "tienda.pequenomundo.com" in r.html.html and len(r.html.html) > 50000:
                    print("✅ Successfully bypassed Cloudflare!")
                    
                    # Look for products
                    products = r.html.find('.product-item')
                    if products:
                        print(f"🎉 Found {len(products)} products!")
                        
                        # Get first product details
                        first = products[0]
                        title_elem = first.find('a', first=True)
                        price_elem = first.find('.price', first=True)
                        
                        title = title_elem.text if title_elem else "No title"
                        price = price_elem.text if price_elem else "No price"
                        
                        print(f"📦 Sample product: {title[:50]}")
                        print(f"💰 Sample price: {price}")
                        
                        return True
                    else:
                        print("😞 No products found")
                else:
                    print("❌ Still blocked after JS rendering")
            
            elif r.status_code == 200 and "tienda.pequenomundo.com" in r.text:
                print("✅ Direct access successful!")
                
                # Save content
                with open(f'browser_like_{name}.html', 'w', encoding='utf-8') as f:
                    f.write(r.text)
                
                # Parse for products
                products = r.html.find('.product-item')
                if products:
                    print(f"🎉 Found {len(products)} products directly!")
                    return True
                else:
                    print("📭 No products found (might be no results)")
            
            else:
                print(f"❌ Failed: Status {r.status_code}")
            
            # Small delay between requests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"💥 Error testing {name}: {e}")
            continue
    
    return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_browser_like_scraping())
        
        if result:
            print(f"\n🎉 SUCCESS! Browser-like scraping worked!")
            print(f"💡 Check browser_like_*.html files for scraped content")
        else:
            print(f"\n😞 All methods failed - true geo-blocking or advanced protection")
            
    except ImportError:
        print("❌ requests-html not installed. Install with:")
        print("pip install requests-html")
    except Exception as e:
        print(f"💥 Error: {e}")
