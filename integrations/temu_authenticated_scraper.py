import asyncio
import random
import time
from typing import Any, Dict, List, Optional
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from undetected_playwright import Malenia

class TemuAuthenticatedScraper:
    def __init__(self, timeout: int = 90000):
        self.timeout = timeout
        
        # Temu credentials from the screenshot
        self.email = "shaimee19721976@gmail.com"
        self.password = "Vp25077200Jc22117600"
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Authenticated product scraping from Temu
        """
        logger.info(f"🔐 Starting authenticated Temu scraper for: '{search_term}'")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # Visible for debugging
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={'width': 1920, 'height': 1080},
                    locale='es-ES',  # Spanish locale for Costa Rica
                    timezone_id='America/Costa_Rica',
                    ignore_https_errors=True
                )
                
                # Apply stealth
                await Malenia.apply_stealth(context)
                page = await context.new_page()
                
                # Step 1: Go to Temu homepage
                logger.info("🏠 Step 1: Going to Temu homepage...")
                await page.goto("https://www.temu.com", timeout=30000)
                await page.wait_for_timeout(random.uniform(3000, 5000))
                
                # Take screenshot of homepage
                await page.screenshot(path='step1_homepage.png')
                logger.info("📸 Homepage screenshot saved")
                
                # Step 2: Handle login/registration
                logger.info("🔐 Step 2: Handling authentication...")
                await self._handle_authentication(page)
                
                # Step 3: Navigate to search
                logger.info("🔍 Step 3: Navigating to search...")
                await self._navigate_to_search(page, search_term)
                
                # Step 4: Extract products
                logger.info("📦 Step 4: Extracting products...")
                products = await self._extract_products(page, limit)
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"💥 Authenticated scraping failed: {e}")
            return None

    async def _handle_authentication(self, page):
        """Handle the two-step login/registration process"""
        try:
            # Wait for the page to load
            await page.wait_for_timeout(3000)
            
            # Check if we're already logged in
            if await self._is_logged_in(page):
                logger.info("✅ Already logged in")
                return
            
            # Step 1: Handle email/phone input
            logger.info("📧 Step 1: Entering email/phone...")
            
            # Look for email/phone input field
            email_selectors = [
                'input[type="email"]',
                'input[type="tel"]',
                'input[placeholder*="email"]',
                'input[placeholder*="teléfono"]',
                'input[placeholder*="phone"]',
                'input[name="email"]',
                'input[name="phone"]',
                'input[aria-label*="email"]',
                'input[aria-label*="teléfono"]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await page.wait_for_selector(selector, timeout=2000)
                    if email_field:
                        logger.info(f"✅ Found email/phone field with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                # Try to find any input field that might be for email/phone
                try:
                    email_field = await page.wait_for_selector('input', timeout=5000)
                    logger.info("✅ Found generic input field")
                except:
                    logger.error("❌ No email/phone field found")
                    return
            
            if email_field:
                # Clear and fill email
                await email_field.click()
                await email_field.fill("")
                await page.wait_for_timeout(500)
                await email_field.type(self.email)
                await page.wait_for_timeout(1000)
                
                # Look for "Continuar" (Continue) button
                continue_selectors = [
                    'button:has-text("Continuar")',
                    'button:has-text("Continue")',
                    'button[type="submit"]',
                    '.continue-btn',
                    '.submit-btn'
                ]
                
                continue_button = None
                for selector in continue_selectors:
                    try:
                        continue_button = await page.wait_for_selector(selector, timeout=3000)
                        if continue_button:
                            logger.info(f"✅ Found continue button with selector: {selector}")
                            break
                    except:
                        continue
                
                if continue_button:
                    logger.info("🔄 Clicking continue button...")
                    await continue_button.click()
                    await page.wait_for_timeout(random.uniform(3000, 5000))
                    
                    # Take screenshot after first step
                    await page.screenshot(path='step2_after_email.png')
                    logger.info("📸 Post-email screenshot saved")
                    
                    # Step 2: Handle password input (if it appears)
                    await self._handle_password_step(page)
                else:
                    logger.warning("⚠️ No continue button found")
            else:
                logger.error("❌ Could not find email/phone field")
                
        except Exception as e:
            logger.error(f"💥 Authentication handling failed: {e}")

    async def _handle_password_step(self, page):
        """Handle the password input step after email/phone"""
        try:
            logger.info("🔐 Step 2: Handling password input...")
            
            # Wait for password field to appear
            await page.wait_for_timeout(2000)
            
            # Look for password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password"]',
                'input[placeholder*="contraseña"]',
                'input[aria-label*="password"]',
                'input[aria-label*="contraseña"]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=3000)
                    if password_field:
                        logger.info(f"✅ Found password field with selector: {selector}")
                        break
                except:
                    continue
            
            if password_field:
                # Clear and fill password
                await password_field.click()
                await password_field.fill("")
                await page.wait_for_timeout(500)
                await password_field.type(self.password)
                await page.wait_for_timeout(1000)
                
                # Look for login/register button
                login_selectors = [
                    'button:has-text("Iniciar sesión")',
                    'button:has-text("Registrarse")',
                    'button:has-text("Login")',
                    'button:has-text("Register")',
                    'button[type="submit"]',
                    '.login-btn',
                    '.register-btn',
                    '.submit-btn'
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = await page.wait_for_selector(selector, timeout=3000)
                        if login_button:
                            logger.info(f"✅ Found login button with selector: {selector}")
                            break
                    except:
                        continue
                
                if login_button:
                    logger.info("🔄 Clicking login button...")
                    await login_button.click()
                    await page.wait_for_timeout(random.uniform(3000, 5000))
                    
                    # Take screenshot after login attempt
                    await page.screenshot(path='step3_after_password.png')
                    logger.info("📸 Post-password screenshot saved")
                    
                    # Check if login was successful
                    if await self._is_logged_in(page):
                        logger.info("✅ Login successful!")
                    else:
                        logger.warning("⚠️ Login may have failed, continuing anyway...")
                else:
                    logger.warning("⚠️ No login button found after password")
            else:
                logger.info("ℹ️ No password field found - may be email-only login")
                
        except Exception as e:
            logger.error(f"💥 Password step handling failed: {e}")

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in"""
        try:
            # Look for indicators of being logged in
            logged_in_indicators = [
                '.user-avatar',
                '.profile-icon',
                '.account-menu',
                'a[href*="/account"]',
                'a[href*="/profile"]',
                '.user-name',
                '.account-name'
            ]
            
            for selector in logged_in_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"✅ Found logged-in indicator: {selector}")
                        return True
                except:
                    continue
            
            # Also check for logout buttons
            logout_indicators = [
                'button:has-text("Logout")',
                'button:has-text("Cerrar sesión")',
                'a[href*="/logout"]'
            ]
            
            for selector in logout_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"✅ Found logout button: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"⚠️ Error checking login status: {e}")
            return False

    async def _navigate_to_search(self, page, search_term: str):
        """Navigate to search results"""
        try:
            # Try to find search box
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search"]',
                'input[name="q"]',
                'input[aria-label*="search"]',
                '.search-input',
                '#search'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await page.wait_for_selector(selector, timeout=3000)
                    if search_box:
                        logger.info(f"✅ Found search box with selector: {selector}")
                        break
                except:
                    continue
            
            if search_box:
                # Type search term
                await search_box.click()
                await search_box.fill("")
                await page.wait_for_timeout(500)
                
                # Type character by character
                for char in search_term:
                    await search_box.type(char)
                    await page.wait_for_timeout(random.uniform(100, 300))
                
                await page.wait_for_timeout(1000)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(random.uniform(3000, 5000))
            else:
                # Fallback: direct URL navigation
                logger.info("🔄 No search box found, using direct URL...")
                search_url = f"https://www.temu.com/search_result.html?search_key={search_term.replace(' ', '%20')}"
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(random.uniform(3000, 5000))
            
            # Take screenshot of search results
            await page.screenshot(path='step3_search_results.png')
            logger.info("📸 Search results screenshot saved")
            
            # Save HTML for analysis
            html_content = await page.content()
            with open('authenticated_search_results.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("💾 HTML content saved: authenticated_search_results.html")
            
        except Exception as e:
            logger.error(f"💥 Search navigation failed: {e}")

    async def _extract_products(self, page, limit: int) -> List[Dict[str, Any]]:
        """Extract products from the authenticated page"""
        products = []
        
        try:
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Try multiple product selectors
            selectors = [
                '.product-item',
                '.item',
                '[data-product-id]',
                '.product-card',
                '.search-result-item',
                'div[class*="product"]',
                'div[class*="item"]'
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements[:limit]:
                            try:
                                product = await self._extract_product_info(element)
                                if product and product not in products:
                                    products.append(product)
                                    if len(products) >= limit:
                                        break
                            except Exception as e:
                                logger.debug(f"⚠️ Error extracting product: {e}")
                                continue
                        
                        if products:
                            break
                            
                except Exception as e:
                    logger.debug(f"⚠️ Selector {selector} failed: {e}")
                    continue
            
            logger.info(f"📊 Total products extracted: {len(products)}")
            return products
            
        except Exception as e:
            logger.error(f"💥 Product extraction failed: {e}")
            return []

    async def _extract_product_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract product information from an element"""
        try:
            # Extract title
            title = 'N/A'
            title_selectors = [
                'h1', 'h2', 'h3', 'h4',
                '.title', '.name', '.product-title',
                'p', 'span', 'div'
            ]
            
            for sel in title_selectors:
                try:
                    title_elem = await element.query_selector(sel)
                    if title_elem:
                        text = await title_elem.inner_text()
                        if text and len(text.strip()) > 3:
                            title = text.strip()
                            break
                except:
                    continue
            
            # Extract price
            price = 'N/A'
            price_selectors = [
                '.price', '.cost', '.amount',
                '[data-price]', '[class*="price"]'
            ]
            
            for sel in price_selectors:
                try:
                    price_elem = await element.query_selector(sel)
                    if price_elem:
                        text = await price_elem.inner_text()
                        if text and any(char.isdigit() for char in text):
                            price = text.strip()
                            break
                except:
                    continue
            
            # Extract image
            image_url = 'N/A'
            try:
                img_elem = await element.query_selector('img')
                if img_elem:
                    image_url = await img_elem.get_attribute('src')
                    if not image_url:
                        image_url = await img_elem.get_attribute('data-src')
            except:
                pass
            
            # Extract URL
            product_url = '#'
            try:
                link_elem = await element.query_selector('a')
                if link_elem:
                    product_url = await link_elem.get_attribute('href')
                    if product_url and not product_url.startswith('http'):
                        product_url = f"https://www.temu.com{product_url}"
            except:
                pass
            
            # Only return valid products
            if title != 'N/A' and title.strip():
                return {
                    'title': title,
                    'price': price,
                    'imageUrl': image_url,
                    'productUrl': product_url
                }
            
        except Exception as e:
            logger.debug(f"⚠️ Error extracting product info: {e}")
        
        return None

# Test function
async def test_authenticated_scraper():
    """Test the authenticated Temu scraper"""
    logger.info("🧪 Testing Authenticated Temu Scraper...")
    
    scraper = TemuAuthenticatedScraper()
    products = await scraper.get_products("phone case", limit=5)
    
    if products:
        print(f"✅ Found {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['title']}")
            print(f"   Price: {product['price']}")
            print(f"   URL: {product['productUrl']}")
            print(f"   Image: {product['imageUrl']}")
            print()
    else:
        print("❌ No products found")
        
    print("📸 Check the generated screenshots and HTML files for debugging")

if __name__ == "__main__":
    asyncio.run(test_authenticated_scraper())
