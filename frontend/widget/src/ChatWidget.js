/**
 * Expert Company Chat Widget - JavaScript Module
 * Compatible with the HTML demo page
 */

// Simplified interfaces for demo
const SUPPORTED_LANGUAGES = [
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', rtl: false },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', rtl: true },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', rtl: false }
];

class ChatWidget {
    constructor(container, config = {}) {
        this.container = container;
        this.config = {
            apiUrl: 'http://127.0.0.1:8001',
            theme: 'light',
            language: 'en',
            debug: false,
            ...config
        };
        
        this.currentLanguage = this.config.language;
        this.messages = [];
        this.isConnected = false;
        this.sessionId = this.generateSessionId();
        
        this.initialize();
    }

    async initialize() {
        try {
            // Initialize services
            this.initializeServices();
            
            // Setup UI components
            this.setupUI();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Test API connection
            await this.testConnection();
            
            console.log('🚀 ChatWidget initialized successfully');
        } catch (error) {
            console.error('❌ ChatWidget initialization failed:', error);
            this.handleInitializationError(error);
        }
    }

    initializeServices() {
        // Initialize API service
        this.apiService = new APIService(this.config.apiUrl);
        
        // Initialize theme manager
        this.themeManager = new ThemeManager();
        
        // Initialize message renderer
        this.messageRenderer = new MessageRenderer();
        
        // Initialize language selector
        this.languageSelector = new LanguageSelector();
    }

    setupUI() {
        // Get UI elements
        this.chatInput = this.container.querySelector('#chatInput');
        this.sendButton = this.container.querySelector('#sendButton');
        this.chatMessages = this.container.querySelector('#chatMessages');
        this.quickActions = this.container.querySelector('#quickActions');
        this.statusIndicator = this.container.querySelector('#statusIndicator');
        this.languageSelectorContainer = this.container.querySelector('#languageSelector');
        
        // Setup language selector
        if (this.languageSelectorContainer) {
            this.setupLanguageSelector();
        }
        
        // Apply theme
        this.themeManager.applyTheme(this.container);
    }

    setupLanguageSelector() {
        const languageHtml = `
            <div class="language-selector">
                <button class="language-selector-button" type="button" aria-haspopup="listbox" aria-expanded="false">
                    <span class="current-language">
                        <span class="language-flag" id="current-flag">🇺🇸</span>
                        <span class="language-name" id="current-name">English</span>
                        <span class="dropdown-arrow">▼</span>
                    </span>
                </button>
                <div class="language-dropdown" role="listbox" style="display: none;">
                    ${SUPPORTED_LANGUAGES.map(lang => `
                        <button 
                            class="language-option" 
                            type="button" 
                            data-language="${lang.code}"
                            role="option"
                            aria-selected="${lang.code === this.currentLanguage}"
                        >
                            <span class="language-flag">${lang.flag}</span>
                            <span class="language-details">
                                <span class="language-name">${lang.name}</span>
                                <span class="language-native">${lang.nativeName}</span>
                            </span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        this.languageSelectorContainer.innerHTML = languageHtml;
        
        // Setup language selector events
        const button = this.languageSelectorContainer.querySelector('.language-selector-button');
        const dropdown = this.languageSelectorContainer.querySelector('.language-dropdown');
        const options = this.languageSelectorContainer.querySelectorAll('.language-option');
        
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = dropdown.style.display === 'block';
            dropdown.style.display = isOpen ? 'none' : 'block';
            button.setAttribute('aria-expanded', !isOpen);
        });
        
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                const languageCode = e.currentTarget.dataset.language;
                this.changeLanguage(languageCode);
                dropdown.style.display = 'none';
                button.setAttribute('aria-expanded', 'false');
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            dropdown.style.display = 'none';
            button.setAttribute('aria-expanded', 'false');
        });
    }

    setupEventListeners() {
        // Send button
        this.sendButton.addEventListener('click', () => this.handleSendMessage());
        
        // Input field
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Input changes
        this.chatInput.addEventListener('input', (e) => {
            this.sendButton.disabled = !e.target.value.trim();
            this.autoResize(e.target);
        });
        
        // Quick actions
        this.quickActions.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action-button')) {
                this.handleQuickAction(e.target.dataset.action);
            }
        });
    }

    async testConnection() {
        try {
            const health = await this.apiService.getHealth();
            this.isConnected = true;
            this.updateStatus('Connected', true);
            
            if (this.config.debug) {
                console.log('✅ API Connection successful:', health);
            }
        } catch (error) {
            this.isConnected = false;
            this.updateStatus('Offline', false);
            
            if (this.config.debug) {
                console.warn('⚠️ API Connection failed:', error.message);
            }
        }
    }

    async handleSendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage({
            id: this.generateMessageId(),
            role: 'user',
            content: message,
            timestamp: Date.now(),
            language: this.currentLanguage
        });
        
        // Clear input
        this.chatInput.value = '';
        this.sendButton.disabled = true;
        this.autoResize(this.chatInput);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to API
            const response = await this.apiService.sendMessage({
                message: message,
                language: this.currentLanguage
            });
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add assistant response
            this.addMessage({
                id: this.generateMessageId(),
                role: 'assistant',
                content: response.response,
                timestamp: Date.now(),
                language: response.language,
                metadata: {
                    intent: response.intent,
                    confidence: response.confidence,
                    topics: response.detected_topics,
                    actions: response.suggested_actions
                }
            });
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage({
                id: this.generateMessageId(),
                role: 'assistant',
                content: this.getErrorMessage(error),
                timestamp: Date.now(),
                language: this.currentLanguage
            });
        }
    }

    handleQuickAction(action) {
        const actionMessages = {
            screenshot: "I can help you with screenshot analysis and cloning. What type of interface would you like to recreate?",
            figma: "I can assist with Figma imports and design analysis. Do you have a specific design file you'd like to work with?",
            landing: "I can help you create effective landing pages for petroleum engineering services. What's your target audience?",
            signup: "I can help design signup forms for training programs. What information do you need to collect?",
            calculate: "I can help with engineering calculations and factorial computations. What would you like to calculate?"
        };
        
        const message = actionMessages[action] || `Tell me more about ${action}.`;
        this.chatInput.value = message;
        this.sendButton.disabled = false;
        this.chatInput.focus();
        
        // Auto-resize
        this.autoResize(this.chatInput);
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        
        // Show messages container if first message
        if (this.messages.length === 1) {
            this.chatMessages.style.display = 'block';
        }
    }

    renderMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${message.role}`;
        messageElement.setAttribute('data-message-id', message.id);
        
        const isRTL = message.language === 'ar';
        const direction = isRTL ? 'rtl' : 'ltr';
        
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="content-text" dir="${direction}">${this.formatContent(message.content)}</div>
            </div>
            <div class="message-timestamp">${this.formatTimestamp(message.timestamp)}</div>
            ${message.metadata ? this.renderMetadata(message.metadata) : ''}
        `;
        
        this.chatMessages.appendChild(messageElement);
    }

    renderMetadata(metadata) {
        let html = '<div class="message-metadata">';
        
        if (metadata.intent && metadata.confidence) {
            html += `
                <div class="metadata-intent">
                    <span class="intent-label">Intent:</span>
                    <span class="intent-value">${metadata.intent}</span>
                    <span class="confidence-badge">${Math.round(metadata.confidence * 100)}%</span>
                </div>
            `;
        }
        
        if (metadata.topics && metadata.topics.length > 0) {
            html += `
                <div class="metadata-topics">
                    <span class="topics-label">Topics:</span>
                    <div class="topics-list">
                        ${metadata.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        if (metadata.actions && metadata.actions.length > 0) {
            html += `
                <div class="metadata-actions">
                    <span class="actions-label">Suggested:</span>
                    <div class="actions-list">
                        ${metadata.actions.map(action => `<button class="action-button" data-action="${action}">${action}</button>`).join('')}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }

    formatContent(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message message-assistant';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    updateStatus(text, isOnline) {
        this.statusIndicator.innerHTML = `
            <div class="status-dot" style="background: ${isOnline ? '#10b981' : '#ef4444'};"></div>
            <span class="status-text">${text}</span>
        `;
    }

    changeLanguage(languageCode) {
        const language = SUPPORTED_LANGUAGES.find(lang => lang.code === languageCode);
        if (!language) return;
        
        this.currentLanguage = languageCode;
        
        // Update display
        const flag = this.container.querySelector('#current-flag');
        const name = this.container.querySelector('#current-name');
        if (flag) flag.textContent = language.flag;
        if (name) name.textContent = language.name;
        
        // Update RTL class
        this.container.classList.toggle('rtl', language.rtl);
        
        // Save preference
        localStorage.setItem('expert-chat-language', languageCode);
        
        console.log(`🌐 Language changed to: ${language.name}`);
    }

    getErrorMessage(error) {
        const errorMessages = {
            en: "I'm having trouble connecting right now. Please try again in a moment.",
            ar: "أواجه مشكلة في الاتصال الآن. يرجى المحاولة مرة أخرى بعد لحظة.",
            fr: "J'ai des difficultés de connexion actuellement. Veuillez réessayer dans un moment."
        };
        
        return errorMessages[this.currentLanguage] || errorMessages.en;
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    handleInitializationError(error) {
        console.error('ChatWidget initialization error:', error);
        this.updateStatus('Error', false);
    }
}

// Simplified API Service
class APIService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = 30000;
    }

    async sendMessage(message) {
        const response = await fetch(`${this.baseUrl}/demo/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(message)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    async getHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Simplified Theme Manager
class ThemeManager {
    applyTheme(container) {
        // Theme is handled via CSS
        container.classList.add('theme-light');
    }
}

// Simplified Message Renderer
class MessageRenderer {
    // Methods handled by main ChatWidget
}

// Simplified Language Selector
class LanguageSelector {
    // Methods handled by main ChatWidget
}

// Export for module usage
export { ChatWidget }; 