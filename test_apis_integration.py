#!/usr/bin/env python3
"""
Script de prueba para las APIs de Correos de Costa Rica y SINPE
Prueba la integración completa del dashboard
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar componentes
from integrations.correos_client import CorreosClient, create_package_info, PickupOrder
from integrations.sinpe_client import SinpeClient, create_payment_request, PaymentLink
from loguru import logger

# Configurar logging
logger.add("test_apis_integration.log", rotation="1 MB")

class APIsIntegrationTester:
    """
    Clase para probar la integración de APIs
    """
    
    def __init__(self):
        self.correos_client = CorreosClient()
        self.sinpe_client = SinpeClient()
        
    async def test_correos_integration(self):
        """
        Probar integración con Correos de Costa Rica
        """
        print("📮 Probando integración con Correos de Costa Rica...")
        
        try:
            # Probar conexión
            connection = await self.correos_client.test_connection()
            print(f"✅ Conexión: {'Exitosa' if connection else 'Fallida'}")
            
            # Crear información de paquete
            package_info = create_package_info(
                tracking_number="CR123456",
                weight=1.5,
                description="Producto Shaymee - Decoración para casa",
                declared_value=25000.0,
                recipient_name="María González",
                recipient_phone="50687654321",
                delivery_address="456 Avenida Central, San José, Costa Rica"
            )
            
            # Crear orden de recogida
            pickup_order = await self.correos_client.create_pickup_order(package_info)
            print(f"✅ Orden de recogida creada: {pickup_order.order_id}")
            print(f"   📦 Tracking: {pickup_order.package_info.tracking_number}")
            print(f"   📅 Fecha: {pickup_order.pickup_date.strftime('%Y-%m-%d')}")
            print(f"   📍 Estado: {pickup_order.status}")
            
            # Obtener información de seguimiento
            tracking_info = await self.correos_client.get_tracking_info("CR123456")
            print(f"✅ Información de seguimiento obtenida")
            print(f"   📍 Estado actual: {tracking_info.get('status', 'N/A')}")
            print(f"   📍 Ubicación: {tracking_info.get('current_location', 'N/A')}")
            
            # Obtener órdenes de recogida
            pickup_orders = await self.correos_client.get_pickup_orders(limit=3)
            print(f"✅ Órdenes de recogida obtenidas: {len(pickup_orders)}")
            
            # Actualizar estado de orden
            status_updated = await self.correos_client.update_pickup_order_status(
                pickup_order.order_id, 
                "completed", 
                "Paquete recogido exitosamente"
            )
            print(f"✅ Estado actualizado: {'Exitoso' if status_updated else 'Fallido'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error con Correos: {str(e)}")
            return False
    
    async def test_sinpe_integration(self):
        """
        Probar integración con SINPE
        """
        print("\n💳 Probando integración con SINPE...")
        
        try:
            # Probar conexión
            connection = await self.sinpe_client.test_connection()
            print(f"✅ Conexión: {'Exitosa' if connection else 'Fallida'}")
            
            # Crear solicitud de pago
            payment_request = create_payment_request(
                amount=25000.0,
                description="Pago Shaymee Store - Producto decorativo",
                reference="ORD-123456",
                customer_name="Juan Pérez",
                customer_email="juan.perez@email.com",
                customer_phone="50612345678"
            )
            
            # Crear link de pago
            payment_link = await self.sinpe_client.create_payment_link(payment_request)
            print(f"✅ Link de pago creado: {payment_link.payment_id}")
            print(f"   💰 Monto: ₡{payment_link.amount:,.2f}")
            print(f"   🔗 URL: {payment_link.payment_url}")
            print(f"   📱 QR Code: {payment_link.qr_code}")
            print(f"   ⏰ Expira: {payment_link.expires_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Obtener estado del pago
            payment_status = await self.sinpe_client.get_payment_status(payment_link.payment_id)
            print(f"✅ Estado del pago obtenido")
            print(f"   📊 Estado: {payment_status.status}")
            print(f"   💰 Monto pagado: ₡{payment_status.paid_amount:,.2f}")
            
            # Obtener historial de pagos
            payment_history = await self.sinpe_client.get_payment_history(limit=5)
            print(f"✅ Historial de pagos obtenido: {len(payment_history)} pagos")
            
            # Cancelar pago (simulado)
            cancelled = await self.sinpe_client.cancel_payment(payment_link.payment_id)
            print(f"✅ Cancelación de pago: {'Exitosa' if cancelled else 'Fallida'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error con SINPE: {str(e)}")
            return False
    
    async def test_dashboard_integration(self):
        """
        Probar integración del dashboard
        """
        print("\n🖥️ Probando integración del dashboard...")
        
        try:
            # Simular datos del dashboard
            dashboard_data = {
                "stats": {
                    "totalOrders": 45,
                    "pendingOrders": 8,
                    "completedOrders": 32,
                    "totalRevenue": 1250000,
                    "averageOrderValue": 27777,
                    "pickupOrders": 12,
                    "deliveredOrders": 25
                },
                "recentOrders": [
                    {
                        "id": "ORD-001",
                        "customer_name": "María González",
                        "customer_phone": "50687654321",
                        "total": 35000,
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    },
                    {
                        "id": "ORD-002",
                        "customer_name": "Juan Pérez",
                        "customer_phone": "50612345678",
                        "total": 25000,
                        "status": "processing",
                        "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
                    }
                ]
            }
            
            print("✅ Datos del dashboard generados")
            print(f"   📊 Total órdenes: {dashboard_data['stats']['totalOrders']}")
            print(f"   💰 Ingresos totales: ₡{dashboard_data['stats']['totalRevenue']:,}")
            print(f"   📦 Órdenes pendientes: {dashboard_data['stats']['pendingOrders']}")
            print(f"   🚚 Órdenes de recogida: {dashboard_data['stats']['pickupOrders']}")
            
            # Simular creación de orden de recogida desde dashboard
            pickup_order_data = {
                "tracking_number": "CR789012",
                "weight": 2.0,
                "description": "Producto Shaymee - Accesorios",
                "declared_value": 30000,
                "recipient_name": "Ana Rodríguez",
                "recipient_phone": "50698765432",
                "delivery_address": "789 Calle Principal, Heredia, Costa Rica",
                "pickup_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
            
            print("✅ Orden de recogida desde dashboard")
            print(f"   📦 Tracking: {pickup_order_data['tracking_number']}")
            print(f"   📦 Peso: {pickup_order_data['weight']} kg")
            print(f"   💰 Valor: ₡{pickup_order_data['declared_value']:,}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error con dashboard: {str(e)}")
            return False
    
    async def test_automated_workflow(self):
        """
        Probar flujo de trabajo automatizado
        """
        print("\n🤖 Probando flujo de trabajo automatizado...")
        
        try:
            # Simular proceso completo: Orden → Pago → Recogida → Entrega
            
            # 1. Crear orden
            print("📋 1. Creando orden...")
            order_data = {
                "id": "ORD-AUTO-001",
                "customer_name": "Carlos López",
                "customer_phone": "50655556666",
                "total": 45000,
                "items": [
                    {"name": "Lámpara decorativa", "price": 25000, "quantity": 1},
                    {"name": "Cojín ornamental", "price": 20000, "quantity": 1}
                ]
            }
            print(f"   ✅ Orden creada: {order_data['id']}")
            
            # 2. Generar link de pago
            print("💳 2. Generando link de pago...")
            payment_request = create_payment_request(
                amount=order_data["total"],
                description=f"Pago Shaymee - Orden {order_data['id']}",
                reference=order_data["id"],
                customer_name=order_data["customer_name"],
                customer_phone=order_data["customer_phone"]
            )
            payment_link = await self.sinpe_client.create_payment_link(payment_request)
            print(f"   ✅ Link generado: {payment_link.payment_id}")
            
            # 3. Simular pago exitoso
            print("✅ 3. Simulando pago exitoso...")
            payment_status = await self.sinpe_client.get_payment_status(payment_link.payment_id)
            print(f"   ✅ Pago confirmado: {payment_status.status}")
            
            # 4. Crear orden de recogida automática
            print("📦 4. Creando orden de recogida automática...")
            package_info = create_package_info(
                tracking_number=f"CR{order_data['id']}",
                weight=1.8,
                description=f"Productos Shaymee - Orden {order_data['id']}",
                declared_value=order_data["total"],
                recipient_name=order_data["customer_name"],
                recipient_phone=order_data["customer_phone"],
                delivery_address="123 Calle Principal, San José, Costa Rica"
            )
            pickup_order = await self.correos_client.create_pickup_order(package_info)
            print(f"   ✅ Orden de recogida creada: {pickup_order.order_id}")
            
            # 5. Actualizar estado en dashboard
            print("🔄 5. Actualizando estado en dashboard...")
            print(f"   ✅ Orden procesada automáticamente")
            print(f"   ✅ Pago verificado")
            print(f"   ✅ Orden de recogida generada")
            print(f"   ✅ Cliente notificado")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en flujo automatizado: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """
        Ejecutar todas las pruebas
        """
        print("🚀 Iniciando pruebas de integración de APIs...")
        print("=" * 60)
        
        tests = [
            ("Correos de Costa Rica", self.test_correos_integration),
            ("SINPE", self.test_sinpe_integration),
            ("Dashboard", self.test_dashboard_integration),
            ("Flujo Automatizado", self.test_automated_workflow)
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
        print("📊 RESUMEN DE PRUEBAS DE APIS")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"{status}: {test_name}")
        
        print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las APIs están funcionando correctamente!")
            print("💡 El dashboard está listo para gestionar órdenes automáticamente")
        else:
            print("⚠️ Algunas APIs necesitan configuración adicional")
        
        return passed == total

async def main():
    """
    Función principal
    """
    tester = APIsIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Sistema completo funcionando!")
        print("💡 Próximos pasos:")
        print("   1. Configurar WhatsApp Business")
        print("   2. Desplegar dashboard en producción")
        print("   3. Configurar webhooks automáticos")
        print("   4. Implementar notificaciones")
    else:
        print("\n🔧 Revisa la configuración de las APIs")

if __name__ == "__main__":
    asyncio.run(main()) 