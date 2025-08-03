#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión con Temu
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrations.temu_client import TemuClient
from loguru import logger

async def test_temu_connection():
    """
    Probar la conexión con Temu
    """
    print("🛍️ Probando conexión con Temu...")
    print("=" * 50)
    
    # Inicializar cliente
    temu_client = TemuClient()
    mode = temu_client.get_mode()
    
    print(f"📡 Modo: {mode}")
    print(f"🔑 API Key: {'Configurado' if mode == 'API' else 'Scraping Mode'}")
    print()
    
    # Probar conexión
    print("🔍 Probando conexión...")
    connection_ok = await temu_client.test_connection()
    
    if connection_ok:
        print("✅ Conexión exitosa!")
    else:
        print("❌ Error en la conexión")
        return False
    
    # Probar categorías
    print("\n📂 Obteniendo categorías...")
    try:
        categories = await temu_client.get_categories()
        print(f"✅ Categorías obtenidas: {len(categories)}")
        for cat in categories[:3]:  # Mostrar solo las primeras 3
            print(f"   - {cat['name']}: {cat['description']}")
    except Exception as e:
        print(f"❌ Error obteniendo categorías: {str(e)}")
        return False
    
    # Probar productos
    print("\n🛒 Obteniendo productos...")
    try:
        products = await temu_client.get_products(limit=5)
        print(f"✅ Productos obtenidos: {len(products)}")
        for product in products[:3]:  # Mostrar solo los primeros 3
            print(f"   - {product['name']}: ${product['price']}")
    except Exception as e:
        print(f"❌ Error obteniendo productos: {str(e)}")
        return False
    
    # Probar detalles de producto
    print("\n📋 Obteniendo detalles de producto...")
    try:
        if products:
            product_id = products[0]['id']
            details = await temu_client.get_product_details(product_id)
            if details:
                print(f"✅ Detalles obtenidos para: {details['name']}")
            else:
                print("❌ No se pudieron obtener detalles")
    except Exception as e:
        print(f"❌ Error obteniendo detalles: {str(e)}")
        return False
    
    # Probar creación de orden (simulación)
    print("\n📦 Probando creación de orden...")
    try:
        test_products = products[:2] if len(products) >= 2 else products
        test_address = {
            'name': 'Test User',
            'address': '123 Test Street',
            'city': 'San José',
            'country': 'Costa Rica',
            'phone': '50612345678'
        }
        
        order = await temu_client.create_order(test_products, test_address)
        if 'error' not in order:
            print(f"✅ Orden creada: {order.get('temu_order_id', 'N/A')}")
            print(f"   Total: ${order.get('total', 0)}")
            print(f"   Estado: {order.get('status', 'N/A')}")
        else:
            print(f"❌ Error creando orden: {order.get('error')}")
    except Exception as e:
        print(f"❌ Error en creación de orden: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ¡Todas las pruebas completadas exitosamente!")
    print(f"📊 Resumen:")
    print(f"   - Modo: {mode}")
    print(f"   - Categorías: {len(categories)}")
    print(f"   - Productos: {len(products)}")
    print(f"   - Conexión: ✅ Funcionando")
    
    return True

async def main():
    """
    Función principal
    """
    print("🚀 Iniciando pruebas de Temu...")
    print()
    
    try:
        success = await test_temu_connection()
        if success:
            print("\n✅ Todas las pruebas pasaron exitosamente!")
            print("💡 El cliente de Temu está listo para usar en el agente de IA")
        else:
            print("\n❌ Algunas pruebas fallaron")
            print("🔧 Revisa la configuración y vuelve a intentar")
        
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        logger.error(f"Test error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 