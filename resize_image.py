#!/usr/bin/env python3
"""
Script para redimensionar imagen para verificación de Meta Business Manager
Requisito: 1500 x 1000 píxeles mínimo
"""

from PIL import Image
import os
import sys

def resize_image(input_path, output_path, target_width=1500, target_height=1000):
    """
    Redimensiona una imagen manteniendo la proporción y rellenando si es necesario
    """
    try:
        # Abrir la imagen
        with Image.open(input_path) as img:
            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calcular las nuevas dimensiones manteniendo proporción
            img_width, img_height = img.size
            ratio = min(target_width / img_width, target_height / img_height)
            
            # Calcular nuevas dimensiones
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            # Redimensionar la imagen
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crear una nueva imagen con el tamaño objetivo
            final_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            
            # Centrar la imagen redimensionada
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            # Pegar la imagen redimensionada en el centro
            final_img.paste(resized_img, (x_offset, y_offset))
            
            # Guardar la imagen
            final_img.save(output_path, 'JPEG', quality=95)
            
            print(f"✅ Imagen redimensionada exitosamente!")
            print(f"📏 Dimensiones originales: {img_width} x {img_height}")
            print(f"📏 Dimensiones finales: {target_width} x {target_height}")
            print(f"💾 Guardada como: {output_path}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al procesar la imagen: {str(e)}")
        return False

def main():
    # Nombre del archivo de entrada
    input_filename = "WhatsApp Image 2025-08-02 at 8.29.15 PM.jpeg"
    output_filename = "verification_document_1500x1000.jpg"
    
    # Verificar si el archivo existe
    if not os.path.exists(input_filename):
        print(f"❌ Error: No se encontró el archivo '{input_filename}'")
        print("Asegúrate de que el archivo esté en el directorio actual")
        return False
    
    print("🔄 Procesando imagen...")
    print(f"📁 Archivo de entrada: {input_filename}")
    print(f"📁 Archivo de salida: {output_filename}")
    print("📏 Redimensionando a 1500 x 1000 píxeles...")
    
    # Redimensionar la imagen
    success = resize_image(input_filename, output_filename)
    
    if success:
        print("\n🎉 ¡Proceso completado!")
        print("📋 La imagen está lista para subir a Meta Business Manager")
        print("💡 Consejos:")
        print("   - El archivo se guardó como 'verification_document_1500x1000.jpg'")
        print("   - La imagen mantiene su contenido original centrado")
        print("   - Se agregó fondo blanco para cumplir con las dimensiones requeridas")
    else:
        print("\n❌ Error en el proceso")
        return False
    
    return True

if __name__ == "__main__":
    main() 