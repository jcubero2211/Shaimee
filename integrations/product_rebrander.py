import os
import asyncio
import aiohttp
import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from loguru import logger
from openai import OpenAI, AsyncOpenAI
from PIL import Image, ImageDraw, ImageFont
import io
import aiofiles
import math

class ProductRebrander:
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 target_profit_margin: float = 0.35,  # 35% profit margin
                 shipping_cost: float = 5.00,  # Base shipping cost in USD
                 brand_name: str = "Shaymee",
                 brand_voice: str = "friendly, professional, and slightly upscale"):
        
        self.client = AsyncOpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.brand_name = brand_name
        self.brand_voice = brand_voice
        self.target_profit_margin = target_profit_margin
        self.shipping_cost = shipping_cost
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'image_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_duration = 300  # 5 minutes in seconds
        
    async def calculate_optimal_price(self, original_price: float) -> Dict[str, float]:
        """Calculate optimal selling price with profit margin"""
        try:
            # Convert price string to float (handle currency symbols and commas)
            if isinstance(original_price, str):
                # Remove currency symbols and commas, then convert to float
                price_str = ''.join(c for c in original_price if c.isdigit() or c == '.')
                original_price = float(price_str)
            
            # Calculate base cost (original price + shipping)
            base_cost = original_price + self.shipping_cost
            
            # Calculate minimum price to achieve target profit margin
            min_price = base_cost / (1 - self.target_profit_margin)
            
            # Add a small random factor to make prices look more natural
            final_price = min_price * (1 + random.uniform(-0.05, 0.10))  # -5% to +10% variation
            
            # Round to 2 decimal places
            final_price = round(final_price, 2)
            
            # Calculate profit
            profit = final_price - base_cost
            
            return {
                'original_price': original_price,
                'shipping_cost': self.shipping_cost,
                'selling_price': final_price,
                'profit': profit,
                'profit_margin': profit / final_price
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimal price: {e}")
            # Fallback to a simple markup if calculation fails
            return {
                'original_price': original_price,
                'shipping_cost': self.shipping_cost,
                'selling_price': original_price * 1.5,  # 50% markup
                'profit': original_price * 0.5,
                'profit_margin': 0.33
            }
    
    def _get_cache_path(self, search_term: str, image_name: str) -> str:
        """Get the cache path for a search term and image name"""
        safe_search = "".join(c if c.isalnum() else "_" for c in search_term.lower())
        safe_name = "".join(c if c.isalnum() else "_" for c in image_name.lower())
        return os.path.join(self.cache_dir, safe_search, f"{safe_name}.jpg")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache is still valid (less than 5 minutes old)"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = os.path.getmtime(cache_path)
        return (datetime.now().timestamp() - file_time) < self.cache_duration

    async def process_product_image(self, image_url: str, product_data: Dict, search_term: str = None) -> str:
        """
        Download and process product image with branding and pricing.
        Uses cache if available and fresh (less than 5 minutes old).
        
        Args:
            image_url: URL of the source image
            product_data: Dictionary containing product information
            search_term: Search term used to find this product
            
        Returns:
            str: Absolute path to the processed image (cached or new)
        """
        if not search_term:
            search_term = 'default'
            
        # Generate a unique cache key based on the product title and search term
        product_title = product_data.get('title', 'product')
        cache_path = self._get_cache_path(search_term, product_title)
        
        # Check if we have a valid cached version
        if self._is_cache_valid(cache_path):
            logger.info(f"🔄 Using cached image for '{product_title}': {cache_path}")
            return cache_path
            
        # If no valid cache, process the image
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        # Create cache directory if it doesn't exist
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        
                        # Load image
                        image_data = await response.read()
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Create a new image with extra space at the bottom for text
                        new_height = image.height + 150  # Add space for text
                        new_image = Image.new('RGB', (image.width, new_height), 'white')
                        new_image.paste(image, (0, 0))
                        draw = ImageDraw.Draw(new_image)
                        
                        try:
                            # Try to load a nice font (fallback to default if not available)
                            font_title = ImageFont.truetype("Arial Bold.ttf", 24)
                            font_price = ImageFont.truetype("Arial Bold.ttf", 32)
                            font_brand = ImageFont.truetype("Arial.ttf", 18)
                        except:
                            # Fallback to default fonts
                            font_title = ImageFont.load_default()
                            font_price = ImageFont.load_default()
                            font_brand = ImageFont.load_default()
                        
                        # Add product title (wrapped)
                        title = product_data.get('rebranded_name', product_data.get('title', ''))
                        title_lines = []
                        current_line = []
                        
                        # Simple text wrapping
                        for word in title.split():
                            test_line = ' '.join(current_line + [word])
                            if draw.textlength(test_line, font=font_title) <= image.width - 40:
                                current_line.append(word)
                            else:
                                title_lines.append(' '.join(current_line))
                                current_line = [word]
                        if current_line:
                            title_lines.append(' '.join(current_line))
                        
                        # Draw title (centered)
                        y_position = image.height + 20
                        for line in title_lines:
                            text_width = draw.textlength(line, font=font_title)
                            x_position = (image.width - text_width) // 2
                            draw.text((x_position, y_position), line, fill="black", font=font_title)
                            y_position += 30
                        
                        # Add price with strikethrough original price
                        pricing = product_data.get('pricing', {})
                        original_price = pricing.get('original_price', 0)
                        selling_price = pricing.get('selling_price', 0)
                        
                        # Format prices
                        original_price_str = f"₡{original_price:,.2f}"
                        selling_price_str = f"₡{selling_price:,.2f}"
                        
                        # Draw prices
                        price_y = y_position + 10
                        
                        # Original price with strikethrough
                        if original_price > selling_price:
                            text_width = draw.textlength(original_price_str, font=font_brand)
                            x_position = (image.width - text_width) // 2 - 40
                            draw.text((x_position, price_y), original_price_str, fill="red", font=font_brand)
                            # Draw strikethrough
                            y_line = price_y + font_brand.size // 2
                            draw.line([(x_position, y_line), (x_position + text_width, y_line)], 
                                     fill="red", width=1)
                        
                        # Selling price (larger and bold)
                        text_width = draw.textlength(selling_price_str, font=font_price)
                        x_position = (image.width - text_width) // 2 + 40
                        draw.text((x_position, price_y - 5), selling_price_str, 
                                 fill="#2ecc71", font=font_price)  # Green color for price
                        
                        # Add brand name at the bottom
                        brand_text = self.brand_name.upper()
                        text_width = draw.textlength(brand_text, font=font_brand)
                        x_position = (image.width - text_width) // 2
                        draw.text((x_position, new_height - 30), brand_text, 
                                 fill="#7f8c8d", font=font_brand)  # Gray color for brand
                        
                        # Add a subtle border
                        draw.rectangle([0, 0, new_image.width-1, new_image.height-1], 
                                     outline="#e0e0e0", width=2)
                        
                        # Save to cache (overwrite if exists)
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        new_image.save(cache_path, "JPEG", quality=95)
                        
                        # Also save to the original location for backward compatibility
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        safe_search_term = "".join(c if c.isalnum() else "_" for c in (search_term or 'products'))[:30]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        output_dir = os.path.join(project_root, 'processed_images', safe_search_term, timestamp)
                        os.makedirs(output_dir, exist_ok=True)
                        safe_name = "".join(c if c.isalnum() else "_" for c in title)[:30]
                        output_path = os.path.join(output_dir, f"{safe_name}.jpg")
                        new_image.save(output_path, "JPEG", quality=95)
                        
                        logger.info(f"✅ Created and cached branded image: {cache_path}")
                        logger.info(f"📁 Also saved to: {output_path}")
                        return cache_path
                        
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return image_url  # Return original URL if processing fails
    
    async def generate_ai_content(self, product_data: Dict) -> Dict:
        """Generate AI content for a product"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": f"""
                    You are a professional e-commerce product manager for {self.brand_name}.
                    Your tasks:
                    1. Create a compelling product name in Spanish
                    2. Write a 2-3 sentence description highlighting key features
                    3. Suggest 3-5 key selling points
                    4. Estimate product weight class (light/medium/heavy)
                    
                    Brand Voice: {self.brand_voice}
                    Target Market: Costa Rica
                    """},
                    {"role": "user", "content": f"""
                    Rebrand this product for maximum appeal:
                    
                    Original Name: {product_data.get('title', '')}
                    Original Price: {product_data.get('price', 'N/A')}
                    
                    Format your response as a JSON object with these keys:
                    - rebranded_name: string
                    - description: string
                    - key_features: array of strings
                    - weight_class: one of [light, medium, heavy]
                    """}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in AI content generation: {e}")
            return {
                "rebranded_name": product_data.get('title', ''),
                "description": "",
                "key_features": [],
                "weight_class": "medium"
            }
            
    async def rebrand_product(self, product_data: Dict, search_term: str = None) -> Dict:
        """
        Process and rebrand a single product with AI
        
        Args:
            product_data: Dictionary containing product information
            search_term: Optional search term used to find this product
            
        Returns:
            Dict: Rebranded product data with processed image path
        """
        try:
            # Generate AI content first
            content = await self.generate_ai_content(product_data)
            
            # Calculate pricing
            pricing = await self.calculate_optimal_price(product_data.get('price', 0))
            
            # Prepare product data for image processing
            product_info = {
                **product_data,
                'rebranded_name': content.get('rebranded_name', product_data.get('title', '')),
                'pricing': pricing
            }
            
            # Process image with complete product info and search term
            processed_image = await self.process_product_image(
                image_url=product_data.get('imageUrl', ''),
                product_data=product_info,
                search_term=search_term
            )
            
            # Combine all data
            return {
                **product_data,
                'brand': self.brand_name,
                'rebranded_name': content.get('rebranded_name', product_data.get('title', '')),
                'description': content.get('description', ''),
                'key_features': content.get('key_features', []),
                'weight_class': content.get('weight_class', 'medium'),
                'pricing': pricing,
                'processed_image': processed_image,
                'original_url': product_data.get('productUrl', '')
            }
            
        except Exception as e:
            logger.error(f"Error in product processing: {e}")
            # Fallback with minimal data
            return {
                **product_data,
                "brand": self.brand_name,
                "rebranded_name": product_data.get('title', ''),
                "pricing": {
                    'original_price': 0,
                    'shipping_cost': self.shipping_cost,
                    'selling_price': 0,
                    'profit': 0,
                    'profit_margin': 0
                }
            }

    async def rebrand_products(self, products: List[Dict], search_term: str = None) -> List[Dict]:
        """
        Process multiple products with rate limiting
        
        Args:
            products: List of product dictionaries to process
            search_term: Optional search term used to find these products
            
        Returns:
            List[Dict]: List of rebranded products with processed images
        """
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def process_with_semaphore(product):
            async with semaphore:
                return await self.rebrand_product(product, search_term=search_term)
        
        tasks = [process_with_semaphore(product) for product in products]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any failed products
        return [r for r in results if not isinstance(r, Exception)]
    
    def calculate_total_profit(self, products: List[Dict]) -> Dict:
        """Calculate total profit metrics for all products"""
        total_cost = sum(p.get('pricing', {}).get('original_price', 0) for p in products)
        total_revenue = sum(p.get('pricing', {}).get('selling_price', 0) for p in products)
        total_profit = total_revenue - total_cost
        
        return {
            'total_products': len(products),
            'total_cost': total_cost,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'average_profit_margin': total_profit / total_revenue if total_revenue > 0 else 0
        }
