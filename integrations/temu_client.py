import asyncio
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from undetected_playwright import Malenia

load_dotenv()  # Load environment variables from .env file

class TemuClient:
    def __init__(self, timeout: int = 90000): # Timeout in milliseconds
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")
        self.proxy_host = os.getenv("PROXY_HOST")
        self.proxy_port = os.getenv("PROXY_PORT")

        if not all([self.proxy_user, self.proxy_pass, self.proxy_host, self.proxy_port]):
            raise ValueError("Proxy credentials not fully set in environment variables.")

        self.timeout = timeout

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        logger.info(f"Starting Playwright scraper for search term: '{search_term}'")
        search_url = f"https://www.temu.com/search_result.html?search_key={search_term.replace(' ', '%20')}"

        max_retries = 5
        for attempt in range(max_retries):
            logger.info(f"Scraper attempt {attempt + 1} of {max_retries}...")
            browser = None
            async with async_playwright() as p:
                try:
                    browser = await p.chromium.launch(headless=False)
                    context = await browser.new_context(
                        proxy={
                            "server": f"http://{self.proxy_host}:{self.proxy_port}",
                            "username": self.proxy_user,
                            "password": self.proxy_pass
                        },
                        ignore_https_errors=True,
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                        viewport={'width': 1920, 'height': 1080}
                    )
                    await Malenia.apply_stealth(context)
                    page = await context.new_page()

                    logger.info(f"Navigating to: {search_url}")
                    await page.goto(search_url, timeout=self.timeout)

                    product_selector = "div[data-qa-gallery-type='list-gallery'] > div"
                    logger.info(f"Waiting for product selector: '{product_selector}'")
                    await page.wait_for_selector(product_selector, timeout=30000)

                    product_elements = await page.query_selector_all(product_selector)
                    logger.info(f"Found {len(product_elements)} product elements on the page.")

                    if not product_elements:
                        logger.warning("No product elements found. The layout may have changed.")
                        await browser.close()
                        continue # Try next attempt

                    products = []
                    for element in product_elements[:limit]:
                        try:
                            title_element = await element.query_selector('p._x_line-clamp-2')
                            title = await title_element.inner_text() if title_element else 'N/A'

                            price_element = await element.query_selector('div[data-qa-id="ad-price"]')
                            price = await price_element.inner_text() if price_element else 'N/A'

                            image_element = await element.query_selector('img.w-full')
                            image_url = await image_element.get_attribute('src') if image_element else 'N/A'

                            link_element = await element.query_selector('a')
                            product_url = await link_element.get_attribute('href') if link_element else '#'
                            if product_url and not product_url.startswith('http'):
                                product_url = f"https://www.temu.com{product_url}"

                            products.append({"title": title.strip(), "price": price.strip(), "imageUrl": image_url, "productUrl": product_url})
                        except Exception as item_error:
                            logger.error(f"Error extracting details for a product: {item_error}")
                            continue

                    logger.info(f"Successfully scraped {len(products)} products.")
                    await browser.close()
                    return products # Success!

                except PlaywrightTimeoutError:
                    logger.error(f"Attempt {attempt + 1} timed out. Temu may be blocking the request.")
                    if 'page' in locals() and not page.is_closed():
                        try:
                            await page.screenshot(path='debug_screenshot.png', full_page=True)
                            logger.info("Saved debug screenshot to 'debug_screenshot.png'")
                        except Exception as ss_error:
                            logger.error(f"Could not take screenshot: {ss_error}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred on attempt {attempt + 1}: {e}")
                finally:
                    if browser:
                        await browser.close()
            
            logger.warning(f"Attempt {attempt + 1} failed. Retrying with a new proxy IP...")

        logger.error("Scraper failed after all retry attempts.")
        return None
