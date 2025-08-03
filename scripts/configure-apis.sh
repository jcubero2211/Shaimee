#!/bin/bash

# ========================================
# SHAYMEE AI AGENT - API CONFIGURATION SCRIPT
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Creating .env file from template..."
        cp env.example .env
        print_success ".env file created!"
    else
        print_success ".env file found!"
    fi
}

# Function to configure OpenAI
configure_openai() {
    echo ""
    print_status "=== CONFIGURACIÓN DE OPENAI ==="
    echo ""
    echo "1. Ve a https://platform.openai.com"
    echo "2. Crea una cuenta o inicia sesión"
    echo "3. Ve a 'API Keys' en el dashboard"
    echo "4. Haz clic en 'Create new secret key'"
    echo "5. Copia la key generada"
    echo ""
    
    read -p "Ingresa tu OpenAI API Key: " openai_key
    
    if [ ! -z "$openai_key" ]; then
        # Update .env file
        sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
        print_success "OpenAI API Key configurada!"
    else
        print_warning "OpenAI API Key no configurada"
    fi
}

# Function to configure WhatsApp Business
configure_whatsapp() {
    echo ""
    print_status "=== CONFIGURACIÓN DE WHATSAPP BUSINESS ==="
    echo ""
    echo "1. Ve a https://developers.facebook.com"
    echo "2. Crea una cuenta o inicia sesión"
    echo "3. Crea una nueva aplicación (Business)"
    echo "4. Agrega WhatsApp como producto"
    echo "5. Configura tu número de WhatsApp Business"
    echo ""
    
    read -p "Ingresa tu WhatsApp Business Token: " whatsapp_token
    read -p "Ingresa tu Phone Number ID: " phone_number_id
    read -p "Ingresa tu Webhook Verify Token: " verify_token
    
    if [ ! -z "$whatsapp_token" ] && [ ! -z "$phone_number_id" ]; then
        # Update .env file
        sed -i.bak "s/WHATSAPP_TOKEN=.*/WHATSAPP_TOKEN=$whatsapp_token/" .env
        sed -i.bak "s/WHATSAPP_PHONE_NUMBER_ID=.*/WHATSAPP_PHONE_NUMBER_ID=$phone_number_id/" .env
        sed -i.bak "s/WHATSAPP_VERIFY_TOKEN=.*/WHATSAPP_VERIFY_TOKEN=$verify_token/" .env
        print_success "WhatsApp Business configurado!"
    else
        print_warning "WhatsApp Business no configurado completamente"
    fi
}

# Function to configure Temu
configure_temu() {
    echo ""
    print_status "=== CONFIGURACIÓN DE TEMU API ==="
    echo ""
    echo "1. Contacta a Temu: partnership@temu.com"
    echo "2. Solicita acceso a su API de afiliados"
    echo "3. Proporciona documentación de empresa"
    echo "4. Espera aprobación (puede tomar semanas)"
    echo ""
    echo "ALTERNATIVA: Usar web scraping (ya implementado)"
    echo ""
    
    read -p "¿Tienes acceso a Temu API? (y/n): " has_temu_api
    
    if [ "$has_temu_api" = "y" ]; then
        read -p "Ingresa tu Temu API Key: " temu_api_key
        read -p "Ingresa tu Partner ID: " partner_id
        read -p "Ingresa tu Secret Key: " secret_key
        
        if [ ! -z "$temu_api_key" ]; then
            sed -i.bak "s/TEMU_API_KEY=.*/TEMU_API_KEY=$temu_api_key/" .env
            sed -i.bak "s/TEMU_PARTNER_ID=.*/TEMU_PARTNER_ID=$partner_id/" .env
            sed -i.bak "s/TEMU_SECRET_KEY=.*/TEMU_SECRET_KEY=$secret_key/" .env
            print_success "Temu API configurado!"
        fi
    else
        print_warning "Usando web scraping para Temu"
        sed -i.bak "s/TEMU_API_KEY=.*/TEMU_API_KEY=scraping_mode/" .env
    fi
}

# Function to configure Correos de Costa Rica
configure_correos() {
    echo ""
    print_status "=== CONFIGURACIÓN DE CORREOS DE COSTA RICA ==="
    echo ""
    echo "1. Contacta a Correos CR: +506 2202-2900"
    echo "2. Pregunta por 'API de envíos para empresas'"
    echo "3. Proporciona documentación de empresa"
    echo "4. Espera aprobación"
    echo ""
    echo "ALTERNATIVA: Usar automatización web (ya implementado)"
    echo ""
    
    read -p "¿Tienes acceso a Correos CR API? (y/n): " has_correos_api
    
    if [ "$has_correos_api" = "y" ]; then
        read -p "Ingresa tu Correos API Key: " correos_api_key
        read -p "Ingresa tu Usuario: " correos_username
        read -p "Ingresa tu Password: " correos_password
        
        if [ ! -z "$correos_api_key" ]; then
            sed -i.bak "s/CORREOS_API_KEY=.*/CORREOS_API_KEY=$correos_api_key/" .env
            sed -i.bak "s/CORREOS_USERNAME=.*/CORREOS_USERNAME=$correos_username/" .env
            sed -i.bak "s/CORREOS_PASSWORD=.*/CORREOS_PASSWORD=$correos_password/" .env
            print_success "Correos CR API configurado!"
        fi
    else
        print_warning "Usando automatización web para Correos CR"
        sed -i.bak "s/CORREOS_API_KEY=.*/CORREOS_API_KEY=automation_mode/" .env
    fi
}

# Function to configure SINPE
configure_sinpe() {
    echo ""
    print_status "=== CONFIGURACIÓN DE SINPE API ==="
    echo ""
    echo "1. Contacta al BCCR: sinpe@bccr.fi.cr"
    echo "2. Solicita acceso a 'SINPE Móvil API'"
    echo "3. Proporciona documentación de empresa"
    echo "4. Espera aprobación"
    echo ""
    echo "ALTERNATIVA: Usar links de pago SINPE (ya implementado)"
    echo ""
    
    read -p "¿Tienes acceso a SINPE API? (y/n): " has_sinpe_api
    
    if [ "$has_sinpe_api" = "y" ]; then
        read -p "Ingresa tu SINPE API Key: " sinpe_api_key
        read -p "Ingresa tu Merchant ID: " merchant_id
        read -p "Ingresa tu Secret Key: " sinpe_secret_key
        
        if [ ! -z "$sinpe_api_key" ]; then
            sed -i.bak "s/SINPE_API_KEY=.*/SINPE_API_KEY=$sinpe_api_key/" .env
            sed -i.bak "s/SINPE_MERCHANT_ID=.*/SINPE_MERCHANT_ID=$merchant_id/" .env
            sed -i.bak "s/SINPE_SECRET_KEY=.*/SINPE_SECRET_KEY=$sinpe_secret_key/" .env
            print_success "SINPE API configurado!"
        fi
    else
        print_warning "Usando links de pago SINPE"
        sed -i.bak "s/SINPE_API_KEY=.*/SINPE_API_KEY=link_mode/" .env
    fi
}

# Function to test configurations
test_configurations() {
    echo ""
    print_status "=== PROBANDO CONFIGURACIONES ==="
    echo ""
    
    # Test OpenAI
    if grep -q "sk-" .env; then
        print_success "✅ OpenAI API Key configurada"
    else
        print_warning "⚠️ OpenAI API Key no configurada"
    fi
    
    # Test WhatsApp
    if grep -q "WHATSAPP_TOKEN=" .env && ! grep -q "your_whatsapp" .env; then
        print_success "✅ WhatsApp Business configurado"
    else
        print_warning "⚠️ WhatsApp Business no configurado"
    fi
    
    # Test Temu
    if grep -q "TEMU_API_KEY=" .env && ! grep -q "your_temu" .env; then
        print_success "✅ Temu API configurado"
    else
        print_warning "⚠️ Temu API no configurado (usando scraping)"
    fi
    
    # Test Correos
    if grep -q "CORREOS_API_KEY=" .env && ! grep -q "your_correos" .env; then
        print_success "✅ Correos CR API configurado"
    else
        print_warning "⚠️ Correos CR API no configurado (usando automatización)"
    fi
    
    # Test SINPE
    if grep -q "SINPE_API_KEY=" .env && ! grep -q "your_sinpe" .env; then
        print_success "✅ SINPE API configurado"
    else
        print_warning "⚠️ SINPE API no configurado (usando links)"
    fi
}

# Function to display next steps
display_next_steps() {
    echo ""
    print_status "=== PRÓXIMOS PASOS ==="
    echo ""
    echo "1. Revisa el archivo .env y completa las configuraciones faltantes"
    echo "2. Ejecuta el script de instalación: ./scripts/setup.sh"
    echo "3. Inicia el desarrollo: npm run dev"
    echo ""
    echo "4. Para APIs que no tengas acceso:"
    echo "   - Temu: Usaremos web scraping"
    echo "   - Correos CR: Usaremos automatización web"
    echo "   - SINPE: Usaremos links de pago"
    echo ""
    echo "5. Documentación de APIs:"
    echo "   - WhatsApp: https://developers.facebook.com/docs/whatsapp"
    echo "   - OpenAI: https://platform.openai.com/docs"
    echo "   - Temu: Contactar partnership@temu.com"
    echo "   - Correos CR: +506 2202-2900"
    echo "   - SINPE: sinpe@bccr.fi.cr"
    echo ""
}

# Main function
main() {
    echo "========================================"
    echo "SHAYMEE AI AGENT - CONFIGURACIÓN DE APIS"
    echo "========================================"
    echo ""
    
    # Check .env file
    check_env_file
    
    # Configure each API
    configure_openai
    configure_whatsapp
    configure_temu
    configure_correos
    configure_sinpe
    
    # Test configurations
    test_configurations
    
    # Display next steps
    display_next_steps
    
    print_success "Configuración de APIs completada!"
}

# Run main function
main "$@" 