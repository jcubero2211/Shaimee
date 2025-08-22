import asyncio
import os
from loguru import logger
from playwright.async_api import async_playwright

async def manual_temu_test():
    """
    Manual test to observe Temu's search flow and identify any workarounds
    """
    # Create a persistent user data directory to make it look like a regular browser
    user_data_dir = os.path.expanduser("~/temu-browser-data")
    os.makedirs(user_data_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch Chrome in persistent context mode to avoid incognito-like behavior
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # Visible browser
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',  # Disable extensions that might look suspicious
                '--no-first-run',  # Skip first run setup
                '--no-default-browser-check',  # Skip default browser check
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ],
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Costa_Rica'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to Temu homepage
            logger.info("Navigating to Temu homepage...")
            await page.goto('https://www.temu.com', wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # Take screenshot of homepage
            await page.screenshot(path='temu_homepage.png')
            logger.info("Screenshot saved: temu_homepage.png")
            
            # Try to find search box
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="search"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="buscar"]',
                '.search-input',
                '#search-input',
                '[data-testid="search-input"]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        logger.info(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # Highlight the search box
                await search_input.evaluate('el => el.style.border = "3px solid red"')
                await page.wait_for_timeout(1000)
                
                # Take screenshot with highlighted search box
                await page.screenshot(path='temu_search_highlighted.png')
                logger.info("Screenshot saved: temu_search_highlighted.png")
                
                # Try to type in search box
                await search_input.click()
                await search_input.fill('phone case')
                await page.wait_for_timeout(1000)
                
                # Try to submit search
                try:
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(3000)
                    
                    # Take screenshot of search results
                    await page.screenshot(path='temu_search_results.png')
                    logger.info("Screenshot saved: temu_search_results.png")
                    
                    # Save HTML content for analysis
                    html_content = await page.content()
                    with open('temu_search_results.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info("HTML content saved: temu_search_results.html")
                    
                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    await page.screenshot(path='temu_search_error.png')
                    logger.info("Error screenshot saved: temu_search_error.png")
            else:
                logger.warning("No search input found")
                await page.screenshot(path='temu_no_search.png')
                logger.info("Screenshot saved: temu_no_search.png")
            
            # Keep browser open for manual testing
            logger.info("Browser will stay open for 5 minutes for manual testing...")
            await page.wait_for_timeout(300000)  # 5 minutes
            
        except Exception as e:
            logger.error(f"Error during manual test: {e}")
            await page.screenshot(path='temu_error.png')
            logger.info("Error screenshot saved: temu_error.png")
        
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(manual_temu_test())
