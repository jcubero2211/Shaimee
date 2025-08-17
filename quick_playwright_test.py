#!/usr/bin/env python3
"""
Quick Playwright test with shorter timeouts to see what's actually happening
"""

import asyncio
from playwright.async_api import async_playwright

async def quick_test():
    """Quick test to see what the site shows"""
    
    print("🎭 QUICK PLAYWRIGHT TEST")
    print("="*30)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("📡 Going to homepage first...")
            await page.goto("https://tienda.pequenomundo.com/", timeout=10000)
            await page.wait_for_timeout(2000)
            
            title = await page.title()
            print(f"📝 Homepage title: {title}")
            
            # Take screenshot of homepage
            await page.screenshot(path='homepage_test.png')
            print("📸 Homepage screenshot: homepage_test.png")
            
            print("\\n🔍 Now trying search...")
            await page.goto("https://tienda.pequenomundo.com/catalogsearch/result/?q=juguetes", timeout=10000)
            await page.wait_for_timeout(3000)
            
            search_title = await page.title()
            print(f"📝 Search page title: {search_title}")
            
            # Take screenshot of search page
            await page.screenshot(path='search_test.png')
            print("📸 Search screenshot: search_test.png")
            
            # Check content
            content = await page.content()
            print(f"📄 Content length: {len(content)} chars")
            
            if "Just a moment" in content:
                print("⚠️  Cloudflare challenge detected")
            elif "product" in content.lower():
                print("✅ Found product content!")
            elif "sin resultados" in content.lower():
                print("📭 No results message")
            else:
                print("🤔 Unknown content type")
                
        except Exception as e:
            print(f"💥 Error: {e}")
            # Take final screenshot
            await page.screenshot(path='error_final.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(quick_test())
