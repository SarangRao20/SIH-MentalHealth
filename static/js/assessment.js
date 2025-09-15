/**
 * MindCare Assessment Interface
 * Handles assessment forms, progress tracking, and result visualization
 */

class AssessmentInterface {
    constructor() {
        this.currentAssessment = null;
        this.responses = {};
        this.totalQuestions = 0;
        this.answeredQuestions = 0;
        this.timeStarted = null;
        this.autoSaveInterval = null;
        
        this.init();
    }
    
    init() {
        this.detectAssessmentType();
        this.setupEventListeners();
        this.loadSavedResponses();
        this.startTimer();
    }
    
    detectAssessmentType() {
        const assessmentForm = document.getElementById('assessment-form');
        if (assessmentForm) {
            const typeInput = assessmentForm.querySelector('input[name="assessment_type"]');
            this.currentAssessment = typeInput ? typeInput.value : null;
            this.totalQuestions = assessmentForm.querySelectorAll('[data-question]').length;
        }
    }
    
    setupEventListeners() {
        // Radio button changes
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name.startsWith('q')) {
                this.handleQuestionResponse(e.target);
            }
        });
        
        // Form submission
        const assessmentForm = document.getElementById('assessment-form');
        if (assessmentForm) {
            assessmentForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        // Auto-save responses
        this.autoSaveInterval = setInterval(() => {
            this.saveResponses();
        }, 30000); // Save every 30 seconds
        
        // Page visibility change (save on tab switch)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.saveResponses();
            }
        });
        
        // Before unload warning
        window.addEventListener('beforeunload', (e) => {
            if (this.answeredQuestions > 0 && this.answeredQuestions < this.totalQuestions) {
                e.preventDefault();
                e.returnValue = 'You have unsaved assessment progress. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }
    
    handleQuestionResponse(radioInput) {
        const questionNum = radioInput.name;
        const value = parseInt(radioInput.value);
        
        // Store response
        this.responses[questionNum] = value;
        
        // Update progress
        this.updateProgress();
        
        // Visual feedback
        this.highlightQuestion(radioInput);
        
        // Auto-scroll to next question
        this.scrollToNextQuestion(radioInput);
        
        // Save progress
        this.saveResponses();
        
        // Show encouraging messages
        this.showProgressFeedback();
    }
    
    updateProgress() {
        this.answeredQuestions = Object.keys(this.responses).length;
        const percentage = (this.answeredQuestions / this.totalQuestions) * 100;
        
        // Update progress bar
        const progressBar = document.getElementById('progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.textContent = Math.round(percentage) + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Change color based on progress
            if (percentage === 100) {
                progressBar.classList.remove('bg-primary');
                progressBar.classList.add('bg-success');
            }
        }
        
        // Enable/disable submit button
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = this.answeredQuestions < this.totalQuestions;
            
            if (this.answeredQuestions === this.totalQuestions) {
                submitBtn.classList.add('btn-success');
                submitBtn.classList.remove('btn-primary');
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Complete Assessment';
            }
        }
        
        // Update question counters
        this.updateQuestionCounters();
    }
    
    updateQuestionCounters() {
        const questionGroups = document.querySelectorAll('.question-group');
        questionGroups.forEach((group, index) => {
            const questionNum = group.getAttribute('data-question');
            const isAnswered = this.responses.hasOwnProperty(`q${questionNum}`);
            
            if (isAnswered) {
                group.classList.add('answered');
                const counter = group.querySelector('.question-number');
                if (counter) {
                    counter.innerHTML = `<i class="fas fa-check-circle"></i> Question ${parseInt(questionNum) + 1} of ${this.totalQuestions}`;
                }
            }
        });
    }
    
    highlightQuestion(radioInput) {
        const questionGroup = radioInput.closest('.question-group');
        if (questionGroup) {
            questionGroup.classList.add('answered');
            
            // Add success border
            questionGroup.style.borderColor = '#28a745';
            questionGroup.style.boxShadow = '0 0 0 0.2rem rgba(40, 167, 69, 0.25)';
            
            // Remove highlight after animation
            setTimeout(() => {
                questionGroup.style.borderColor = '';
                questionGroup.style.boxShadow = '';
            }, 2000);
        }
    }
    
    scrollToNextQuestion(radioInput) {
        const currentQuestionNum = parseInt(radioInput.name.substring(1));
        const nextQuestionNum = currentQuestionNum + 1;
        const nextQuestion = document.querySelector(`[data-question="${nextQuestionNum}"]`);
        
        if (nextQuestion) {
            setTimeout(() => {
                nextQuestion.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }, 300);
        } else if (this.answeredQuestions === this.totalQuestions) {
            // Scroll to submit button if all questions answered
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                setTimeout(() => {
                    submitBtn.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 300);
            }
        }
    }
    
    showProgressFeedback() {
        const percentage = (this.answeredQuestions / this.totalQuestions) * 100;
        
        if (percentage === 25) {
            this.showMilestone('Great start! You\'re 25% complete.', 'success');
        } else if (percentage === 50) {
            this.showMilestone('Halfway there! Keep going.', 'info');
        } else if (percentage === 75) {
            this.showMilestone('Almost done! Just a few more questions.', 'warning');
        } else if (percentage === 100) {
            this.showMilestone('All questions answered! Ready to submit.', 'success');
        }
    }
    
    showMilestone(message, type) {
        // Don't show duplicate milestones
        if (this.lastMilestone === message) return;
        this.lastMilestone = message;
        
        const milestone = document.createElement('div');
        milestone.className = `alert alert-${type} milestone-alert`;
        milestone.innerHTML = `
            <i class="fas fa-trophy"></i> ${message}
        `;
        
        // Insert after progress bar
        const progressBar = document.querySelector('.progress');
        if (progressBar && progressBar.parentNode) {
            progressBar.parentNode.insertBefore(milestone, progressBar.nextSibling);
            
            // Remove after 3 seconds
            setTimeout(() => {
                if (milestone.parentNode) {
                    milestone.remove();
                }
            }, 3000);
        }
    }
    
    handleSubmit(e) {
        e.preventDefault();
        
        // Final validation
        if (this.answeredQuestions < this.totalQuestions) {
            this.showValidationError('Please answer all questions before submitting.');
            return;
        }
        
        // Calculate time taken
        const timeElapsed = this.timeStarted ? Date.now() - this.timeStarted : 0;
        
        // Show confirmation modal
        this.showSubmissionConfirmation(timeElapsed);
    }
    
    showSubmissionConfirmation(timeElapsed) {
        const minutes = Math.floor(timeElapsed / 60000);
        const seconds = Math.floor((timeElapsed % 60000) / 1000);
        
        const modal = document.getElementById('confirmModal');
        if (modal) {
            // Update modal content with summary
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="text-center">
                        <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                        <h5>Assessment Complete!</h5>
                        <p>You've answered all ${this.totalQuestions} questions.</p>
                        <div class="row mt-3">
                            <div class="col-6">
                                <div class="border p-2 rounded">
                                    <small class="text-muted">Time taken</small>
                                    <div class="fw-bold">${minutes}m ${seconds}s</div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="border p-2 rounded">
                                    <small class="text-muted">Assessment</small>
                                    <div class="fw-bold">${this.currentAssessment}</div>
                                </div>
                            </div>
                        </div>
                        <p class="text-muted mt-3 small">
                            You won't be able to change your answers after submission, 
                            but you can take the assessment again later.
                        </p>
                    </div>
                `;
            }
            
            new bootstrap.Modal(modal).show();
        } else {
            // Fallback if modal not found
            this.submitForm();
        }
    }
    
    submitForm() {
        const form = document.getElementById('assessment-form');
        if (form) {
            // Clear auto-save data
            this.clearSavedResponses();
            
            // Add loading state
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
                submitBtn.disabled = true;
            }
            
            // Submit form
            form.submit();
        }
    }
    
    showValidationError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of form
        const form = document.getElementById('assessment-form');
        if (form) {
            form.insertBefore(alert, form.firstChild);
            
            // Scroll to alert
            alert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    saveResponses() {
        if (Object.keys(this.responses).length === 0) return;
        
        const saveData = {
            assessment: this.currentAssessment,
            responses: this.responses,
            timeStarted: this.timeStarted,
            timestamp: Date.now()
        };
        
        try {
            localStorage.setItem('mindcare-assessment-progress', JSON.stringify(saveData));
        } catch (error) {
            console.error('Failed to save assessment progress:', error);
        }
    }
    
    loadSavedResponses() {
        try {
            const saved = localStorage.getItem('mindcare-assessment-progress');
            if (!saved) return;
            
            const saveData = JSON.parse(saved);
            
            // Only load if it's the same assessment and within last hour
            if (saveData.assessment === this.currentAssessment && 
                Date.now() - saveData.timestamp < 3600000) {
                
                this.responses = saveData.responses;
                this.timeStarted = saveData.timeStarted;
                
                // Restore radio selections
                Object.entries(this.responses).forEach(([questionName, value]) => {
                    const radio = document.querySelector(`input[name="${questionName}"][value="${value}"]`);
                    if (radio) {
                        radio.checked = true;
                        this.highlightQuestion(radio);
                    }
                });
                
                this.updateProgress();
                
                // Show restoration message
                if (Object.keys(this.responses).length > 0) {
                    this.showRestorationMessage();
                }
            }
        } catch (error) {
            console.error('Failed to load saved assessment progress:', error);
        }
    }
    
    showRestorationMessage() {
        if (window.MindCare && window.MindCare.utils) {
            window.MindCare.utils.showNotification(
                `Restored your previous progress (${this.answeredQuestions}/${this.totalQuestions} questions answered)`,
                'info',
                5000
            );
        }
    }
    
    clearSavedResponses() {
        try {
            localStorage.removeItem('mindcare-assessment-progress');
        } catch (error) {
            console.error('Failed to clear saved responses:', error);
        }
    }
    
    startTimer() {
        this.timeStarted = Date.now();
    }
    
    // Assessment results page functionality
    initializeResultsPage() {
        this.setupResultsInteractions();
        this.animateResults();
    }
    
    setupResultsInteractions() {
        // Print functionality
        const printBtn = document.querySelector('button[onclick="window.print()"]');
        if (printBtn) {
            printBtn.addEventListener('click', () => {
                // Add print-specific styles
                document.body.classList.add('printing');
                window.print();
                document.body.classList.remove('printing');
            });
        }
        
        // Share functionality
        if (navigator.share) {
            const shareBtn = document.querySelector('button[onclick="shareResults()"]');
            if (shareBtn) {
                shareBtn.addEventListener('click', this.handleNativeShare);
            }
        }
    }
    
    animateResults() {
        // Animate score display
        const scoreElement = document.querySelector('.display-4');
        if (scoreElement) {
            const finalScore = parseInt(scoreElement.textContent);
            this.animateNumber(scoreElement, 0, finalScore, 1500);
        }
        
        // Stagger animation of recommendation cards
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.5s ease';
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 100);
        });
    }
    
    animateNumber(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            element.textContent = Math.round(current);
            
            if (current >= end) {
                element.textContent = end;
                clearInterval(timer);
            }
        }, 16);
    }
    
    async handleNativeShare() {
        try {
            await navigator.share({
                title: 'My Mental Health Assessment Results',
                text: 'I completed a mental health assessment on MindCare.',
                url: window.location.href
            });
        } catch (error) {
            console.error('Error sharing:', error);
            // Fallback to copy URL
            if (window.MindCare && window.MindCare.utils) {
                window.MindCare.utils.copyToClipboard(window.location.href);
            }
        }
    }
    
    // Cleanup
    destroy() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        
        window.removeEventListener('beforeunload', this.beforeUnloadHandler);
    }
}

// Global functions for template usage
function submitForm() {
    if (window.assessmentInterface) {
        window.assessmentInterface.submitForm();
    }
}

function shareResults() {
    if (window.assessmentInterface) {
        window.assessmentInterface.handleNativeShare();
    }
}

function viewResults(assessmentId) {
    // Navigate to results page
    window.location.href = `/assessment_results/${assessmentId}`;
}

// Initialize assessment interface when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const assessmentForm = document.getElementById('assessment-form');
    const resultsPage = document.querySelector('.assessment-results');
    
    if (assessmentForm) {
        window.assessmentInterface = new AssessmentInterface();
    } else if (resultsPage) {
        window.assessmentInterface = new AssessmentInterface();
        window.assessmentInterface.initializeResultsPage();
    }
});

// Add CSS for assessment interface
const assessmentStyle = document.createElement('style');
assessmentStyle.textContent = `
.question-group.answered {
    border-color: #28a745 !important;
    background: linear-gradient(135deg, rgba(40, 167, 69, 0.05) 0%, rgba(255, 255, 255, 1) 100%);
}

.question-group.answered .question-number {
    color: #28a745 !important;
}

.milestone-alert {
    position: sticky;
    top: 20px;
    z-index: 10;
    animation: milestone-bounce 0.5s ease;
    margin: 10px 0;
}

@keyframes milestone-bounce {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.form-check:hover {
    background: rgba(0, 123, 255, 0.05);
    border-radius: 5px;
}

.form-check-input:checked ~ .form-check-label {
    color: #007bff;
    font-weight: 600;
}

.progress {
    height: 12px;
    border-radius: 10px;
    overflow: hidden;
    background: #e9ecef;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}

.progress-bar {
    transition: all 0.5s ease;
    background: linear-gradient(45deg, #007bff, #0056b3);
    position: relative;
    overflow: hidden;
}

.progress-bar::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: progress-shine 2s infinite;
}

@keyframes progress-shine {
    0% { left: -100%; }
    100% { left: 100%; }
}

@media print {
    .milestone-alert,
    .btn,
    .modal,
    .alert-dismissible {
        display: none !important;
    }
    
    .question-group {
        break-inside: avoid;
        margin-bottom: 20px;
    }
    
    .form-check-input:checked ~ .form-check-label::after {
        content: ' ✓';
        color: #28a745;
        font-weight: bold;
    }
}

.printing .card-footer,
.printing .modal,
.printing .btn:not(.btn-print) {
    display: none !important;
}

.assessment-results .metric-value {
    animation: count-up 1.5s ease-out;
}

@keyframes count-up {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
}
`;
document.head.appendChild(assessmentStyle);
