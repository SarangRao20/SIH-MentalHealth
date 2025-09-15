/**
 * MindCare Mental Health Platform - Main JavaScript
 * Global functionality and utilities
 */

// Global configuration
const MindCare = {
    config: {
        animationDuration: 300,
        apiTimeout: 10000,
        maxRetries: 3
    },
    
    // Utility functions
    utils: {
        // Format time ago
        timeAgo: function(timestamp) {
            const now = new Date();
            const past = new Date(timestamp);
            const diffInSeconds = Math.floor((now - past) / 1000);
            
            const intervals = {
                year: 31536000,
                month: 2592000,
                week: 604800,
                day: 86400,
                hour: 3600,
                minute: 60
            };
            
            for (const [unit, seconds] of Object.entries(intervals)) {
                const interval = Math.floor(diffInSeconds / seconds);
                if (interval >= 1) {
                    return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
                }
            }
            
            return 'Just now';
        },
        
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Show notification
        showNotification: function(message, type = 'info', duration = 5000) {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto remove
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        },
        
        // Copy to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    this.showNotification('Copied to clipboard!', 'success', 2000);
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showNotification('Copied to clipboard!', 'success', 2000);
            }
        },
        
        // Validate email
        isValidEmail: function(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        // Sanitize HTML
        sanitizeHTML: function(str) {
            const temp = document.createElement('div');
            temp.textContent = str;
            return temp.innerHTML;
        }
    },
    
    // Animation helpers
    animations: {
        fadeIn: function(element, duration = 300) {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            const fadeEffect = setInterval(() => {
                if (!element.style.opacity) {
                    element.style.opacity = '0';
                }
                if (parseFloat(element.style.opacity) < 1) {
                    element.style.opacity = (parseFloat(element.style.opacity) + 0.1).toString();
                } else {
                    clearInterval(fadeEffect);
                }
            }, duration / 10);
        },
        
        fadeOut: function(element, duration = 300) {
            const fadeEffect = setInterval(() => {
                if (!element.style.opacity) {
                    element.style.opacity = '1';
                }
                if (parseFloat(element.style.opacity) > 0) {
                    element.style.opacity = (parseFloat(element.style.opacity) - 0.1).toString();
                } else {
                    clearInterval(fadeEffect);
                    element.style.display = 'none';
                }
            }, duration / 10);
        },
        
        slideDown: function(element, duration = 300) {
            element.style.height = '0px';
            element.style.overflow = 'hidden';
            element.style.display = 'block';
            
            const startHeight = 0;
            const endHeight = element.scrollHeight;
            const increment = endHeight / (duration / 16);
            
            const slideEffect = setInterval(() => {
                const currentHeight = parseInt(element.style.height);
                if (currentHeight < endHeight) {
                    element.style.height = Math.min(currentHeight + increment, endHeight) + 'px';
                } else {
                    clearInterval(slideEffect);
                    element.style.height = 'auto';
                    element.style.overflow = 'visible';
                }
            }, 16);
        }
    },
    
    // API helpers
    api: {
        request: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: MindCare.config.apiTimeout
            };
            
            const mergedOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                MindCare.utils.showNotification('Network error. Please try again.', 'danger');
                throw error;
            }
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeGlobalFeatures();
});

function initializeGlobalFeatures() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-grow textareas
    const textareas = document.querySelectorAll('textarea[data-auto-grow]');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    // Loading button states
    document.addEventListener('click', function(e) {
        if (e.target.matches('.btn[data-loading]')) {
            const btn = e.target;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            btn.disabled = true;
            
            // Restore button after timeout or form submission
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 3000);
        }
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements with animation classes
    document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right').forEach(el => {
        observer.observe(el);
    });
    
    
    
    // Initialize crisis detection warnings
    initializeCrisisDetection();
    
    // Initialize wellness reminders
    initializeWellnessReminders();
    
    // Initialize offline detection
    initializeOfflineDetection();
}

// Crisis detection system
function initializeCrisisDetection() {
    const crisisKeywords = [
        'suicide', 'kill myself', 'end my life', 'want to die',
        'self harm', 'hurt myself', 'worthless', 'hopeless'
    ];
    
    const textInputs = document.querySelectorAll('textarea, input[type="text"]');
    
    textInputs.forEach(input => {
        input.addEventListener('input', MindCare.utils.debounce(function() {
            const text = this.value.toLowerCase();
            const hasCrisisKeywords = crisisKeywords.some(keyword => text.includes(keyword));
            
            if (hasCrisisKeywords && text.length > 10) {
                showCrisisSupport();
            }
        }, 1000));
    });
}

function showCrisisSupport() {
    // Only show once per session
    if (sessionStorage.getItem('crisisSupportShown')) return;
    
    const supportModal = document.createElement('div');
    supportModal.className = 'modal fade';
    supportModal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-exclamation-triangle"></i> Immediate Support Available
                    </h5>
                </div>
                <div class="modal-body">
                    <p class="lead">We noticed you might be going through a difficult time.</p>
                    <p>If you're having thoughts of self-harm or suicide, please reach out for help immediately:</p>
                    <div class="d-grid gap-2">
                        <a href="tel:988" class="btn btn-danger">
                            <i class="fas fa-phone"></i> Call 988 - Suicide & Crisis Lifeline
                        </a>
                        <a href="sms:741741" class="btn btn-outline-danger">
                            <i class="fas fa-comment"></i> Text HOME to 741741
                        </a>
                        <a href="/chatbot" class="btn btn-outline-primary">
                            <i class="fas fa-comments"></i> Chat with our AI Support
                        </a>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        I'm okay, continue
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(supportModal);
    const modal = new bootstrap.Modal(supportModal);
    modal.show();
    
    sessionStorage.setItem('crisisSupportShown', 'true');
    
    // Remove modal after close
    supportModal.addEventListener('hidden.bs.modal', () => {
        supportModal.remove();
    });
}

// Wellness reminders
function initializeWellnessReminders() {
    // Show wellness reminder after 30 minutes of activity
    let activityTimer = null;
    
    document.addEventListener('click', () => {
        clearTimeout(activityTimer);
        activityTimer = setTimeout(showWellnessReminder, 30 * 60 * 1000);
    });
}

function showWellnessReminder() {
    const lastReminder = localStorage.getItem('lastWellnessReminder');
    const now = Date.now();
    
    // Don't show more than once per hour
    if (lastReminder && (now - parseInt(lastReminder)) < 60 * 60 * 1000) {
        return;
    }
    
    MindCare.utils.showNotification(`
        <strong>Wellness Check!</strong><br>
        You've been active for a while. Consider taking a short break for your mental health.
        <div class="mt-2">
            <a href="/meditation" class="btn btn-sm btn-outline-light me-2">Meditate</a>
            <a href="/chatbot" class="btn btn-sm btn-outline-light">Chat</a>
        </div>
    `, 'info', 10000);
    
    localStorage.setItem('lastWellnessReminder', now.toString());
}





// Offline detection
function initializeOfflineDetection() {
    window.addEventListener('online', () => {
        MindCare.utils.showNotification('Connection restored!', 'success', 3000);
    });
    
    window.addEventListener('offline', () => {
        MindCare.utils.showNotification(
            'You appear to be offline. Some features may not work properly.',
            'warning',
            5000
        );
    });
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    
    // Don't show error notifications for script loading errors
    if (event.error && event.error.stack && !event.error.stack.includes('Script error')) {
        MindCare.utils.showNotification(
            'An unexpected error occurred. Please refresh the page.',
            'danger',
            5000
        );
    }
});



// Export for use in other scripts
window.MindCare = MindCare;
