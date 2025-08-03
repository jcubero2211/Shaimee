# Shaymee AI Agent - Arquitectura Técnica

## Resumen Ejecutivo

El agente de IA de Shaymee es una solución integral que integra múltiples tecnologías para crear una experiencia de compra automatizada y personalizada. El sistema utiliza un patrón de arquitectura de microservicios con un agente de IA como orquestador central.

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  WhatsApp Business (UI Principal)  │  Dashboard Admin (React) │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Express.js Backend (Node.js)  │  FastAPI AI Agent (Python)  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  Temu API  │  Correos CR API  │  SINPE API  │  OpenAI GPT-4  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis Cache  │  Vector DB (Pinecone)         │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Agente de IA (Python + FastAPI)

**Tecnologías:**
- FastAPI para APIs RESTful
- OpenAI GPT-4 para procesamiento de lenguaje natural
- LangChain para orquestación de agentes
- Pinecone/Weaviate para búsqueda semántica

**Funcionalidades:**
- Procesamiento de mensajes de WhatsApp
- Búsqueda semántica de productos
- Generación de respuestas contextuales
- Orquestación de flujos de compra

**Arquitectura del Agente:**
```python
class ShaymeeAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4")
        self.tools = self._initialize_tools()
        self.memory = ConversationBufferMemory()
        self.agent_executor = self._initialize_agent()
    
    async def process_message(self, user_id, message, context):
        # Procesa mensaje con IA
        # Ejecuta herramientas apropiadas
        # Genera respuesta contextual
        pass
```

### 2. Backend Principal (Node.js + Express)

**Tecnologías:**
- Express.js para APIs RESTful
- Socket.io para comunicación en tiempo real
- Prisma ORM para base de datos
- Redis para cache y sesiones

**Funcionalidades:**
- Gestión de usuarios y autenticación
- Procesamiento de órdenes
- Integración con APIs externas
- WebSocket para actualizaciones en tiempo real

### 3. Bot de WhatsApp

**Tecnologías:**
- whatsapp-web.js para conexión con WhatsApp
- Express.js para webhooks
- Axios para comunicación con APIs

**Funcionalidades:**
- Recepción de mensajes de WhatsApp
- Envío de respuestas automáticas
- Gestión de sesiones de conversación
- Integración con el agente de IA

### 4. Dashboard Administrativo (React)

**Tecnologías:**
- React 18 con hooks
- React Router para navegación
- React Query para gestión de estado
- Tailwind CSS para estilos
- Recharts para gráficos

**Funcionalidades:**
- Panel de control en tiempo real
- Gestión de órdenes y productos
- Analytics y reportes
- Configuración del sistema

## Flujo de Datos

### 1. Flujo de Compra Completo

```
Usuario → WhatsApp → AI Agent → Product Search → Temu API
    ↓
Payment Generation → SINPE API → Payment Verification
    ↓
Order Creation → Temu Purchase → Shipment Creation
    ↓
Correos CR API → Tracking Updates → User Notification
```

### 2. Procesamiento de Mensajes

```
WhatsApp Message → Webhook → AI Agent → Context Analysis
    ↓
Tool Selection → API Call → Response Generation
    ↓
WhatsApp Response → User
```

### 3. Gestión de Órdenes

```
Order Creation → Database Storage → Payment Link Generation
    ↓
Payment Verification → Temu Purchase → Shipment Creation
    ↓
Tracking Updates → User Notifications → Order Completion
```

## Integraciones Externas

### 1. Temu API

**Endpoint:** `https://api.temu.com`
**Funcionalidades:**
- Búsqueda de productos
- Obtención de catálogos
- Creación de órdenes
- Seguimiento de envíos

**Ejemplo de Integración:**
```javascript
class TemuClient {
    async getProducts(category, limit) {
        const response = await axios.get(`${TEMU_API_URL}/products`, {
            headers: { 'Authorization': `Bearer ${TEMU_API_KEY}` },
            params: { category, limit }
        });
        return response.data;
    }
}
```

### 2. Correos de Costa Rica API

**Endpoint:** `https://api.correos.go.cr`
**Funcionalidades:**
- Creación de envíos
- Generación de etiquetas
- Seguimiento de paquetes
- Cálculo de costos

### 3. SINPE API

**Endpoint:** `https://api.sinpe.fi.cr`
**Funcionalidades:**
- Generación de links de pago
- Verificación de transacciones
- Webhooks de confirmación

### 4. OpenAI GPT-4

**Modelo:** `gpt-4`
**Funcionalidades:**
- Procesamiento de lenguaje natural
- Generación de respuestas contextuales
- Análisis de intenciones del usuario

## Base de Datos

### Esquema Principal

```sql
-- Usuarios
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Órdenes
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    temu_order_id VARCHAR(100),
    status VARCHAR(50),
    total DECIMAL(10,2),
    payment_status VARCHAR(50),
    shipping_address JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Productos
CREATE TABLE products (
    id UUID PRIMARY KEY,
    temu_product_id VARCHAR(100),
    name VARCHAR(200),
    description TEXT,
    price DECIMAL(10,2),
    category VARCHAR(100),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversaciones
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100),
    message TEXT,
    response TEXT,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Seguridad

### 1. Autenticación y Autorización

- JWT tokens para APIs
- OAuth 2.0 para integraciones externas
- Rate limiting para prevenir abuso
- Validación de webhooks con firmas

### 2. Protección de Datos

- Encriptación de datos sensibles
- HTTPS en todas las comunicaciones
- Sanitización de inputs
- Logs de auditoría

### 3. Seguridad de APIs

```javascript
// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100
});

// JWT verification
const verifyToken = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'No token provided' });
    
    jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
        if (err) return res.status(401).json({ error: 'Invalid token' });
        req.user = decoded;
        next();
    });
};
```

## Monitoreo y Logging

### 1. Logging

```javascript
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' })
    ]
});
```

### 2. Métricas

- Tiempo de respuesta de APIs
- Tasa de éxito de transacciones
- Uso de recursos del sistema
- Análisis de conversaciones

### 3. Alertas

- Errores críticos del sistema
- Fallos en integraciones externas
- Tiempo de respuesta alto
- Problemas de pago

## Escalabilidad

### 1. Horizontal Scaling

- Microservicios independientes
- Load balancing con Nginx
- Base de datos distribuida
- Cache distribuido con Redis

### 2. Vertical Scaling

- Optimización de consultas SQL
- Indexación de base de datos
- Compresión de respuestas
- CDN para assets estáticos

### 3. Performance

```javascript
// Caching con Redis
const cacheProduct = async (productId, data) => {
    await redis.setex(`product:${productId}`, 3600, JSON.stringify(data));
};

// Database connection pooling
const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});
```

## Deployment

### 1. Docker Configuration

```dockerfile
# Backend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### 2. Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/shaymee
    depends_on:
      - db
      - redis
  
  ai-agent:
    build: ./ai-agent
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  whatsapp-bot:
    build: ./whatsapp-bot
    ports:
      - "3002:3002"
  
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=shaymee
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
```

### 3. CI/CD Pipeline

```yaml
# GitHub Actions
name: Deploy Shaymee AI Agent

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: npm test
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          docker-compose up -d
```

## Consideraciones de Negocio

### 1. Costos Operativos

- OpenAI API: ~$0.03 por 1K tokens
- WhatsApp Business API: $0.005 por mensaje
- Temu API: Costos por transacción
- Hosting: ~$200-500/mes

### 2. ROI Esperado

- Reducción del 70% en tiempo de atención al cliente
- Aumento del 40% en conversiones
- Reducción del 50% en errores de procesamiento
- Escalabilidad ilimitada

### 3. Métricas de Éxito

- Tiempo de respuesta < 2 segundos
- Tasa de satisfacción del cliente > 90%
- Tasa de conversión > 15%
- Uptime > 99.9%

## Próximos Pasos

### Fase 1: MVP (2-3 meses)
- [ ] Implementación básica del agente de IA
- [ ] Integración con WhatsApp Business
- [ ] Conexión con Temu API
- [ ] Dashboard administrativo básico

### Fase 2: Integración Completa (3-4 meses)
- [ ] Integración con Correos de Costa Rica
- [ ] Sistema de pagos SINPE
- [ ] Rebranding automático de productos
- [ ] Sistema de tracking completo

### Fase 3: Optimización (2-3 meses)
- [ ] Optimización de performance
- [ ] Análisis avanzado de datos
- [ ] Machine learning personalizado
- [ ] Escalabilidad empresarial

## Conclusión

La arquitectura propuesta proporciona una base sólida para el agente de IA de Shaymee, con capacidad de escalabilidad, seguridad y mantenibilidad. El uso de tecnologías modernas y patrones de diseño establecidos asegura la viabilidad técnica y comercial del proyecto. 