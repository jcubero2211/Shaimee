#!/usr/bin/env python3
"""
Script de prueba para el agente de IA de Shaymee
Prueba la integración con OpenAI y Temu
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes del agente
from integrations.temu_client import TemuClient
from loguru import logger

# Configurar logging
logger.add("test_ai_agent.log", rotation="1 MB")

class ShaymeeAITester:
    """
    Clase para probar el agente de IA de Shaymee
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.temu_client = TemuClient()
        
    async def test_openai_connection(self):
        """
        Probar conexión con OpenAI
        """
        print("🔑 Probando conexión con OpenAI...")
        
        if not self.openai_key:
            print("❌ Error: OPENAI_API_KEY no configurada")
            return False
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_key)
            
            # Probar con un prompt simple
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres Shaymee, un asistente virtual amigable para una tienda en Costa Rica."},
                    {"role": "user", "content": "Hola, ¿cómo estás?"}
                ],
                max_tokens=100
            )
            
            print("✅ Conexión con OpenAI exitosa!")
            print(f"🤖 Respuesta: {response.choices[0].message.content}")
            return True
            
        except Exception as e:
            print(f"❌ Error con OpenAI: {str(e)}")
            return False
    
    async def test_temu_integration(self):
        """
        Probar integración con Temu
        """
        print("\n🛍️ Probando integración con Temu...")
        
        try:
            # Probar obtención de categorías
            categories = await self.temu_client.get_categories()
            print(f"✅ Categorías obtenidas: {len(categories)}")
            
            # Probar obtención de productos
            products = await self.temu_client.get_products(limit=3)
            print(f"✅ Productos obtenidos: {len(products)}")
            
            # Mostrar algunos productos
            for i, product in enumerate(products[:2]):
                print(f"   {i+1}. {product['name']} - ${product['price']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error con Temu: {str(e)}")
            return False
    
    async def test_ai_agent_conversation(self):
        """
        Probar conversación del agente de IA
        """
        print("\n🤖 Probando conversación del agente de IA...")
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_key)
            
            # Simular conversación de cliente
            conversation = [
                {"role": "system", "content": """Eres Shaymee, un asistente virtual amigable para una tienda en Costa Rica. 
                Tu trabajo es ayudar a los clientes a encontrar productos, hacer compras y dar seguimiento a sus pedidos.
                Siempre sé cortés y usa "usted" para mostrar respeto."""},
                {"role": "user", "content": "Hola, estoy buscando un regalo para mi mamá"}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=conversation,
                max_tokens=200
            )
            
            print("✅ Conversación del agente exitosa!")
            print(f"💬 Respuesta: {response.choices[0].message.content}")
            
            # Agregar respuesta a la conversación
            conversation.append({"role": "assistant", "content": response.choices[0].message.content})
            conversation.append({"role": "user", "content": "¿Qué productos me recomiendas?"})
            
            # Segunda respuesta
            response2 = client.chat.completions.create(
                model="gpt-4",
                messages=conversation,
                max_tokens=300
            )
            
            print(f"💬 Segunda respuesta: {response2.choices[0].message.content}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en conversación: {str(e)}")
            return False
    
    async def test_product_search_integration(self):
        """
        Probar búsqueda de productos integrada
        """
        print("\n🔍 Probando búsqueda de productos integrada...")
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_key)
            
            # Obtener productos de Temu
            products = await self.temu_client.get_products(limit=5)
            
            # Crear contexto con productos
            products_context = "Productos disponibles:\n"
            for i, product in enumerate(products):
                products_context += f"{i+1}. {product['name']} - ${product['price']} - {product['category']}\n"
            
            # Simular consulta de cliente
            conversation = [
                {"role": "system", "content": f"""Eres Shaymee, un asistente virtual. 
                Tienes acceso a estos productos: {products_context}
                Recomienda productos basándote en las necesidades del cliente."""},
                {"role": "user", "content": "Busco algo para decorar mi casa"}
            ]
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=conversation,
                max_tokens=250
            )
            
            print("✅ Búsqueda de productos integrada exitosa!")
            print(f"💬 Recomendación: {response.choices[0].message.content}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en búsqueda de productos: {str(e)}")
            return False
    
    async def test_order_simulation(self):
        """
        Probar simulación de orden
        """
        print("\n📦 Probando simulación de orden...")
        
        try:
            # Obtener productos
            products = await self.temu_client.get_products(limit=2)
            
            # Simular dirección de envío
            shipping_address = {
                'name': 'Test User',
                'address': '123 Test Street',
                'city': 'San José',
                'country': 'Costa Rica',
                'phone': '50612345678'
            }
            
            # Crear orden
            order = await self.temu_client.create_order(products, shipping_address)
            
            if 'error' not in order:
                print("✅ Simulación de orden exitosa!")
                print(f"📋 ID de orden: {order.get('temu_order_id', 'N/A')}")
                print(f"💰 Total: ${order.get('total', 0)}")
                print(f"📦 Estado: {order.get('status', 'N/A')}")
                return True
            else:
                print(f"❌ Error en orden: {order.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error en simulación de orden: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """
        Ejecutar todas las pruebas
        """
        print("🚀 Iniciando pruebas del agente de IA de Shaymee...")
        print("=" * 60)
        
        tests = [
            ("OpenAI Connection", self.test_openai_connection),
            ("Temu Integration", self.test_temu_integration),
            ("AI Agent Conversation", self.test_ai_agent_conversation),
            ("Product Search Integration", self.test_product_search_integration),
            ("Order Simulation", self.test_order_simulation)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Ejecutando: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))
                print(f"{'✅ PASÓ' if result else '❌ FALLÓ'}: {test_name}")
            except Exception as e:
                print(f"❌ ERROR: {test_name} - {str(e)}")
                results.append((test_name, False))
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status}: {test_name}")
        
        print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron! El agente de IA está listo.")
        else:
            print("⚠️ Algunas pruebas fallaron. Revisa la configuración.")
        
        return passed == total

async def main():
    """
    Función principal
    """
    tester = ShaymeeAITester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 El agente de IA de Shaymee está funcionando correctamente!")
        print("💡 Próximos pasos:")
        print("   1. Configurar WhatsApp Business")
        print("   2. Configurar Correos de Costa Rica")
        print("   3. Configurar SINPE")
        print("   4. Desplegar en producción")
    else:
        print("\n🔧 Revisa la configuración y vuelve a intentar.")

if __name__ == "__main__":
    asyncio.run(main()) 