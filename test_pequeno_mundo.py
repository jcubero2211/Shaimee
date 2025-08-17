import asyncio
import os
from dotenv import load_dotenv
from loguru import logger
from integrations.pequeno_mundo_client import PequenoMundoClient
from integrations.product_rebrander import ProductRebrander

# Load environment variables
load_dotenv()

async def main():
    logger.info("Initializing Pequeño Mundo Client for testing...")
    client = PequenoMundoClient()
    rebrander = ProductRebrander()

    search_term = "Relojes"
    logger.info(f"Attempting to scrape products for search term: '{search_term}'")

    try:
        # Get products from Pequeño Mundo
        products = await client.get_products(search_term)
        
        if products is not None:
            logger.success(f"Scraper finished. Found {len(products)} products.")
            
            # Rebrand the products
            logger.info("Rebranding products with AI...")
            rebranded_products = await rebrander.rebrand_products(products)
            
            # Display results
            for i, product in enumerate(rebranded_products, 1):
                logger.info(f"\n{'='*50}")
                logger.info(f"Producto #{i}")
                logger.info(f"Original: {product.get('title', 'N/A')}")
                logger.info(f"Precio: {product.get('price', 'N/A')}")
                logger.info(f"Marca: {product.get('brand', 'N/A')}")
                logger.info(f"Nombre rebranded: {product.get('rebranded_name', 'N/A')}")
                logger.info(f"Descripción: {product.get('description', 'N/A')}")
                logger.info(f"URL: {product.get('productUrl', 'N/A')}")
                logger.info(f"Imagen: {product.get('imageUrl', 'N/A')}")
            
            logger.success("\nRebranding completed successfully!")
            
        else:
            logger.error("Scraper failed and returned None. Check logs for exceptions.")
            
    except Exception as e:
        logger.error(f"An error occurred during the test run: {e}")
        
    finally:
        # Cleanup if needed
        pass

if __name__ == "__main__":
    asyncio.run(main())
