const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const logger = require('../backend/utils/logger');

class WhatsAppBot {
    constructor() {
        this.app = express();
        this.client = null;
        this.isReady = false;
        this.sessions = new Map();
        
        this.setupMiddleware();
        this.setupRoutes();
        this.initializeWhatsApp();
    }
    
    setupMiddleware() {
        this.app.use(express.json());
        this.app.use(express.urlencoded({ extended: true }));
        
        // Verify webhook signature
        this.app.use('/webhook', (req, res, next) => {
            const signature = req.headers['x-hub-signature-256'];
            if (this.verifySignature(req.body, signature)) {
                next();
            } else {
                res.status(401).send('Unauthorized');
            }
        });
    }
    
    setupRoutes() {
        // Webhook endpoint for WhatsApp Business API
        this.app.post('/webhook', async (req, res) => {
            try {
                const { entry } = req.body;
                
                for (const webhookEntry of entry) {
                    for (const change of webhookEntry.changes) {
                        if (change.value.messages && change.value.messages.length > 0) {
                            for (const message of change.value.messages) {
                                await this.handleIncomingMessage(message);
                            }
                        }
                    }
                }
                
                res.status(200).send('OK');
            } catch (error) {
                logger.error('Webhook error:', error);
                res.status(500).send('Internal Server Error');
            }
        });
        
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'OK',
                whatsapp_ready: this.isReady,
                sessions: this.sessions.size
            });
        });
        
        // Send message endpoint
        this.app.post('/send', async (req, res) => {
            try {
                const { phone, message, type = 'text' } = req.body;
                const result = await this.sendMessage(phone, message, type);
                res.json(result);
            } catch (error) {
                logger.error('Send message error:', error);
                res.status(500).json({ error: error.message });
            }
        });
        
        // Get QR code for WhatsApp Web
        this.app.get('/qr', async (req, res) => {
            try {
                if (this.client && this.qrCode) {
                    const qrBuffer = await qrcode.toBuffer(this.qrCode);
                    res.set('Content-Type', 'image/png');
                    res.send(qrBuffer);
                } else {
                    res.status(404).json({ error: 'QR code not available' });
                }
            } catch (error) {
                logger.error('QR code error:', error);
                res.status(500).json({ error: error.message });
            }
        });
    }
    
    async initializeWhatsApp() {
        try {
            // Initialize WhatsApp client
            this.client = new Client({
                authStrategy: new LocalAuth(),
                puppeteer: {
                    headless: true,
                    args: [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                }
            });
            
            // QR code event
            this.client.on('qr', async (qr) => {
                this.qrCode = qr;
                logger.info('QR Code received, scan with WhatsApp');
                
                // Generate QR code image
                try {
                    const qrBuffer = await qrcode.toBuffer(qr);
                    logger.info('QR Code generated successfully');
                } catch (error) {
                    logger.error('Error generating QR code:', error);
                }
            });
            
            // Ready event
            this.client.on('ready', () => {
                this.isReady = true;
                logger.info('WhatsApp client is ready!');
            });
            
            // Message event
            this.client.on('message', async (message) => {
                await this.handleIncomingMessage(message);
            });
            
            // Authentication failure
            this.client.on('auth_failure', (msg) => {
                logger.error('WhatsApp authentication failed:', msg);
                this.isReady = false;
            });
            
            // Disconnected
            this.client.on('disconnected', (reason) => {
                logger.warn('WhatsApp client disconnected:', reason);
                this.isReady = false;
            });
            
            // Initialize client
            await this.client.initialize();
            
        } catch (error) {
            logger.error('Error initializing WhatsApp:', error);
        }
    }
    
    async handleIncomingMessage(message) {
        try {
            const phone = message.from;
            const messageType = message.type;
            const messageContent = this.extractMessageContent(message);
            
            logger.info(`Received message from ${phone}: ${messageContent}`);
            
            // Get or create session
            let session = this.sessions.get(phone);
            if (!session) {
                session = {
                    phone,
                    conversation_id: this.generateConversationId(),
                    last_activity: new Date(),
                    context: {}
                };
                this.sessions.set(phone, session);
            }
            
            // Update session activity
            session.last_activity = new Date();
            
            // Process message with AI agent
            const aiResponse = await this.processWithAI(phone, messageContent, session);
            
            // Send response
            await this.sendMessage(phone, aiResponse.response, 'text');
            
            // Update session context
            session.context = aiResponse.context || session.context;
            
        } catch (error) {
            logger.error('Error handling incoming message:', error);
            
            // Send error message to user
            try {
                await this.sendMessage(message.from, 
                    'Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentarlo de nuevo?');
            } catch (sendError) {
                logger.error('Error sending error message:', sendError);
            }
        }
    }
    
    extractMessageContent(message) {
        switch (message.type) {
            case 'text':
                return message.body;
            case 'image':
                return `[Imagen: ${message.caption || 'Sin descripción'}]`;
            case 'video':
                return `[Video: ${message.caption || 'Sin descripción'}]`;
            case 'audio':
                return '[Audio]';
            case 'document':
                return `[Documento: ${message.body || 'Sin nombre'}]`;
            case 'location':
                return `[Ubicación: ${message.lat}, ${message.lng}]`;
            default:
                return '[Mensaje no soportado]';
        }
    }
    
    async processWithAI(phone, message, session) {
        try {
            // Call AI agent API
            const response = await axios.post(`${process.env.AI_AGENT_URL}/agent/process-message`, {
                user_id: phone,
                message: message,
                session_id: session.conversation_id,
                context: session.context
            }, {
                headers: {
                    'Authorization': `Bearer ${process.env.AI_AGENT_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            });
            
            return response.data;
            
        } catch (error) {
            logger.error('Error processing with AI:', error);
            return {
                response: 'Lo siento, tuve un problema procesando tu mensaje. ¿Podrías intentarlo de nuevo?',
                context: session.context
            };
        }
    }
    
    async sendMessage(phone, message, type = 'text') {
        try {
            if (!this.isReady) {
                throw new Error('WhatsApp client not ready');
            }
            
            // Format phone number
            const formattedPhone = this.formatPhoneNumber(phone);
            
            // Send message based on type
            let result;
            switch (type) {
                case 'text':
                    result = await this.client.sendMessage(formattedPhone, message);
                    break;
                case 'image':
                    // Handle image message
                    result = await this.client.sendMessage(formattedPhone, message);
                    break;
                case 'button':
                    // Handle button message
                    result = await this.sendButtonMessage(formattedPhone, message);
                    break;
                case 'list':
                    // Handle list message
                    result = await this.sendListMessage(formattedPhone, message);
                    break;
                default:
                    result = await this.client.sendMessage(formattedPhone, message);
            }
            
            logger.info(`Message sent to ${phone}: ${message}`);
            return { success: true, message_id: result.id._serialized };
            
        } catch (error) {
            logger.error('Error sending message:', error);
            throw error;
        }
    }
    
    async sendButtonMessage(phone, messageData) {
        try {
            const { text, buttons } = messageData;
            
            // Create button message
            const buttonMessage = {
                text: text,
                footer: 'Shaymee - Tu tienda de confianza',
                buttons: buttons.map(btn => ({
                    id: btn.id,
                    body: btn.text
                }))
            };
            
            // Send using WhatsApp Business API
            return await this.sendWhatsAppBusinessMessage(phone, buttonMessage, 'button');
            
        } catch (error) {
            logger.error('Error sending button message:', error);
            throw error;
        }
    }
    
    async sendListMessage(phone, messageData) {
        try {
            const { text, sections } = messageData;
            
            // Create list message
            const listMessage = {
                text: text,
                footer: 'Shaymee - Tu tienda de confianza',
                sections: sections
            };
            
            // Send using WhatsApp Business API
            return await this.sendWhatsAppBusinessMessage(phone, listMessage, 'list');
            
        } catch (error) {
            logger.error('Error sending list message:', error);
            throw error;
        }
    }
    
    async sendWhatsAppBusinessMessage(phone, message, type) {
        try {
            const response = await axios.post(
                `https://graph.facebook.com/v17.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`,
                {
                    messaging_product: 'whatsapp',
                    to: phone,
                    type: type,
                    [type]: message
                },
                {
                    headers: {
                        'Authorization': `Bearer ${process.env.WHATSAPP_TOKEN}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            return response.data;
            
        } catch (error) {
            logger.error('Error sending WhatsApp Business message:', error);
            throw error;
        }
    }
    
    formatPhoneNumber(phone) {
        // Remove any non-digit characters
        let cleaned = phone.replace(/\D/g, '');
        
        // Add country code if not present
        if (!cleaned.startsWith('506')) {
            cleaned = '506' + cleaned;
        }
        
        // Add @c.us suffix for WhatsApp
        return cleaned + '@c.us';
    }
    
    generateConversationId() {
        return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    verifySignature(body, signature) {
        if (!signature) return false;
        
        const expectedSignature = 'sha256=' + crypto
            .createHmac('sha256', process.env.WHATSAPP_VERIFY_TOKEN)
            .update(JSON.stringify(body))
            .digest('hex');
        
        return crypto.timingSafeEqual(
            Buffer.from(signature),
            Buffer.from(expectedSignature)
        );
    }
    
    // Public methods for external use
    async sendWelcomeMessage(phone) {
        const welcomeMessage = `¡Hola! 👋 Soy Shaymee, tu asistente virtual de la tienda Shaymee.

¿En qué puedo ayudarte hoy? Puedo:
• Ayudarte a encontrar productos
• Mostrarte nuestras categorías
• Procesar tu compra
• Dar seguimiento a tus pedidos

¿Qué te gustaría hacer?`;
        
        return await this.sendMessage(phone, welcomeMessage);
    }
    
    async sendProductMenu(phone, categories) {
        const messageData = {
            text: '¿Qué categoría te interesa?',
            sections: [
                {
                    title: 'Categorías disponibles',
                    rows: categories.map(cat => ({
                        id: `cat_${cat.id}`,
                        title: cat.name,
                        description: cat.description
                    }))
                }
            ]
        };
        
        return await this.sendListMessage(phone, messageData);
    }
    
    async sendPaymentLink(phone, paymentData) {
        const message = `Perfecto, he generado tu link de pago SINPE:

🔗 Link de Pago: ${paymentData.link}
💰 Total: ₡${paymentData.amount}
📦 Pedido: #${paymentData.order_id}

Una vez que realices el pago, te enviaré la confirmación y comenzaremos a procesar tu pedido.

¿Necesitas ayuda con el pago?`;
        
        return await this.sendMessage(phone, message);
    }
    
    async sendOrderUpdate(phone, orderData) {
        const message = `📦 Actualización de tu pedido #${orderData.order_id}:

✅ Estado: ${orderData.status}
📅 Fecha: ${orderData.date}
🚚 Envío: ${orderData.shipping_status}

${orderData.tracking_url ? `🔍 Seguimiento: ${orderData.tracking_url}` : ''}

¿Hay algo más en lo que pueda ayudarte?`;
        
        return await this.sendMessage(phone, message);
    }
    
    // Cleanup old sessions
    cleanupSessions() {
        const now = new Date();
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours
        
        for (const [phone, session] of this.sessions.entries()) {
            if (now - session.last_activity > maxAge) {
                this.sessions.delete(phone);
                logger.info(`Cleaned up session for ${phone}`);
            }
        }
    }
}

// Start the bot
const bot = new WhatsAppBot();

// Cleanup sessions every hour
setInterval(() => {
    bot.cleanupSessions();
}, 60 * 60 * 1000);

// Export for use in other modules
module.exports = bot;

// Start server if running directly
if (require.main === module) {
    const PORT = process.env.WHATSAPP_PORT || 3002;
    bot.app.listen(PORT, () => {
        logger.info(`WhatsApp Bot running on port ${PORT}`);
    });
} 