import asyncio
import aiohttp
import json
from typing import List, Dict, Optional, Any
from loguru import logger
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Configure Loguru
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'temu_client.log')
logger.add(log_file_path, rotation="10 MB", retention="7 days", level="INFO")

class TemuClient:
    """
    Cliente para interactuar con Temu, utilizando Apify para el scraping.
    """
    ACTOR_ID = "amit123~temu-products-scraper"
    BASE_URL = "https://api.apify.com/v2"

    def __init__(self):
        """
        Inicializa el cliente, cargando el token de Apify.
        """
        self.apify_token = os.getenv("APIFY_API_TOKEN")
        self.timeout = 180  # 3-minute timeout for the entire process
        self.mode = "none"
        
        if self.apify_token:
            self.mode = "scraping"
            logger.info("TemuClient initialized in Scraping mode using Apify.")
        else:
            logger.warning("TemuClient is unavailable. No APIFY_API_TOKEN provided.")

    async def get_products(self, search_term: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene una lista de productos de Temu utilizando el Actor de Apify.
        """
        if self.mode != 'scraping':
            logger.error("TemuClient is not configured for scraping. Cannot get products.")
            return None

        start_run_url = f"{self.BASE_URL}/acts/{self.ACTOR_ID}/runs?token={self.apify_token}"
        run_input = {
            "searchQueries": [search_term],
            "maxItems": limit,
            "language": "en-US",
            "country": "US",
            "currency": "USD"
        }

        logger.info(f"Starting Apify Actor '{self.ACTOR_ID}' for search term: '{search_term}'")
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Start the Actor run
                async with session.post(start_run_url, json=run_input) as response:
                    if response.status != 201:
                        body = await response.text()
                        logger.error(f"Failed to start Apify Actor. Status: {response.status}, Body: {body}")
                        return None
                    run_data = await response.json()
                    run_id = run_data.get('data', {}).get('id')
                    dataset_id = run_data.get('data', {}).get('defaultDatasetId')

                    if not run_id or not dataset_id:
                        logger.error(f"Could not get run ID or dataset ID from Apify response: {run_data}")
                        return None

                logger.info(f"Actor run started with ID: {run_id}. Polling for completion...")

                # Step 2: Poll for the run to finish
                run_status_url = f"{self.BASE_URL}/acts/{self.ACTOR_ID}/runs/{run_id}?token={self.apify_token}"
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    async with session.get(run_status_url) as response:
                        if response.status != 200:
                            logger.warning(f"Polling failed with status: {response.status}. Retrying...")
                            await asyncio.sleep(10) # Wait 10 seconds before retrying
                            continue
                        
                        status_data = await response.json()
                        status = status_data.get('data', {}).get('status')

                        if status == 'SUCCEEDED':
                            logger.info("Actor run succeeded.")
                            break
                        elif status in ['FAILED', 'ABORTED', 'TIMED_OUT']:
                            logger.error(f"Actor run finished with status: {status}")
                            return None
                        
                        logger.info(f"Run status is '{status}'. Waiting...")
                        await asyncio.sleep(10) # Wait 10 seconds before polling again
                else: # Loop finished due to timeout
                    logger.error(f"Polling timed out after {self.timeout} seconds.")
                    return None

                # Step 3: Retrieve results from the dataset
                logger.info(f"Retrieving results from dataset ID: {dataset_id}")
                dataset_items_url = f"{self.BASE_URL}/datasets/{dataset_id}/items?token={self.apify_token}"
                async with session.get(dataset_items_url) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.error(f"Failed to retrieve dataset items. Status: {response.status}, Body: {body}")
                        return None
                    
                    items = await response.json()
                    logger.info(f"Successfully retrieved {len(items)} products from Apify.")
                    return self._parse_apify_results(items)

        except asyncio.TimeoutError:
            logger.error(f"A step timed out after {self.timeout} seconds.")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred during Apify integration: {e}")
            return None

    def _parse_apify_results(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parsea los resultados JSON del Actor de Apify a nuestro formato de producto estándar.
        """
        products = []
        for item in items:
            try:
                # Extraer el precio numérico del string, ej: "$14.72"
                price_str = item.get('price_info', {}).get('price_str', '0').replace('$', '').replace(',', '')
                price = float(price_str)

                product = {
                    'name': item.get('title'),
                    'price': price,
                    'image_url': item.get('thumb_url'),
                    'product_url': item.get('link_url'),
                    'rating': item.get('comment', {}).get('goods_score'),
                    'sales_count': item.get('sales_num')
                }
                products.append(product)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse product item due to invalid data: {item}. Error: {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred while parsing an Apify item: {e}")
        
        return products

    async def get_categories(self) -> List[Dict[str, str]]:
        """
        Obtiene categorías disponibles
        """
        categories = [
            {'id': 'fashion', 'name': 'Fashion', 'description': 'Clothing, accessories, shoes'},
            {'id': 'electronics', 'name': 'Electronics', 'description': 'Phones, gadgets, accessories'},
            {'id': 'home', 'name': 'Home & Garden', 'description': 'Home decor, kitchen, garden'},
            {'id': 'beauty', 'name': 'Beauty & Health', 'description': 'Makeup, skincare, health'},
            {'id': 'sports', 'name': 'Sports & Outdoors', 'description': 'Fitness, outdoor activities'},
            {'id': 'toys', 'name': 'Toys & Games', 'description': 'Kids toys, games, hobbies'},
            {'id': 'automotive', 'name': 'Automotive', 'description': 'Car accessories, tools'},
            {'id': 'pets', 'name': 'Pet Supplies', 'description': 'Pet food, toys, accessories'}
        ]
        
        return categories
    
    async def create_order(self, products: List[Dict[str, Any]], shipping_address: Dict[str, str]) -> Dict[str, Any]:
        """
        Crear orden en Temu
        """
        try:
            if self.is_api_mode:
                return await self._create_order_api(products, shipping_address)
            else:
                return await self._create_order_simulation(products, shipping_address)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {'error': str(e)}
    
    async def _create_order_api(self, products: List[Dict[str, Any]], shipping_address: Dict[str, str]) -> Dict[str, Any]:
        """
        Crear orden usando API oficial
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/orders"
                data = {
                    'products': products,
                    'shipping_address': shipping_address,
                    'partner_id': self.partner_id
                }
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Order creation failed: {response.status}")
                        return {'error': 'Order creation failed'}
        except Exception as e:
            logger.error(f"API order error: {str(e)}")
            return {'error': str(e)}
    
    async def _create_order_simulation(self, products: List[Dict[str, Any]], shipping_address: Dict[str, str]) -> Dict[str, Any]:
        """
        Simular creación de orden (para modo scraping)
        """
        try:
            # Simular proceso de orden
            order_id = f"temu_order_{int(time.time())}"
            total = sum(product.get('price', 0) for product in products)
            
            order_data = {
                'temu_order_id': order_id,
                'status': 'pending',
                'total': total,
                'products': products,
                'shipping_address': shipping_address,
                'estimated_delivery': '7-14 days',
                'tracking_number': f"TEMU{order_id[-8:]}"
            }
            
            logger.info(f"Simulated order created: {order_id}")
            return order_data
            
        except Exception as e:
            logger.error(f"Simulation error: {str(e)}")
            return {'error': str(e)}
    
    async def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener detalles de un producto específico
        """
        try:
            # Simular detalles del producto
            product = {
                'id': product_id,
                'name': f'Product {product_id}',
                'price': round(random.uniform(5.0, 50.0), 2),
                'original_price': round(random.uniform(10.0, 100.0), 2),
                'description': 'High quality product with great value',
                'images': [
                    f'https://via.placeholder.com/600x600?text=Product+{product_id}+1',
                    f'https://via.placeholder.com/600x600?text=Product+{product_id}+2'
                ],
                'specifications': {
                    'Material': 'Premium quality',
                    'Size': 'Standard',
                    'Color': 'Multiple options',
                    'Warranty': '30 days'
                },
                'reviews': [
                    {
                        'user': 'Customer 1',
                        'rating': 5,
                        'comment': 'Great product, fast delivery!'
                    }
                ]
            }
            
            return product
            
        except Exception as e:
            logger.error(f"Error getting product details: {str(e)}")
            return None
    

    
    async def test_connection(self) -> bool:
        """
        Probar conexión con Temu
        """
        try:
            if self.mode == 'API':
                # Probar API
                logger.info("Testing API connection...")
                categories = await self.get_categories()
                return len(categories) > 0
            elif self.mode == 'Scraping':
                # Probar scraping con Oxylabs
                logger.info("Testing scraping connection with Oxylabs...")
                test_products = await self._scrape_products_by_term("t-shirt")
                return len(test_products) > 0
            else: # self.mode == 'Unavailable'
                logger.warning("Connection test skipped: client is unavailable.")
                return False
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 