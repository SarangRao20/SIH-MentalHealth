/**
 * MindCare Chatbot Interface
 * Handles chat functionality, crisis detection, and voice integration
 */

class ChatbotInterface {
    constructor() {
        this.sessionId = null;
        this.isTyping = false;
        this.messageQueue = [];
        this.crisisDetected = false;
        this.voiceEnabled = false;
        
        this.init();
    }
    
    init() {
        this.sessionId = document.querySelector('input[name="session_id"]')?.value;
        this.setupEventListeners();
        this.scrollToBottom();
        this.showWelcomeMessage();
    }
    
    setupEventListeners() {
        const chatForm = document.getElementById('chat-form');
        const messageInput = document.getElementById('message-input');
        
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSubmit(e);
                }
            });
            
            // Auto-resize textarea
            messageInput.addEventListener('input', () => {
                messageInput.style.height = 'auto';
                messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
            });
            
            // Show typing indicator
            messageInput.addEventListener('input', MindCare.utils.debounce(() => {
                this.detectCrisisKeywords(messageInput.value);
            }, 500));
        }
        
        // Handle voice button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('#voice-btn, #voice-btn *')) {
                this.toggleVoice();
            }
        });
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Clear input and disable submit button
        messageInput.value = '';
        messageInput.style.height = 'auto';
        this.setSubmitButtonState(true);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send message to server
            const response = await this.sendMessage(message);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessage(response.bot_message, 'bot');
            
            // Handle crisis detection
            if (response.crisis_detected) {
                this.handleCrisisDetection(response);
            }
            
            // Handle assessment suggestions
            if (response.assessment_suggestion) {
                this.showAssessmentSuggestion(response.assessment_suggestion);
            }
            
            // Speak response if voice is enabled
            if (this.voiceEnabled && response.bot_message) {
                this.speakMessage(response.bot_message);
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addMessage(
                'I apologize, but I\'m having trouble connecting right now. Please try again or contact support if you need immediate help.',
                'bot',
                true
            );
        } finally {
            this.setSubmitButtonState(false);
            messageInput.focus();
        }
    }
    
    async sendMessage(message) {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('session_id', this.sessionId);
        
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    addMessage(content, type, isError = false) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timestamp = new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble ${isError ? 'error' : ''}">
                <div class="message-content">${this.formatMessage(content)}</div>
                <small class="message-time text-muted d-block mt-1">${timestamp}</small>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Animate message in
        setTimeout(() => {
            messageDiv.classList.add('animate-in');
        }, 10);
    }
    
    formatMessage(content) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        content = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        // Convert line breaks to <br>
        content = content.replace(/\n/g, '<br>');
        
        // Highlight important words
        const importantWords = ['important', 'urgent', 'help', 'support', 'crisis'];
        importantWords.forEach(word => {
            const regex = new RegExp(`\\b(${word})\\b`, 'gi');
            content = content.replace(regex, '<strong>$1</strong>');
        });
        
        return content;
    }
    
    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    showWelcomeMessage() {
        const chatMessages = document.getElementById('chat-messages');
        const messages = chatMessages.querySelectorAll('.message');
        
        if (messages.length === 0) {
            setTimeout(() => {
                this.addMessage(
                    "Hello! I'm here to provide mental health support and listen to whatever you'd like to share. How are you feeling today?",
                    'bot'
                );
            }, 500);
        }
    }
    
    detectCrisisKeywords(text) {
        const crisisKeywords = [
            'suicide', 'kill myself', 'end my life', 'want to die',
            'self harm', 'hurt myself', 'worthless', 'hopeless',
            'better off dead', 'end it all'
        ];
        
        const textLower = text.toLowerCase();
        const hasCrisisKeywords = crisisKeywords.some(keyword => textLower.includes(keyword));
        
        if (hasCrisisKeywords && text.length > 10 && !this.crisisDetected) {
            this.showCrisisAlert();
            this.crisisDetected = true;
        }
    }
    
    handleCrisisDetection(response) {
        this.showCrisisAlert();
        
        // Add special crisis support message
        setTimeout(() => {
            this.addMessage(
                `I'm concerned about what you've shared. Your safety is important. Please consider reaching out for immediate support:
                
                🔴 Crisis Hotline: <a href="tel:988">988</a>
                📱 Text Support: <a href="sms:741741">Text HOME to 741741</a>
                💬 Online Chat: <a href="/consultation">Request Professional Help</a>
                
                Would you like to talk about what's troubling you?`,
                'bot'
            );
        }, 1000);
    }
    
    showCrisisAlert() {
        const alertDiv = document.getElementById('crisis-alert');
        if (alertDiv) {
            alertDiv.classList.remove('d-none');
            
            // Scroll alert into view
            alertDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Add pulse animation
            alertDiv.classList.add('crisis-pulse');
        }
    }
    
    showAssessmentSuggestion(suggestion) {
        const suggestionDiv = document.getElementById('assessment-suggestion');
        const reasonDiv = document.getElementById('assessment-reason');
        const buttonDiv = document.getElementById('take-assessment-btn');
        
        if (suggestionDiv && suggestion.suggested_assessment !== 'none') {
            reasonDiv.textContent = suggestion.reason;
            buttonDiv.href = `/assessment/${suggestion.suggested_assessment}`;
            buttonDiv.innerHTML = `<i class="fas fa-clipboard-check"></i> Take ${suggestion.suggested_assessment}`;
            
            suggestionDiv.classList.remove('d-none');
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                suggestionDiv.classList.add('d-none');
            }, 10000);
        }
    }
    
    async speakMessage(text) {
        try {
            const response = await fetch('/voice_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.audio_url) {
                    const audio = new Audio(data.audio_url);
                    audio.play();
                }
            }
        } catch (error) {
            console.error('Voice synthesis error:', error);
        }
    }
    
    toggleVoice() {
        this.voiceEnabled = !this.voiceEnabled;
        const voiceBtn = document.getElementById('voice-btn');
        const voiceStatus = document.getElementById('voice-status');
        
        if (voiceBtn) {
            if (this.voiceEnabled) {
                voiceBtn.classList.add('btn-success');
                voiceBtn.classList.remove('btn-primary');
                voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                if (voiceStatus) {
                    voiceStatus.innerHTML = '<small class="text-success"><i class="fas fa-volume-up"></i> Voice enabled</small>';
                }
            } else {
                voiceBtn.classList.add('btn-primary');
                voiceBtn.classList.remove('btn-success');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                if (voiceStatus) {
                    voiceStatus.innerHTML = '<small class="text-muted"><i class="fas fa-volume-mute"></i> Voice disabled</small>';
                }
            }
        }
    }
    
    setSubmitButtonState(disabled) {
        const submitBtn = document.getElementById('send-btn');
        if (submitBtn) {
            submitBtn.disabled = disabled;
            if (disabled) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            } else {
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            }
        }
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }
    
    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages && confirm('Are you sure you want to clear the chat history?')) {
            chatMessages.innerHTML = '';
            this.crisisDetected = false;
            
            // Hide alerts
            const crisisAlert = document.getElementById('crisis-alert');
            const assessmentSuggestion = document.getElementById('assessment-suggestion');
            
            if (crisisAlert) crisisAlert.classList.add('d-none');
            if (assessmentSuggestion) assessmentSuggestion.classList.add('d-none');
            
            // Show welcome message again
            this.showWelcomeMessage();
        }
    }
}

// Global functions for template usage
function sendMessage(event) {
    if (window.chatbot) {
        window.chatbot.handleSubmit(event);
    }
}

function clearChat() {
    if (window.chatbot) {
        window.chatbot.clearChat();
    }
}

function toggleVoice() {
    if (window.chatbot) {
        window.chatbot.toggleVoice();
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('chat-messages')) {
        window.chatbot = new ChatbotInterface();
    }
});

// Add CSS for typing indicator
const style = document.createElement('style');
style.textContent = `
.typing-indicator .message-bubble {
    background: #f8f9fa !important;
    border: 1px solid #dee2e6;
}

.typing-dots {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 8px 0;
}

.typing-dots span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007bff;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
}

.crisis-pulse {
    animation: crisis-pulse 1s ease-in-out infinite;
}

@keyframes crisis-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

.message.animate-in {
    animation: slideInMessage 0.3s ease-out;
}

@keyframes slideInMessage {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-bubble.error {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
    border: 1px solid #f5c6cb !important;
    color: #721c24 !important;
}
`;
document.head.appendChild(style);
