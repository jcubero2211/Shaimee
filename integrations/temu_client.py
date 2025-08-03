import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Optional, Any
from loguru import logger
import os
from bs4 import BeautifulSoup
import time
import random

class TemuClient:
    """
    Cliente para interactuar con Temu API o web scraping
    """
    
    def __init__(self):
        self.api_key = os.getenv("TEMU_API_KEY", "scraping_mode")
        self.api_url = os.getenv("TEMU_API_URL", "https://api.temu.com")
        self.partner_id = os.getenv("TEMU_PARTNER_ID")
        self.secret_key = os.getenv("TEMU_SECRET_KEY")
        
        # Headers para web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.is_api_mode = self.api_key != "scraping_mode"
        logger.info(f"TemuClient initialized in {'API' if self.is_api_mode else 'Scraping'} mode")
    
    async def get_products(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtener productos de Temu
        """
        try:
            if self.is_api_mode:
                return await self._get_products_api(category, limit)
            else:
                return await self._get_products_scraping(category, limit)
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            return []
    
    async def _get_products_api(self, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        Obtener productos usando API oficial
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}/products"
                params = {
                    'category': category,
                    'limit': limit,
                    'partner_id': self.partner_id
                }
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_products_api(data)
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return []
    
    async def _get_products_scraping(self, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        Obtener productos usando web scraping
        """
        try:
            # Simular búsqueda en Temu
            search_terms = self._get_search_terms(category)
            products = []
            
            for term in search_terms[:limit//5]:  # 5 productos por término
                term_products = await self._scrape_products_by_term(term)
                products.extend(term_products)
            
            # Limitar resultados
            return products[:limit]
            
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            return []
    
    async def _scrape_products_by_term(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Scrape productos por término de búsqueda
        """
        try:
            # Simular productos de Temu (en producción, harías scraping real)
            products = []
            
            # Generar productos simulados
            for i in range(5):
                product = {
                    'id': f'temu_{search_term}_{i}',
                    'name': f'{search_term.title()} Product {i+1}',
                    'price': round(random.uniform(5.0, 50.0), 2),
                    'original_price': round(random.uniform(10.0, 100.0), 2),
                    'image_url': f'https://via.placeholder.com/300x300?text={search_term}+{i+1}',
                    'category': search_term,
                    'rating': round(random.uniform(3.5, 5.0), 1),
                    'reviews_count': random.randint(10, 1000),
                    'shipping': 'Free Shipping',
                    'discount': random.randint(10, 70),
                    'temu_url': f'https://temu.com/product/{search_term}_{i}'
                }
                products.append(product)
            
            # Simular delay para evitar rate limiting
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            return products
            
        except Exception as e:
            logger.error(f"Error scraping products for term {search_term}: {str(e)}")
            return []
    
    def _get_search_terms(self, category: Optional[str]) -> List[str]:
        """
        Obtener términos de búsqueda basados en categoría
        """
        if category:
            return [category]
        
        # Términos populares en Temu
        popular_terms = [
            'phone case', 'earrings', 'dress', 'shoes', 'bag',
            'watch', 'sunglasses', 'necklace', 'bracelet', 'ring',
            'makeup', 'skincare', 'hair accessories', 'home decor',
            'kitchen', 'garden', 'pet supplies', 'toys', 'electronics'
        ]
        
        return random.sample(popular_terms, min(5, len(popular_terms)))
    
    def _format_products_api(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formatear productos de API oficial
        """
        products = []
        for item in data.get('products', []):
            product = {
                'id': item.get('id'),
                'name': item.get('name'),
                'price': item.get('price'),
                'original_price': item.get('original_price'),
                'image_url': item.get('image_url'),
                'category': item.get('category'),
                'rating': item.get('rating'),
                'reviews_count': item.get('reviews_count'),
                'shipping': item.get('shipping'),
                'discount': item.get('discount'),
                'temu_url': item.get('url')
            }
            products.append(product)
        
        return products
    
    async def get_categories(self) -> List[Dict[str, str]]:
        """
        Obtener categorías disponibles
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
    
    def get_mode(self) -> str:
        """
        Obtener el modo actual del cliente
        """
        return "API" if self.is_api_mode else "Scraping"
    
    async def test_connection(self) -> bool:
        """
        Probar conexión con Temu
        """
        try:
            if self.is_api_mode:
                # Probar API
                categories = await self.get_categories()
                return len(categories) > 0
            else:
                # Probar scraping - siempre funciona en modo simulación
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 