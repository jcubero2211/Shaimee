#!/usr/bin/env python3
"""
Cliente para SINPE (Sistema Nacional de Pagos Electrónicos)
Maneja la generación de links de pago y seguimiento de transacciones
"""

import asyncio
import aiohttp
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class PaymentRequest:
    """Solicitud de pago SINPE"""
    amount: float
    currency: str = "CRC"
    description: str = ""
    reference: str = ""
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    expiration_hours: int = 24

@dataclass
class PaymentLink:
    """Link de pago generado"""
    payment_id: str
    payment_url: str
    qr_code: str
    amount: float
    currency: str
    description: str
    reference: str
    status: str
    created_at: datetime
    expires_at: datetime
    customer_info: Dict[str, str]

@dataclass
class PaymentStatus:
    """Estado de un pago"""
    payment_id: str
    status: str  # pending, completed, expired, failed
    amount: float
    paid_amount: float = 0.0
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    bank_reference: Optional[str] = None
    customer_info: Dict[str, str] = None

class SinpeClient:
    """
    Cliente para interactuar con SINPE
    """
    
    def __init__(self, api_key: str = None, merchant_id: str = None, base_url: str = "https://api.sinpe.fi.cr"):
        self.api_key = api_key
        self.merchant_id = merchant_id
        self.base_url = base_url
        self.session = None
        self.use_api = api_key is not None and merchant_id is not None
        
        # Configuración por defecto
        self.default_currency = "CRC"
        self.default_expiration_hours = 24
        
        logger.info(f"SinpeClient initialized in {'API' if self.use_api else 'Payment Link'} mode")
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.session:
            await self.session.close()
    
    async def create_payment_link(self, payment_request: PaymentRequest) -> PaymentLink:
        """
        Crear link de pago SINPE
        
        Args:
            payment_request: Solicitud de pago
        
        Returns:
            PaymentLink: Link de pago generado
        """
        try:
            payment_id = f"sinpe_{int(datetime.now().timestamp())}"
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=payment_request.expiration_hours)
            
            if self.use_api:
                return await self._create_payment_link_api(payment_request, payment_id, created_at, expires_at)
            else:
                return await self._create_payment_link_simulation(payment_request, payment_id, created_at, expires_at)
                
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            raise
    
    async def _create_payment_link_api(self, payment_request: PaymentRequest, payment_id: str, created_at: datetime, expires_at: datetime) -> PaymentLink:
        """
        Crear link de pago usando API oficial
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "merchant_id": self.merchant_id,
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "description": payment_request.description,
            "reference": payment_request.reference,
            "customer_name": payment_request.customer_name,
            "customer_email": payment_request.customer_email,
            "customer_phone": payment_request.customer_phone,
            "expiration_hours": payment_request.expiration_hours
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/payments",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 201:
                data = await response.json()
                return PaymentLink(
                    payment_id=data.get("payment_id", payment_id),
                    payment_url=data.get("payment_url"),
                    qr_code=data.get("qr_code"),
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    description=payment_request.description,
                    reference=payment_request.reference,
                    status="pending",
                    created_at=created_at,
                    expires_at=expires_at,
                    customer_info={
                        "name": payment_request.customer_name,
                        "email": payment_request.customer_email,
                        "phone": payment_request.customer_phone
                    }
                )
            else:
                raise Exception(f"API Error: {response.status}")
    
    async def _create_payment_link_simulation(self, payment_request: PaymentRequest, payment_id: str, created_at: datetime, expires_at: datetime) -> PaymentLink:
        """
        Crear link de pago simulado (para desarrollo)
        """
        logger.info(f"Simulating SINPE payment link creation for {payment_request.amount} {payment_request.currency}")
        
        # Simular proceso de generación
        await asyncio.sleep(1)
        
        # Generar URL de pago simulado
        payment_url = f"https://sinpe.fi.cr/pay/{payment_id}"
        qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={payment_url}"
        
        return PaymentLink(
            payment_id=payment_id,
            payment_url=payment_url,
            qr_code=qr_code,
            amount=payment_request.amount,
            currency=payment_request.currency,
            description=payment_request.description,
            reference=payment_request.reference,
            status="pending",
            created_at=created_at,
            expires_at=expires_at,
            customer_info={
                "name": payment_request.customer_name,
                "email": payment_request.customer_email,
                "phone": payment_request.customer_phone
            }
        )
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Obtener estado de un pago
        
        Args:
            payment_id: ID del pago
        
        Returns:
            PaymentStatus: Estado del pago
        """
        try:
            if self.use_api:
                return await self._get_payment_status_api(payment_id)
            else:
                return await self._get_payment_status_simulation(payment_id)
                
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return PaymentStatus(
                payment_id=payment_id,
                status="error",
                amount=0.0,
                customer_info={}
            )
    
    async def _get_payment_status_api(self, payment_id: str) -> PaymentStatus:
        """
        Obtener estado usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with self.session.get(
            f"{self.base_url}/api/v1/payments/{payment_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return PaymentStatus(
                    payment_id=payment_id,
                    status=data.get("status", "pending"),
                    amount=data.get("amount", 0.0),
                    paid_amount=data.get("paid_amount", 0.0),
                    paid_at=datetime.fromisoformat(data.get("paid_at")) if data.get("paid_at") else None,
                    transaction_id=data.get("transaction_id"),
                    bank_reference=data.get("bank_reference"),
                    customer_info=data.get("customer_info", {})
                )
            else:
                return PaymentStatus(
                    payment_id=payment_id,
                    status="error",
                    amount=0.0,
                    customer_info={}
                )
    
    async def _get_payment_status_simulation(self, payment_id: str) -> PaymentStatus:
        """
        Obtener estado simulado
        """
        logger.info(f"Simulating payment status for {payment_id}")
        
        await asyncio.sleep(0.5)
        
        # Simular diferentes estados basados en el ID
        status_options = ["pending", "completed", "expired", "failed"]
        status = status_options[hash(payment_id) % len(status_options)]
        
        if status == "completed":
            return PaymentStatus(
                payment_id=payment_id,
                status=status,
                amount=25000.0,
                paid_amount=25000.0,
                paid_at=datetime.now() - timedelta(hours=1),
                transaction_id=f"TXN_{payment_id}",
                bank_reference=f"REF_{payment_id}",
                customer_info={"name": "Cliente Test", "email": "test@example.com", "phone": "50612345678"}
            )
        else:
            return PaymentStatus(
                payment_id=payment_id,
                status=status,
                amount=25000.0,
                customer_info={"name": "Cliente Test", "email": "test@example.com", "phone": "50612345678"}
            )
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancelar un pago
        
        Args:
            payment_id: ID del pago
        
        Returns:
            bool: True si se canceló correctamente
        """
        try:
            logger.info(f"Canceling payment {payment_id}")
            
            if self.use_api:
                return await self._cancel_payment_api(payment_id)
            else:
                return await self._cancel_payment_simulation(payment_id)
                
        except Exception as e:
            logger.error(f"Error canceling payment: {str(e)}")
            return False
    
    async def _cancel_payment_api(self, payment_id: str) -> bool:
        """
        Cancelar pago usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with self.session.delete(
            f"{self.base_url}/api/v1/payments/{payment_id}",
            headers=headers
        ) as response:
            return response.status == 200
    
    async def _cancel_payment_simulation(self, payment_id: str) -> bool:
        """
        Cancelar pago simulado
        """
        await asyncio.sleep(0.5)
        logger.info(f"Simulated payment cancellation for {payment_id}")
        return True
    
    async def get_payment_history(self, limit: int = 50, status: str = None) -> List[PaymentStatus]:
        """
        Obtener historial de pagos
        
        Args:
            limit: Límite de resultados
            status: Filtrar por estado
        
        Returns:
            List[PaymentStatus]: Lista de pagos
        """
        try:
            if self.use_api:
                return await self._get_payment_history_api(limit, status)
            else:
                return await self._get_payment_history_simulation(limit, status)
                
        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}")
            return []
    
    async def _get_payment_history_api(self, limit: int = 50, status: str = None) -> List[PaymentStatus]:
        """
        Obtener historial usando API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        async with self.session.get(
            f"{self.base_url}/api/v1/payments",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [PaymentStatus(**payment) for payment in data.get("payments", [])]
            else:
                return []
    
    async def _get_payment_history_simulation(self, limit: int = 50, status: str = None) -> List[PaymentStatus]:
        """
        Obtener historial simulado
        """
        logger.info(f"Simulating payment history retrieval")
        await asyncio.sleep(0.5)
        
        # Simular historial de pagos
        sample_payments = []
        statuses = ["completed", "pending", "expired", "failed"]
        
        for i in range(min(limit, 10)):
            payment_status = statuses[i % len(statuses)]
            
            if status and payment_status != status:
                continue
            
            payment = PaymentStatus(
                payment_id=f"sinpe_{i+1}",
                status=payment_status,
                amount=25000.0 + (i * 5000),
                paid_amount=25000.0 + (i * 5000) if payment_status == "completed" else 0.0,
                paid_at=datetime.now() - timedelta(hours=i+1) if payment_status == "completed" else None,
                transaction_id=f"TXN_{i+1}" if payment_status == "completed" else None,
                bank_reference=f"REF_{i+1}" if payment_status == "completed" else None,
                customer_info={"name": f"Cliente {i+1}", "email": f"cliente{i+1}@example.com", "phone": "50612345678"}
            )
            
            sample_payments.append(payment)
        
        return sample_payments
    
    async def test_connection(self) -> bool:
        """
        Probar conexión con SINPE
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            if self.use_api:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with self.session.get(f"{self.base_url}/api/v1/health", headers=headers) as response:
                    return response.status == 200
            else:
                # Simular conexión exitosa
                await asyncio.sleep(0.5)
                return True
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

# Función de utilidad para crear solicitud de pago
def create_payment_request(
    amount: float,
    description: str = "Pago Shaymee Store",
    reference: str = "",
    customer_name: str = "",
    customer_email: str = "",
    customer_phone: str = "",
    currency: str = "CRC",
    expiration_hours: int = 24
) -> PaymentRequest:
    """
    Crear solicitud de pago con valores por defecto
    
    Args:
        amount: Monto a pagar
        description: Descripción del pago
        reference: Referencia del pago
        customer_name: Nombre del cliente
        customer_email: Email del cliente
        customer_phone: Teléfono del cliente
        currency: Moneda (por defecto CRC)
        expiration_hours: Horas de expiración
    
    Returns:
        PaymentRequest: Solicitud de pago
    """
    return PaymentRequest(
        amount=amount,
        currency=currency,
        description=description,
        reference=reference,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        expiration_hours=expiration_hours
    ) 