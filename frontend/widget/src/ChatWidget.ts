/**
 * Expert Company AI Assistant Chat Widget
 * 
 * A modern, responsive chat widget for websites with multilingual support
 * and real-time conversation capabilities.
 */

import { I18n } from './utils/i18n';
import { ApiService } from './services/ApiService';
import { WebSocketService } from './services/WebSocketService';
import { ThemeManager } from './utils/ThemeManager';
import { MessageRenderer } from './components/MessageRenderer';
import { LanguageSelector } from './components/LanguageSelector';

export interface WidgetConfig {
    apiUrl: string;
    websocketUrl?: string;
    sessionId?: string;
    language?: string;
    theme?: 'light' | 'dark' | 'auto';
    position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
    welcomeMessage?: string;
    enableVoice?: boolean;
    enableFileUpload?: boolean;
    brandColor?: string;
    brandName?: string;
    autoDetectLanguage?: boolean;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    language?: string;
    metadata?: Record<string, any>;
}

export class ChatWidget {
    private config: WidgetConfig;
    private container: HTMLElement;
    private chatContainer: HTMLElement;
    private messagesContainer: HTMLElement;
    private inputContainer: HTMLElement;
    private messageInput: HTMLInputElement;
    private sendButton: HTMLButtonElement;
    private toggleButton: HTMLButtonElement;
    private headerContainer: HTMLElement;
    
    private i18n: I18n;
    private apiService: ApiService;
    private webSocketService: WebSocketService;
    private themeManager: ThemeManager;
    private messageRenderer: MessageRenderer;
    private languageSelector: LanguageSelector;
    
    private isOpen: boolean = false;
    private isConnected: boolean = false;
    private messages: ChatMessage[] = [];
    private sessionId: string;
    private currentLanguage: string;
    private isTyping: boolean = false;

    constructor(config: WidgetConfig) {
        this.config = {
            language: 'en',
            theme: 'auto',
            position: 'bottom-right',
            welcomeMessage: 'Hello! How can I help you today?',
            enableVoice: false,
            enableFileUpload: false,
            brandColor: '#007bff',
            brandName: 'Expert Company',
            autoDetectLanguage: true,
            ...config
        };

        this.sessionId = this.config.sessionId || this.generateSessionId();
        this.currentLanguage = this.config.language || 'en';

        this.initializeServices();
        this.createWidget();
        this.setupEventListeners();
        this.loadStoredMessages();

        if (this.config.autoDetectLanguage) {
            this.detectBrowserLanguage();
        }
    }

    private initializeServices(): void {
        this.i18n = new I18n(this.currentLanguage);
        this.apiService = new ApiService(this.config.apiUrl);
        this.themeManager = new ThemeManager(this.config.theme);
        this.messageRenderer = new MessageRenderer(this.i18n);
        this.languageSelector = new LanguageSelector(this.i18n, (lang) => this.changeLanguage(lang));

        if (this.config.websocketUrl) {
            this.webSocketService = new WebSocketService(
                this.config.websocketUrl,
                this.sessionId,
                this.handleWebSocketMessage.bind(this),
                this.handleWebSocketConnect.bind(this),
                this.handleWebSocketDisconnect.bind(this)
            );
        }
    }

    private createWidget(): void {
        // Create main container
        this.container = document.createElement('div');
        this.container.className = 'expert-chat-widget';
        this.container.setAttribute('data-position', this.config.position);
        
        // Create toggle button
        this.createToggleButton();
        
        // Create chat container
        this.createChatContainer();
        
        // Apply theme
        this.themeManager.applyTheme(this.container);
        
        // Add to DOM
        document.body.appendChild(this.container);
    }

    private createToggleButton(): void {
        this.toggleButton = document.createElement('button');
        this.toggleButton.className = 'expert-chat-toggle';
        this.toggleButton.innerHTML = `
            <svg class="chat-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
            </svg>
            <svg class="close-icon" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
        `;
        
        this.container.appendChild(this.toggleButton);
    }

    private createChatContainer(): void {
        this.chatContainer = document.createElement('div');
        this.chatContainer.className = 'expert-chat-container';
        this.chatContainer.style.display = 'none';
        
        // Create header
        this.createHeader();
        
        // Create messages container
        this.createMessagesContainer();
        
        // Create input container
        this.createInputContainer();
        
        this.container.appendChild(this.chatContainer);
        
        // Add welcome message
        this.addWelcomeMessage();
    }

    private createHeader(): void {
        this.headerContainer = document.createElement('div');
        this.headerContainer.className = 'expert-chat-header';
        
        const brandInfo = document.createElement('div');
        brandInfo.className = 'brand-info';
        brandInfo.innerHTML = `
            <div class="brand-name">${this.config.brandName}</div>
            <div class="brand-status">
                <span class="status-indicator ${this.isConnected ? 'connected' : 'disconnected'}"></span>
                <span class="status-text">${this.i18n.t(this.isConnected ? 'connected' : 'connecting')}</span>
            </div>
        `;
        
        const headerActions = document.createElement('div');
        headerActions.className = 'header-actions';
        
        // Add language selector
        const languageSelectorContainer = document.createElement('div');
        languageSelectorContainer.className = 'language-selector-container';
        this.languageSelector.render(languageSelectorContainer);
        headerActions.appendChild(languageSelectorContainer);
        
        // Add minimize button
        const minimizeButton = document.createElement('button');
        minimizeButton.className = 'minimize-button';
        minimizeButton.innerHTML = '−';
        minimizeButton.onclick = () => this.toggle();
        headerActions.appendChild(minimizeButton);
        
        this.headerContainer.appendChild(brandInfo);
        this.headerContainer.appendChild(headerActions);
        this.chatContainer.appendChild(this.headerContainer);
    }

    private createMessagesContainer(): void {
        this.messagesContainer = document.createElement('div');
        this.messagesContainer.className = 'expert-chat-messages';
        this.chatContainer.appendChild(this.messagesContainer);
    }

    private createInputContainer(): void {
        this.inputContainer = document.createElement('div');
        this.inputContainer.className = 'expert-chat-input';
        
        // Create typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.style.display = 'none';
        typingIndicator.innerHTML = `
            <span class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </span>
            <span class="typing-text">${this.i18n.t('typing')}</span>
        `;
        this.inputContainer.appendChild(typingIndicator);
        
        // Create input form
        const inputForm = document.createElement('form');
        inputForm.className = 'input-form';
        
        this.messageInput = document.createElement('input');
        this.messageInput.type = 'text';
        this.messageInput.className = 'message-input';
        this.messageInput.placeholder = this.i18n.t('placeholder');
        this.messageInput.dir = this.i18n.isRTL() ? 'rtl' : 'ltr';
        
        this.sendButton = document.createElement('button');
        this.sendButton.type = 'submit';
        this.sendButton.className = 'send-button';
        this.sendButton.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
        `;
        
        inputForm.appendChild(this.messageInput);
        inputForm.appendChild(this.sendButton);
        this.inputContainer.appendChild(inputForm);
        
        this.chatContainer.appendChild(this.inputContainer);
    }

    private setupEventListeners(): void {
        // Toggle button
        this.toggleButton.addEventListener('click', () => this.toggle());
        
        // Message form
        const inputForm = this.inputContainer.querySelector('.input-form') as HTMLFormElement;
        inputForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Keyboard shortcuts
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize input
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
        
        // Theme changes
        this.themeManager.onThemeChange((theme) => {
            this.container.setAttribute('data-theme', theme);
        });
        
        // Language changes
        this.i18n.onLanguageChange(() => {
            this.updateUI();
        });
    }

    private generateSessionId(): string {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }

    private detectBrowserLanguage(): void {
        const browserLang = navigator.language.substring(0, 2);
        const supportedLanguages = ['en', 'ar', 'fr'];
        
        if (supportedLanguages.includes(browserLang) && browserLang !== this.currentLanguage) {
            this.changeLanguage(browserLang);
        }
    }

    private addWelcomeMessage(): void {
        const welcomeMessage: ChatMessage = {
            id: 'welcome_' + Date.now(),
            role: 'assistant',
            content: this.i18n.t('welcome_message') || this.config.welcomeMessage,
            timestamp: Date.now(),
            language: this.currentLanguage
        };
        
        this.addMessage(welcomeMessage);
    }

    private addMessage(message: ChatMessage): void {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
        this.saveMessages();
    }

    private renderMessage(message: ChatMessage): void {
        const messageElement = this.messageRenderer.render(message);
        this.messagesContainer.appendChild(messageElement);
    }

    private scrollToBottom(): void {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }

    private async sendMessage(): Promise<void> {
        const messageText = this.messageInput.value.trim();
        if (!messageText) return;
        
        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // Add user message
        const userMessage: ChatMessage = {
            id: 'user_' + Date.now(),
            role: 'user',
            content: messageText,
            timestamp: Date.now(),
            language: this.currentLanguage
        };
        
        this.addMessage(userMessage);
        this.showTypingIndicator();
        
        try {
            // Send via WebSocket if available, otherwise use API
            if (this.webSocketService && this.isConnected) {
                this.webSocketService.sendMessage(messageText, this.currentLanguage);
            } else {
                await this.sendMessageViaAPI(messageText);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showErrorMessage();
        } finally {
            this.hideTypingIndicator();
        }
    }

    private async sendMessageViaAPI(message: string): Promise<void> {
        const response = await this.apiService.sendMessage(message, this.currentLanguage);
        
        const assistantMessage: ChatMessage = {
            id: 'assistant_' + Date.now(),
            role: 'assistant',
            content: response.response,
            timestamp: Date.now(),
            language: response.language,
            metadata: {
                intent: response.intent,
                confidence: response.confidence
            }
        };
        
        this.addMessage(assistantMessage);
    }

    private handleWebSocketMessage(data: any): void {
        const assistantMessage: ChatMessage = {
            id: 'assistant_' + Date.now(),
            role: 'assistant',
            content: data.content,
            timestamp: Date.now(),
            language: data.language,
            metadata: data.metadata
        };
        
        this.addMessage(assistantMessage);
    }

    private handleWebSocketConnect(): void {
        this.isConnected = true;
        this.updateConnectionStatus();
    }

    private handleWebSocketDisconnect(): void {
        this.isConnected = false;
        this.updateConnectionStatus();
    }

    private updateConnectionStatus(): void {
        const statusIndicator = this.headerContainer.querySelector('.status-indicator') as HTMLElement;
        const statusText = this.headerContainer.querySelector('.status-text') as HTMLElement;
        
        if (this.isConnected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = this.i18n.t('connected');
        } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = this.i18n.t('connecting');
        }
    }

    private showTypingIndicator(): void {
        const typingIndicator = this.inputContainer.querySelector('.typing-indicator') as HTMLElement;
        typingIndicator.style.display = 'flex';
        this.isTyping = true;
    }

    private hideTypingIndicator(): void {
        const typingIndicator = this.inputContainer.querySelector('.typing-indicator') as HTMLElement;
        typingIndicator.style.display = 'none';
        this.isTyping = false;
    }

    private showErrorMessage(): void {
        const errorMessage: ChatMessage = {
            id: 'error_' + Date.now(),
            role: 'system',
            content: this.i18n.t('error_message'),
            timestamp: Date.now(),
            language: this.currentLanguage
        };
        
        this.addMessage(errorMessage);
    }

    private changeLanguage(language: string): void {
        this.currentLanguage = language;
        this.i18n.setLanguage(language);
        this.updateUI();
    }

    private updateUI(): void {
        // Update input placeholder
        this.messageInput.placeholder = this.i18n.t('placeholder');
        this.messageInput.dir = this.i18n.isRTL() ? 'rtl' : 'ltr';
        
        // Update chat container direction
        this.chatContainer.dir = this.i18n.isRTL() ? 'rtl' : 'ltr';
        
        // Update connection status
        this.updateConnectionStatus();
        
        // Update typing indicator text
        const typingText = this.inputContainer.querySelector('.typing-text') as HTMLElement;
        if (typingText) {
            typingText.textContent = this.i18n.t('typing');
        }
    }

    private saveMessages(): void {
        try {
            localStorage.setItem(
                `expert_chat_messages_${this.sessionId}`,
                JSON.stringify(this.messages.slice(-50)) // Keep last 50 messages
            );
        } catch (error) {
            console.warn('Failed to save messages to localStorage:', error);
        }
    }

    private loadStoredMessages(): void {
        try {
            const stored = localStorage.getItem(`expert_chat_messages_${this.sessionId}`);
            if (stored) {
                const messages = JSON.parse(stored) as ChatMessage[];
                messages.forEach(message => this.renderMessage(message));
                this.messages = messages;
                this.scrollToBottom();
            }
        } catch (error) {
            console.warn('Failed to load messages from localStorage:', error);
        }
    }

    // Public API methods

    public toggle(): void {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    public open(): void {
        this.isOpen = true;
        this.chatContainer.style.display = 'flex';
        this.toggleButton.querySelector('.chat-icon').style.display = 'none';
        this.toggleButton.querySelector('.close-icon').style.display = 'block';
        this.container.classList.add('open');
        
        // Focus input
        setTimeout(() => {
            this.messageInput.focus();
        }, 100);
        
        // Connect WebSocket if available
        if (this.webSocketService && !this.isConnected) {
            this.webSocketService.connect();
        }
    }

    public close(): void {
        this.isOpen = false;
        this.chatContainer.style.display = 'none';
        this.toggleButton.querySelector('.chat-icon').style.display = 'block';
        this.toggleButton.querySelector('.close-icon').style.display = 'none';
        this.container.classList.remove('open');
    }

    public setLanguage(language: string): void {
        this.changeLanguage(language);
    }

    public sendSystemMessage(message: string): void {
        const systemMessage: ChatMessage = {
            id: 'system_' + Date.now(),
            role: 'system',
            content: message,
            timestamp: Date.now(),
            language: this.currentLanguage
        };
        
        this.addMessage(systemMessage);
    }

    public clearMessages(): void {
        this.messages = [];
        this.messagesContainer.innerHTML = '';
        this.addWelcomeMessage();
        this.saveMessages();
    }

    public destroy(): void {
        if (this.webSocketService) {
            this.webSocketService.disconnect();
        }
        
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
    }
}

// Export for global usage
declare global {
    interface Window {
        ExpertChatWidget: typeof ChatWidget;
    }
}

if (typeof window !== 'undefined') {
    window.ExpertChatWidget = ChatWidget;
} 