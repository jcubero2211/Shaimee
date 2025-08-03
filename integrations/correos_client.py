#!/usr/bin/env python3
"""
Cliente para Correos de Costa Rica
Maneja la generación de órdenes de recogida y seguimiento de paquetes
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class PackageInfo:
    """Información del paquete para Correos de Costa Rica"""
    tracking_number: str
    weight: float
    dimensions: Dict[str, float]  # length, width, height
    description: str
    declared_value: float
    sender_info: Dict[str, str]
    recipient_info: Dict[str, str]
    pickup_address: Dict[str, str]
    delivery_address: Dict[str, str]

@dataclass
class PickupOrder:
    """Orden de recogida de paquete"""
    order_id: str
    package_info: PackageInfo
    pickup_date: datetime
    status: str
    created_at: datetime
    notes: Optional[str] = None

class CorreosClient:
    """
    Cliente para interactuar con Correos de Costa Rica
    """
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.correos.go.cr"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.use_api = api_key is not None
        
        # URLs de Correos de Costa Rica
        self.pickup_url = "https://www.correos.go.cr/servicios-en-linea/solicitud-de-recoleccion"
        self.tracking_url = "https://www.correos.go.cr/servicios-en-linea/rastreo-de-envios"
        
        logger.info(f"CorreosClient initialized in {'API' if self.use_api else 'Web Automation'} mode")
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def create_pickup_order(self, package_info: PackageInfo, pickup_date: datetime = None) -> PickupOrder:
        """
        Crear orden de recogida de paquete
        
        Args:
            package_info: Información del paquete
            pickup_date: Fecha de recogida (por defecto mañana)
        
        Returns:
            PickupOrder: Orden de recogida creada
        """
        try:
            if not pickup_date:
                pickup_date = datetime.now() + timedelta(days=1)
            
            order_id = f"correos_pickup_{int(datetime.now().timestamp())}"
            
            if self.use_api:
                return await self._create_pickup_order_api(package_info, pickup_date, order_id)
            else:
                return await self._create_pickup_order_web(package_info, pickup_date, order_id)
                
        except Exception as e:
            logger.error(f"Error creating pickup order: {str(e)}")
            raise
    
    async def _create_pickup_order_api(self, package_info: PackageInfo, pickup_date: datetime, order_id: str) -> PickupOrder:
        """
        Crear orden de recogida usando API oficial
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "pickup_date": pickup_date.isoformat(),
            "package_info": {
                "tracking_number": package_info.tracking_number,
                "weight": package_info.weight,
                "dimensions": package_info.dimensions,
                "description": package_info.description,
                "declared_value": package_info.declared_value
            },
            "sender_info": package_info.sender_info,
            "recipient_info": package_info.recipient_info,
            "pickup_address": package_info.pickup_address,
            "delivery_address": package_info.delivery_address
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/pickup-orders",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 201:
                data = await response.json()
                return PickupOrder(
                    order_id=data.get("order_id", order_id),
                    package_info=package_info,
                    pickup_date=pickup_date,
                    status="scheduled",
                    created_at=datetime.now(),
                    notes=data.get("notes")
                )
            else:
                raise Exception(f"API Error: {response.status}")
    
    async def _create_pickup_order_web(self, package_info: PackageInfo, pickup_date: datetime, order_id: str) -> PickupOrder:
        """
        Crear orden de recogida usando automatización web (simulado)
        """
        logger.info(f"Simulating web pickup order creation for {package_info.tracking_number}")
        
        # Simular proceso de automatización web
        await asyncio.sleep(1)  # Simular tiempo de procesamiento
        
        return PickupOrder(
            order_id=order_id,
            package_info=package_info,
            pickup_date=pickup_date,
            status="scheduled",
            created_at=datetime.now(),
            notes="Orden creada mediante automatización web"
        )
    
    async def get_tracking_info(self, tracking_number: str) -> Dict:
        """
        Obtener información de seguimiento de un paquete
        
        Args:
            tracking_number: Número de seguimiento
        
        Returns:
            Dict: Información de seguimiento
        """
        try:
            if self.use_api:
                return await self._get_tracking_info_api(tracking_number)
            else:
                return await self._get_tracking_info_web(tracking_number)
                
        except Exception as e:
            logger.error(f"Error getting tracking info: {str(e)}")
            return {"error": str(e)}
    
    async def _get_tracking_info_api(self, tracking_number: str) -> Dict:
        """
        Obtener información de seguimiento usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with self.session.get(
            f"{self.base_url}/api/v1/tracking/{tracking_number}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": f"API Error: {response.status}"}
    
    async def _get_tracking_info_web(self, tracking_number: str) -> Dict:
        """
        Obtener información de seguimiento usando web scraping (simulado)
        """
        logger.info(f"Simulating web tracking for {tracking_number}")
        
        # Simular información de seguimiento
        await asyncio.sleep(0.5)
        
        return {
            "tracking_number": tracking_number,
            "status": "En tránsito",
            "current_location": "Centro de Distribución San José",
            "estimated_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
            "history": [
                {
                    "date": datetime.now().isoformat(),
                    "location": "Centro de Distribución San José",
                    "status": "En tránsito"
                },
                {
                    "date": (datetime.now() - timedelta(days=1)).isoformat(),
                    "location": "Oficina de Correos Heredia",
                    "status": "Recogido"
                }
            ]
        }
    
    async def update_pickup_order_status(self, order_id: str, status: str, notes: str = None) -> bool:
        """
        Actualizar estado de una orden de recogida
        
        Args:
            order_id: ID de la orden
            status: Nuevo estado
            notes: Notas adicionales
        
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            logger.info(f"Updating pickup order {order_id} status to {status}")
            
            if self.use_api:
                return await self._update_pickup_order_status_api(order_id, status, notes)
            else:
                return await self._update_pickup_order_status_web(order_id, status, notes)
                
        except Exception as e:
            logger.error(f"Error updating pickup order status: {str(e)}")
            return False
    
    async def _update_pickup_order_status_api(self, order_id: str, status: str, notes: str = None) -> bool:
        """
        Actualizar estado usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "status": status,
            "notes": notes
        }
        
        async with self.session.patch(
            f"{self.base_url}/api/v1/pickup-orders/{order_id}",
            headers=headers,
            json=payload
        ) as response:
            return response.status == 200
    
    async def _update_pickup_order_status_web(self, order_id: str, status: str, notes: str = None) -> bool:
        """
        Actualizar estado usando web (simulado)
        """
        await asyncio.sleep(0.5)
        logger.info(f"Simulated web update: Order {order_id} -> {status}")
        return True
    
    async def get_pickup_orders(self, status: str = None, limit: int = 50) -> List[PickupOrder]:
        """
        Obtener lista de órdenes de recogida
        
        Args:
            status: Filtrar por estado
            limit: Límite de resultados
        
        Returns:
            List[PickupOrder]: Lista de órdenes
        """
        try:
            if self.use_api:
                return await self._get_pickup_orders_api(status, limit)
            else:
                return await self._get_pickup_orders_web(status, limit)
                
        except Exception as e:
            logger.error(f"Error getting pickup orders: {str(e)}")
            return []
    
    async def _get_pickup_orders_api(self, status: str = None, limit: int = 50) -> List[PickupOrder]:
        """
        Obtener órdenes usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        async with self.session.get(
            f"{self.base_url}/api/v1/pickup-orders",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [PickupOrder(**order) for order in data.get("orders", [])]
            else:
                return []
    
    async def _get_pickup_orders_web(self, status: str = None, limit: int = 50) -> List[PickupOrder]:
        """
        Obtener órdenes usando web (simulado)
        """
        logger.info(f"Simulating web pickup orders retrieval")
        await asyncio.sleep(0.5)
        
        # Simular órdenes de ejemplo
        sample_orders = []
        for i in range(min(limit, 5)):
            package_info = PackageInfo(
                tracking_number=f"CR{i+1:06d}",
                weight=1.5 + (i * 0.2),
                dimensions={"length": 20, "width": 15, "height": 10},
                description=f"Paquete de prueba {i+1}",
                declared_value=25.0 + (i * 5.0),
                sender_info={"name": "Shaymee Store", "phone": "50612345678"},
                recipient_info={"name": f"Cliente {i+1}", "phone": "50687654321"},
                pickup_address={"address": "123 Calle Principal", "city": "San José", "country": "Costa Rica"},
                delivery_address={"address": f"456 Avenida {i+1}", "city": "San José", "country": "Costa Rica"}
            )
            
            order = PickupOrder(
                order_id=f"correos_pickup_{i+1}",
                package_info=package_info,
                pickup_date=datetime.now() + timedelta(days=i+1),
                status="scheduled" if i % 2 == 0 else "completed",
                created_at=datetime.now() - timedelta(days=i),
                notes=f"Orden de ejemplo {i+1}"
            )
            
            if not status or order.status == status:
                sample_orders.append(order)
        
        return sample_orders
    
    async def test_connection(self) -> bool:
        """
        Probar conexión con Correos de Costa Rica
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            if self.use_api:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with self.session.get(f"{self.base_url}/api/v1/health", headers=headers) as response:
                    return response.status == 200
            else:
                # Simular conexión web exitosa
                await asyncio.sleep(0.5)
                return True
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

# Función de utilidad para crear información de paquete
def create_package_info(
    tracking_number: str,
    weight: float,
    description: str,
    declared_value: float,
    sender_name: str = "Shaymee Store",
    sender_phone: str = "50612345678",
    recipient_name: str = "Cliente",
    recipient_phone: str = "50687654321",
    pickup_address: str = "123 Calle Principal, San José, Costa Rica",
    delivery_address: str = "456 Avenida Central, San José, Costa Rica"
) -> PackageInfo:
    """
    Crear información de paquete con valores por defecto
    
    Args:
        tracking_number: Número de seguimiento
        weight: Peso en kg
        description: Descripción del paquete
        declared_value: Valor declarado
        sender_name: Nombre del remitente
        sender_phone: Teléfono del remitente
        recipient_name: Nombre del destinatario
        recipient_phone: Teléfono del destinatario
        pickup_address: Dirección de recogida
        delivery_address: Dirección de entrega
    
    Returns:
        PackageInfo: Información del paquete
    """
    return PackageInfo(
        tracking_number=tracking_number,
        weight=weight,
        dimensions={"length": 20, "width": 15, "height": 10},
        description=description,
        declared_value=declared_value,
        sender_info={"name": sender_name, "phone": sender_phone},
        recipient_info={"name": recipient_name, "phone": recipient_phone},
        pickup_address={"address": pickup_address, "city": "San José", "country": "Costa Rica"},
        delivery_address={"address": delivery_address, "city": "San José", "country": "Costa Rica"}
    ) 