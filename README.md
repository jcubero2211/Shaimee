# Shaymee AI Agent 🤖

## Descripción del Proyecto

Shaymee es un agente de IA inteligente que actúa como intermediario entre clientes y proveedores, específicamente integrando:

- **WhatsApp Business** como interfaz principal
- **Temu API** para obtención de productos
- **Correos de Costa Rica** para envíos
- **SINPE** para pagos automáticos
- **OpenAI GPT-4** para procesamiento de lenguaje natural

## Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   OpenAI        │    │   Temu API      │
│   Business      │◄──►│   GPT-4         │◄──►│   (Productos)   │
│   (UI Principal)│    │   (Agente IA)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SINPE API     │    │   Dashboard     │    │   Correos CR    │
│   (Pagos)       │    │   (Admin)       │    │   (Envíos)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Tecnologías Utilizadas

### Backend
- **Node.js + Express.js** - APIs RESTful
- **Python + FastAPI** - Agente de IA
- **PostgreSQL** - Base de datos principal
- **Redis** - Cache y sesiones

### IA y Machine Learning
- **OpenAI GPT-4** - Procesamiento de lenguaje natural
- **LangChain** - Framework para orquestación de agentes
- **Pinecone/Weaviate** - Vector database para búsqueda semántica

### Integraciones
- **WhatsApp Business API** - Interfaz de usuario
- **Temu API** - Catálogo de productos
- **Correos de Costa Rica API** - Gestión de envíos
- **SINPE API** - Procesamiento de pagos

## Flujo del Sistema

1. **Recepción de Cliente**: Usuario llega vía WhatsApp Business
2. **Análisis de Intención**: IA analiza la consulta del usuario
3. **Búsqueda de Productos**: Conecta con Temu API
4. **Rebranding**: Aplica marca Shaymee a productos
5. **Generación de Pago**: Crea link SINPE automático
6. **Verificación de Pago**: Confirma transacción exitosa
7. **Compra Automática**: Realiza compra en Temu
8. **Gestión de Envío**: Coordina con Correos de Costa Rica
9. **Seguimiento**: Proporciona tracking al cliente

## Estructura del Proyecto

```
shaymee/
├── backend/                 # APIs principales
│   ├── api/                # Endpoints REST
│   ├── services/           # Lógica de negocio
│   └── database/           # Modelos y migraciones
├── ai-agent/               # Agente de IA
│   ├── core/               # Lógica del agente
│   ├── integrations/       # APIs externas
│   └── prompts/            # Templates de prompts
├── dashboard/              # Panel administrativo
│   ├── frontend/           # React/Next.js
│   └── components/         # Componentes UI
├── whatsapp-bot/           # Bot de WhatsApp
│   ├── handlers/           # Manejadores de mensajes
│   └── flows/              # Flujos de conversación
└── docs/                   # Documentación
```

## Instalación y Configuración

### Prerrequisitos
- Node.js 18+
- Python 3.9+
- PostgreSQL 14+
- Redis 6+

### Variables de Entorno
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# WhatsApp Business
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id

# Temu API
TEMU_API_KEY=your_temu_key
TEMU_API_URL=https://api.temu.com

# Correos de Costa Rica
CORREOS_API_KEY=your_correos_key
CORREOS_API_URL=https://api.correos.go.cr

# SINPE
SINPE_API_KEY=your_sinpe_key
SINPE_API_URL=https://api.sinpe.fi.cr

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/shaymee
REDIS_URL=redis://localhost:6379
```

## Desarrollo

### Iniciar el proyecto
```bash
# Clonar repositorio
git clone https://github.com/shaymee/ai-agent.git
cd ai-agent

# Instalar dependencias
npm install
pip install -r requirements.txt

# Configurar base de datos
npm run db:migrate

# Iniciar servicios
npm run dev
```

## Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## Contacto

Shaymee Team - [@shaymee](https://twitter.com/shaymee)

Link del proyecto: [https://github.com/shaymee/ai-agent](https://github.com/shaymee/ai-agent) 