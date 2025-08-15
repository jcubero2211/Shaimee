import asyncio
import json
from integrations.temu_client import TemuClient
from dotenv import load_dotenv

async def main():
    """
    Main function to run the Temu client connection test using Apify.
    """
    print("Loading environment variables...")
    load_dotenv()
    
    print("Initializing TemuClient for Apify test...")
    client = TemuClient()
    
    if client.mode != 'scraping':
        print("❌ TemuClient is not in Scraping mode. Please check your .env file for APIFY_API_TOKEN.")
        return

    print("--- Starting Apify Connection Test ---")
    try:
        # Using a common search term for the test
        search_term = "laptop desk"
        print(f"Attempting to get products for search term: '{search_term}'...")
        
        products = await client.get_products(search_term)
        
        if products:
            print(f"✅ Success! Found {len(products)} products.")
            print("Here is the first product found:")
            # Pretty print the first product
            print(json.dumps(products[0], indent=2))
        elif products == []: # Explicitly check for an empty list
             print("✅ Test finished successfully, but the search returned no products for this term.")
        else: # products is None
            print("❌ Test failed. The scraper run may have failed or an error occurred.")
            print("Check the logs for more details: logs/temu_client.log")
            
    except Exception as e:
        print(f"An unexpected error occurred during the connection test: {e}")

    print("--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())