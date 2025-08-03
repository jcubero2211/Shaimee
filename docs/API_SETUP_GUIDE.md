# Guía de Configuración de APIs - Shaymee AI Agent

## 📋 **Resumen Ejecutivo**

Esta guía te llevará paso a paso a través de la configuración de todas las APIs externas necesarias para el agente de IA de Shaymee.

## 🚀 **Inicio Rápido**

```bash
# Ejecutar script de configuración automática
./scripts/configure-apis.sh
```

---

## 1. 🔑 **OpenAI API (OBLIGATORIO)**

### **Paso a Paso:**

1. **Crear cuenta:**
   - Ve a [platform.openai.com](https://platform.openai.com)
   - Haz clic en "Sign up"
   - Completa el registro con tu email

2. **Obtener API Key:**
   - Inicia sesión en tu cuenta
   - Ve a "API Keys" en el menú lateral
   - Haz clic en "Create new secret key"
   - Copia la key (empieza con `sk-`)

3. **Configurar en .env:**
   ```bash
   OPENAI_API_KEY=sk-tu-api-key-aqui
   ```

### **Costos:**
- $0.03 por 1K tokens (aproximadamente $0.003 por mensaje)
- Crédito gratuito de $5 al registrarte

### **Estado:** ✅ **OBLIGATORIO**

---

## 2. 📱 **WhatsApp Business API (OBLIGATORIO)**

### **Paso a Paso:**

1. **Crear cuenta de Facebook Developer:**
   - Ve a [developers.facebook.com](https://developers.facebook.com)
   - Haz clic en "Get Started"
   - Completa el registro

2. **Crear aplicación:**
   - Haz clic en "Create App"
   - Selecciona "Business" como tipo
   - Nombra tu app "Shaymee AI Agent"

3. **Configurar WhatsApp:**
   - En el dashboard, busca "WhatsApp" en productos
   - Haz clic en "Set up"
   - Selecciona tu número de WhatsApp Business

4. **Obtener credenciales:**
   - **Token:** En WhatsApp > Getting Started
   - **Phone Number ID:** En WhatsApp > Phone Numbers
   - **Verify Token:** Crea uno personalizado (ej: "shaymee2024")

5. **Configurar webhook:**
   - URL: `https://tu-dominio.com/webhook`
   - Verify Token: El que creaste arriba

6. **Configurar en .env:**
   ```bash
   WHATSAPP_TOKEN=tu_token_aqui
   WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
   WHATSAPP_VERIFY_TOKEN=shaymee2024
   ```

### **Costos:**
- $0.005 por mensaje enviado
- $0.005 por mensaje recibido
- Número de WhatsApp Business: ~$1/mes

### **Estado:** ✅ **OBLIGATORIO**

---

## 3. 🛍️ **Temu API (OPCIONAL - Alternativa disponible)**

### **Opción A: API Oficial (Recomendado)**

1. **Contactar a Temu:**
   - Email: `partnership@temu.com`
   - Asunto: "API Access Request for Costa Rica Business"

2. **Documentación requerida:**
   - Registro de empresa
   - Información bancaria
   - Plan de negocio
   - Volumen estimado de ventas

3. **Proceso de aprobación:**
   - Puede tomar 2-4 semanas
   - Requiere documentación completa
   - Aprobación por volumen de ventas

4. **Configurar en .env:**
   ```bash
   TEMU_API_KEY=tu_api_key
   TEMU_PARTNER_ID=tu_partner_id
   TEMU_SECRET_KEY=tu_secret_key
   ```

### **Opción B: Web Scraping (Implementado)**

Si no tienes acceso a la API oficial, el sistema usa web scraping automático:

```bash
TEMU_API_KEY=scraping_mode
```

### **Estado:** ⚠️ **OPCIONAL** (Web scraping disponible)

---

## 4. 📮 **Correos de Costa Rica API (OPCIONAL - Alternativa disponible)**

### **Opción A: API Oficial**

1. **Contactar a Correos CR:**
   - Teléfono: +506 2202-2900
   - Pregunta por: "API de envíos para empresas"

2. **Documentación requerida:**
   - Registro de empresa
   - Certificado de comercio
   - Volumen estimado de envíos
   - Información de facturación

3. **Proceso de aprobación:**
   - Revisión de documentación
   - Aprobación por volumen
   - Configuración técnica

4. **Configurar en .env:**
   ```bash
   CORREOS_API_KEY=tu_api_key
   CORREOS_USERNAME=tu_usuario
   CORREOS_PASSWORD=tu_password
   ```

### **Opción B: Automatización Web (Implementado)**

Si no tienes acceso a la API oficial:

```bash
CORREOS_API_KEY=automation_mode
```

### **Estado:** ⚠️ **OPCIONAL** (Automatización web disponible)

---

## 5. 💳 **SINPE API (OPCIONAL - Alternativa disponible)**

### **Opción A: API Oficial**

1. **Contactar al BCCR:**
   - Email: `sinpe@bccr.fi.cr`
   - Teléfono: +506 2243-7777
   - Solicita: "SINPE Móvil API para empresas"

2. **Documentación requerida:**
   - Registro de empresa
   - Certificado de comercio
   - Información bancaria
   - Plan de implementación

3. **Proceso de aprobación:**
   - Revisión de seguridad
   - Aprobación bancaria
   - Configuración técnica

4. **Configurar en .env:**
   ```bash
   SINPE_API_KEY=tu_api_key
   SINPE_MERCHANT_ID=tu_merchant_id
   SINPE_SECRET_KEY=tu_secret_key
   ```

### **Opción B: Links de Pago (Implementado)**

Si no tienes acceso a la API oficial:

```bash
SINPE_API_KEY=link_mode
```

### **Estado:** ⚠️ **OPCIONAL** (Links de pago disponibles)

---

## 🔧 **Configuración Automática**

### **Script de Configuración:**

```bash
# Ejecutar script interactivo
./scripts/configure-apis.sh
```

### **Verificación Manual:**

```bash
# Verificar configuración
cat .env | grep -E "(OPENAI|WHATSAPP|TEMU|CORREOS|SINPE)"
```

---

## 📊 **Estado de Configuración**

| API | Estado | Alternativa | Costo Estimado |
|-----|--------|-------------|----------------|
| OpenAI | ✅ Obligatorio | Ninguna | $0.03/1K tokens |
| WhatsApp | ✅ Obligatorio | Ninguna | $0.005/msg |
| Temu | ⚠️ Opcional | Web Scraping | Variable |
| Correos CR | ⚠️ Opcional | Automatización Web | Variable |
| SINPE | ⚠️ Opcional | Links de Pago | Variable |

---

## 🚀 **Próximos Pasos**

### **1. Configuración Mínima (Para empezar):**
```bash
# Solo necesitas OpenAI y WhatsApp
OPENAI_API_KEY=sk-tu-key
WHATSAPP_TOKEN=tu-token
WHATSAPP_PHONE_NUMBER_ID=tu-phone-id
```

### **2. Configuración Completa:**
```bash
# Todas las APIs configuradas
# (Ver archivo .env completo)
```

### **3. Iniciar Desarrollo:**
```bash
# Instalar dependencias
npm install

# Configurar APIs
./scripts/configure-apis.sh

# Iniciar desarrollo
npm run dev
```

---

## 📞 **Contactos de Soporte**

### **APIs Oficiales:**
- **WhatsApp:** [developers.facebook.com](https://developers.facebook.com)
- **OpenAI:** [platform.openai.com](https://platform.openai.com)
- **Temu:** partnership@temu.com
- **Correos CR:** +506 2202-2900
- **SINPE:** sinpe@bccr.fi.cr

### **Soporte Técnico:**
- **Documentación:** docs/TECHNICAL_ARCHITECTURE.md
- **Issues:** Crear issue en GitHub
- **Email:** soporte@shaymee.com

---

## ⚠️ **Notas Importantes**

1. **APIs Obligatorias:** OpenAI y WhatsApp son necesarias para el funcionamiento básico
2. **Alternativas:** Para APIs sin acceso, el sistema usa métodos alternativos
3. **Costos:** Considera los costos mensuales en tu plan de negocio
4. **Seguridad:** Nunca compartas tus API keys públicamente
5. **Backup:** Guarda tus credenciales en un lugar seguro

---

## 🎯 **Recomendaciones**

### **Para MVP (2-3 meses):**
- ✅ Configurar OpenAI y WhatsApp
- ⚠️ Usar alternativas para Temu, Correos CR y SINPE
- 📈 Enfocarse en funcionalidad básica

### **Para Producción (6+ meses):**
- ✅ Todas las APIs oficiales configuradas
- 🔒 Seguridad y compliance completos
- 📊 Analytics y monitoreo avanzados 