#!/usr/bin/env python3
"""
Generate a PDF with sample WhatsApp conversations for Shaymee products
"""
from fpdf import FPDF, FPDF_VERSION
from datetime import datetime
import random
import os
import textwrap
import sys
import json
from glob import glob
from PIL import Image

# Check if we need to use the legacy FPDF version
USE_LEGACY = FPDF_VERSION < '2.0.0'

def find_latest_catalog():
    """Find the most recent catalog JSON file"""
    catalog_files = glob('shaymee_catalog_*.json')
    if not catalog_files:
        return None
    return max(catalog_files, key=os.path.getmtime)

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a font that supports a wide range of characters
        self.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
        self.add_font('DejaVu', 'I', 'DejaVuSansCondensed-Oblique.ttf', uni=True)
        self.add_font('DejaVu', 'BI', 'DejaVuSansCondensed-BoldOblique.ttf', uni=True)
        
    def header(self):
        # Add a header to each page
        self.set_font('DejaVu', 'B', 16)
        self.cell(0, 10, 'Vista Previa de Conversaciones de WhatsApp', 0, 1, 'C')
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 5, f'Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
        self.ln(5)
        
    def footer(self):
        # Add a footer to each page
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

class WhatsAppPreviewGenerator:
    def __init__(self):
        self.pdf = PDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.set_font('DejaVu', '', 12)
        self.pdf.alias_nb_pages()  # For page numbers in footer
        
        # Load products from the latest catalog
        catalog_file = find_latest_catalog()
        if not catalog_file:
            raise FileNotFoundError("No catalog file found. Please run the pipeline first to generate product data.")
            
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
            
        self.sample_products = []
        for product in catalog['products'][:5]:  # Use first 5 products
            self.sample_products.append({
                'id': product['id'],
                'title': product['title'],
                'price': product['price'],
                'original_price': product.get('original_price', ''),
                'description': product.get('description', 'Sin descripción disponible'),
                'features': product.get('features', []),
                'image_filename': product.get('image_filename', '')
            })
        
        # Create images directory if it doesn't exist
        self.images_dir = 'product_images'
        os.makedirs(self.images_dir, exist_ok=True)
        
    def _get_product_image(self, product):
        """Get the product image path"""
        # Try to find the image in the product_images directory
        image_path = os.path.join('product_images', f"{product['id']}.jpg")
        
        # If the image exists, return its path
        if os.path.exists(image_path):
            return image_path
            
        # If not, try to find any image with the product ID in the filename
        for ext in ['.jpg', '.jpeg', '.png']:
            image_path = os.path.join('product_images', f"{product['id']}{ext}")
            if os.path.exists(image_path):
                return image_path
                
        # If no image found, return None
        print(f"  ⚠️ Image not found for product: {product['id']}")
        return None
    
    def _format_whatsapp_message(self, product):
        """Format a product as a WhatsApp message"""
        message = f"*{product['title']}*\n"
        
        # Add price with original price if available
        if product.get('original_price'):
            message += f"💵 *Precio:* ~~{product['original_price']}~~ {product['price']} (¡Oferta especial!)\n\n"
        else:
            message += f"💵 *Precio:* {product['price']}\n\n"
            
        message += f"📝 *Descripción:*\n{product['description']}\n\n"
        
        if product.get('features'):
            message += "✨ *Características destacadas:*\n"
            for feature in product['features']:
                # Remove any existing bullet points to avoid duplication
                clean_feature = feature.lstrip('•✓- ').strip()
                message += f"• {clean_feature}\n"
        
        message += "\n🛍️ ¿Te interesa este producto? ¡Estoy aquí para ayudarte!"
        return message
    
    def _add_chat_bubble(self, text, is_customer=False, y_position=0):
        """Add a chat bubble to the PDF"""
        # Set colors based on sender
        if is_customer:
            bg_color = (220, 248, 198)  # Light green for customer
            x = 20
        else:
            bg_color = (255, 255, 255)  # White for business
            x = 10
            
        # Calculate text height
        text_lines = text.split('\n')
        line_height = 8
        padding = 10
        max_width = 80  # Characters per line
        
        # Wrap long lines
        wrapped_lines = []
        for line in text_lines:
            wrapped_lines.extend(textwrap.wrap(line, width=max_width))
        
        # Calculate bubble dimensions
        text_height = len(wrapped_lines) * line_height
        bubble_height = text_height + (2 * padding)
        
        # Add bubble background
        self.pdf.set_fill_color(*bg_color)
        self.pdf.rect(x, y_position, 180, bubble_height, 'F')
        
        # Add text
        self.pdf.set_xy(x + padding, y_position + padding)
        self.pdf.set_text_color(0, 0, 0)  # Black text
        
        # Handle bold text (text between * *)
        current_x = self.pdf.get_x()
        current_y = self.pdf.get_y()
        
        for line in wrapped_lines:
            parts = line.split('*')
            is_bold = False
            
            for i, part in enumerate(parts):
                if part.strip() == '':
                    continue
                    
                if is_bold:
                    self.pdf.set_font('DejaVu', 'B', 12)
                else:
                    self.pdf.set_font('DejaVu', '', 12)
                
                self.pdf.cell(0, line_height, part, ln=0)
                is_bold = not is_bold
            
            self.pdf.ln(line_height)
            current_y += line_height
            self.pdf.set_xy(current_x, current_y)
        
        return bubble_height + 5  # Return total height used
    
    def generate_pdf(self, filename='whatsapp_preview.pdf'):
        """Generate the PDF with sample WhatsApp conversations"""
        self.pdf.add_page()
        
        # Title is now in the header
        self.pdf.add_page()
        
        # Add sample conversations
        for i, product in enumerate(self.sample_products, 1):
            # Add product image if available
            image_path = self._get_product_image(product)
            if image_path and os.path.exists(image_path):
                try:
                    # Resize image to fit PDF
                    img = Image.open(image_path)
                    width, height = img.size
                    aspect_ratio = width / height
                    new_width = 100  # 100mm width
                    new_height = new_width / aspect_ratio
                    
                    self.pdf.image(image_path, x=10, w=new_width, h=new_height)
                    self.pdf.ln(5)
                except Exception as e:
                    print(f"  ⚠️ Could not add image {image_path}: {e}")
            
            # Add product header
            self.pdf.set_fill_color(240, 240, 240)
            self.pdf.set_font('DejaVu', 'B', 14)
            self.pdf.cell(0, 10, f'Producto de Muestra #{i}', 0, 1, 'L', 1)
            self.pdf.ln(5)
            
            # Add conversation
            self.pdf.set_font('DejaVu', 'B', 12)
            self.pdf.cell(0, 10, 'Ejemplo de Conversación:', 0, 1)
            
            y_pos = self.pdf.get_y() + 5
            
            # Business message
            business_msg = "¡Hola! 👋\n\nGracias por contactar a *Shaymee*. Aquí tienes los detalles del producto que te interesa:"
            y_pos += self._add_chat_bubble(business_msg, False, y_pos)
            
            # Product details
            product_msg = self._format_whatsapp_message(product)
            y_pos += self._add_chat_bubble(product_msg, False, y_pos)
            
            # Customer response
            customer_msg = "¡Hola! Me interesa este producto. ¿Tienen disponible el color negro?"
            y_pos += self._add_chat_bubble(customer_msg, True, y_pos)
            
            # Business response
            business_reply = f"¡Claro! Tenemos disponible el color negro. ¿Te gustaría que te lo aparte? El código del producto es *{product['id']}*"
            y_pos += self._add_chat_bubble(business_reply, False, y_pos)
            
            # Add page break if not the last product
            if i < len(self.sample_products):
                self.pdf.add_page()
                y_pos = 10
            
            self.pdf.ln(10)
        
        # Save the PDF
        self.pdf.output(filename)
        return filename

if __name__ == "__main__":
    generator = WhatsAppPreviewGenerator()
    output_file = generator.generate_pdf()
    print(f"✅ PDF generado exitosamente: {output_file}")
    print(f"📄 Ubicación: {os.path.abspath(output_file)}")
