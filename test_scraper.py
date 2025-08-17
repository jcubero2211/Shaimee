import asyncio
from integrations.temu_client import TemuClient
from loguru import logger

async def main():
    # Configure logger to write to a file for detailed debugging
    logger.add("scraper_test.log", rotation="10 MB", level="INFO")
    logger.info("Initializing Temu Client for testing...")
    
    try:
        # Make sure your .env file has PROXY_USER, PROXY_PASS, PROXY_HOST, and PROXY_PORT
        client = TemuClient()
        search_term = "wireless headphones"
        logger.info(f"Attempting to scrape products for search term: '{search_term}'")
        
        products = await client.get_products(search_term, limit=10)

        if products:
            logger.success(f"Successfully scraped {len(products)} products.")
            for i, product in enumerate(products):
                logger.info(f"  Product {i+1}: {product['title']} - {product['price']}")
                logger.info(f"    URL: {product['productUrl']}")
                logger.info(f"    Image: {product['imageUrl']}")
        elif products == []:
            logger.warning("Scraper finished but returned no products. This could be due to anti-bot measures, no results for the search term, or incorrect proxy settings.")
        else: # products is None
            logger.error("Scraper failed and returned None. Check logs for exceptions.")

    except ValueError as e:
        logger.critical(f"Configuration error: {e}. Please check your .env file.")
    except Exception as e:
        logger.opt(exception=True).error(f"An unexpected error occurred during the test run: {e}")

if __name__ == "__main__":
    # This allows running the async main function
    asyncio.run(main())
