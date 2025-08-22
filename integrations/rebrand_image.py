import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import sys

def rebrand_image(product_image_url, logo_path='shaimee_logo_raster.png', output_path='rebranded_product.png', logo_size_ratio=0.18):
    """
    Download a product image, overlay the Shaimee logo, and save the rebranded image.
    """
    # Download product image
    response = requests.get(product_image_url)
    response.raise_for_status()
    product_img = Image.open(BytesIO(response.content)).convert('RGBA')

    # Load and resize logo
    logo = Image.open(logo_path).convert('RGBA')
    logo_width = int(product_img.width * logo_size_ratio)
    logo_height = int(logo.height * (logo_width / logo.width))
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)

    # Position: bottom right with margin
    margin = int(product_img.width * 0.03)
    x = product_img.width - logo_width - margin
    y = product_img.height - logo_height - margin

    # Composite logo onto product image
    rebranded_img = product_img.copy()
    rebranded_img.alpha_composite(logo, (x, y))

    # Optionally add 'Shaimee' text (white, bottom left)
    draw = ImageDraw.Draw(rebranded_img)
    font_size = int(product_img.height * 0.06)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    text = "Shaimee"
    # Use textbbox for Pillow >= 10.0
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = draw.textsize(text, font=font)
    text_x = margin
    text_y = product_img.height - text_height - margin
    draw.text((text_x, text_y), text, font=font, fill=(255,255,255,220))

    # Save as PNG
    rebranded_img.save(output_path)
    print(f"✅ Rebranded image saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rebrand_image.py <product_image_url> [logo_path] [output_path]")
        sys.exit(1)
    product_image_url = sys.argv[1]
    logo_path = sys.argv[2] if len(sys.argv) > 2 else 'shaimee_logo_raster.png'
    output_path = sys.argv[3] if len(sys.argv) > 3 else 'rebranded_product.png'
    rebrand_image(product_image_url, logo_path=logo_path, output_path=output_path)
