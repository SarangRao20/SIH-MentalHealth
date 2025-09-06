// Global variables
let selectedMood = null;
let notes = [];

// DOM elements
const noteForm = document.getElementById('noteForm');
const noteText = document.getElementById('noteText');
const charCount = document.getElementById('charCount');
const notesGrid = document.getElementById('notesGrid');
const loadingSpinner = document.getElementById('loadingSpinner');
const emptyState = document.getElementById('emptyState');
const burnOverlay = document.getElementById('burnOverlay');
const toastContainer = document.getElementById('toastContainer');
const moodButtons = document.querySelectorAll('.mood-btn');

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    createFloatingParticles();
});

function initializeApp() {
    fetchNotes();
    updateCharCount();
}

function setupEventListeners() {
    // Form submission
    noteForm.addEventListener('submit', handleNoteSubmission);
    
    // Character count
    noteText.addEventListener('input', updateCharCount);
    
    // Mood selection
    moodButtons.forEach(btn => {
        btn.addEventListener('click', () => selectMood(btn.dataset.mood));
    });
}

// Mood selection
function selectMood(mood) {
    selectedMood = mood;
    moodButtons.forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-mood="${mood}"]`).classList.add('active');
    
    // Add subtle animation
    const selectedBtn = document.querySelector(`[data-mood="${mood}"]`);
    selectedBtn.style.transform = 'scale(0.95)';
    setTimeout(() => {
        selectedBtn.style.transform = '';
    }, 150);
}

// Character count update
function updateCharCount() {
    const count = noteText.value.length;
    charCount.textContent = count;
    
    if (count > 450) {
        charCount.style.color = 'var(--error)';
    } else if (count > 350) {
        charCount.style.color = 'var(--warning)';
    } else {
        charCount.style.color = 'var(--text-secondary)';
    }
}

// Handle form submission
async function handleNoteSubmission(e) {
    e.preventDefault();
    
    const text = noteText.value.trim();
    if (!text) {
        showToast('Please write something before posting!', 'error');
        return;
    }
    
    const submitBtn = noteForm.querySelector('.submit-btn');
    const originalText = submitBtn.innerHTML;
    
    try {
        // Show loading state
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
        submitBtn.disabled = true;
        
        const response = await fetch('/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                note_text: text,
                mood: selectedMood,
                user_id: `user_${Date.now()}` // Simple user identification
            })
        });
        
        if (response.ok) {
            const newNote = await response.json();
            
            // Reset form
            noteText.value = '';
            selectedMood = null;
            moodButtons.forEach(btn => btn.classList.remove('active'));
            updateCharCount();
            
            // Add note to grid with animation
            addNoteToGrid(newNote, true);
            
            showToast('Note posted successfully! 🎉', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to post note', 'error');
        }
    } catch (error) {
        console.error('Error posting note:', error);
        showToast('Something went wrong. Please try again.', 'error');
    } finally {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Fetch notes from API
async function fetchNotes() {
    try {
        showLoading(true);
        
        const response = await fetch('/notes');
        if (response.ok) {
            notes = await response.json();
            displayNotes();
        } else {
            showToast('Failed to load notes', 'error');
            showEmptyState();
        }
    } catch (error) {
        console.error('Error fetching notes:', error);
        showToast('Failed to load notes', 'error');
        showEmptyState();
    } finally {
        showLoading(false);
    }
}

// Display notes
function displayNotes() {
    if (notes.length === 0) {
        showEmptyState();
        return;
    }
    
    notesGrid.innerHTML = '';
    emptyState.style.display = 'none';
    
    notes.forEach((note, index) => {
        setTimeout(() => {
            addNoteToGrid(note);
        }, index * 100); // Stagger animation
    });
}

// Add single note to grid
function addNoteToGrid(note, prepend = false) {
    const noteElement = createNoteElement(note);
    
    if (prepend) {
        notesGrid.insertBefore(noteElement, notesGrid.firstChild);
        // Update notes array
        notes.unshift(note);
    } else {
        notesGrid.appendChild(noteElement);
    }
    
    // Hide empty state if showing
    if (emptyState.style.display !== 'none') {
        emptyState.style.display = 'none';
    }
}

// Create note element
function createNoteElement(note) {
    const noteDiv = document.createElement('div');
    noteDiv.className = `sticky-note${note.mood ? ` mood-${note.mood}` : ''}`;
    noteDiv.dataset.noteId = note.id;
    
    // Add random rotation for more realistic sticky note placement
    if (!note.mood) {
        const randomRotation = (Math.random() - 0.5) * 6; // Random rotation between -3 and 3 degrees
        noteDiv.style.transform = `rotate(${randomRotation}deg)`;
    }
    
    const moodBadge = note.mood ? `
        <div class="note-mood" style="background: var(--${note.mood}-gradient);">
            ${getMoodEmoji(note.mood)} ${note.mood}
        </div>
    ` : '';
    
    const timestamp = new Date(note.timestamp).toLocaleString();
    
    noteDiv.innerHTML = `
        ${moodBadge}
        <div class="note-text">${escapeHtml(note.note_text)}</div>
        <div class="note-footer">
            <span class="note-timestamp">${timestamp}</span>
            <div class="note-actions">
                <button class="action-btn share-btn" onclick="shareNote(${note.id})" title="Share with therapist">
                    <i class="fas fa-share"></i>
                </button>
                <button class="action-btn burn-btn" onclick="burnNote(${note.id})" title="Burn note">
                    <i class="fas fa-fire"></i>
                </button>
            </div>
        </div>
    `;
    
    // Add wiggle animation on hover
    noteDiv.addEventListener('mouseenter', () => {
        noteDiv.style.animation = 'none';
        noteDiv.offsetHeight; // Trigger reflow
        noteDiv.style.animation = 'wiggle 0.5s ease-in-out';
    });
    
    return noteDiv;
}

// Get mood emoji
function getMoodEmoji(mood) {
    const emojis = {
        happy: '😊',
        sad: '😢',
        angry: '😠',
        calm: '😌',
        anxious: '😰',
        excited: '🤩'
    };
    return emojis[mood] || '💭';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Burn note function
async function burnNote(noteId) {
    const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
    if (!noteElement) return;
    
    try {
        // Get the current rotation of the note for the burning animation
        const computedStyle = window.getComputedStyle(noteElement);
        const transform = computedStyle.transform;
        let currentRotation = '0deg';
        
        if (transform && transform !== 'none') {
            const matrix = new DOMMatrixReadOnly(transform);
            const angle = Math.atan2(matrix.b, matrix.a) * (180 / Math.PI);
            currentRotation = `${angle}deg`;
        }
        
        // Set the initial rotation for the burning animation
        noteElement.style.setProperty('--initial-rotation', currentRotation);
        
        // Show burn animation
        showBurnAnimation();
        noteElement.classList.add('burning');
        
        const response = await fetch(`/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Remove from DOM after animation
            setTimeout(() => {
                noteElement.remove();
                // Remove from notes array
                notes = notes.filter(note => note.id !== noteId);
                
                // Show empty state if no notes left
                if (notes.length === 0) {
                    showEmptyState();
                }
            }, 2500); // Extended time for longer burn animation
            
            showToast('Note burned! 🔥', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to burn note', 'error');
            noteElement.classList.remove('burning');
        }
    } catch (error) {
        console.error('Error burning note:', error);
        showToast('Failed to burn note', 'error');
        noteElement.classList.remove('burning');
    } finally {
        // Hide burn animation after longer duration
        setTimeout(() => {
            hideBurnAnimation();
        }, 2000);
    }
}

// Share note function
async function shareNote(noteId) {
    try {
        const response = await fetch(`/notes/${noteId}/share`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('Note shared with your support network! 💝', 'success');
            
            // Update note in array
            const noteIndex = notes.findIndex(note => note.id === noteId);
            if (noteIndex !== -1) {
                notes[noteIndex].shared = true;
            }
            
            // Add visual indicator
            const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
            if (noteElement) {
                const shareBtn = noteElement.querySelector('.share-btn');
                shareBtn.innerHTML = '<i class="fas fa-check"></i>';
                shareBtn.style.background = 'var(--success)';
                shareBtn.disabled = true;
            }
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to share note', 'error');
        }
    } catch (error) {
        console.error('Error sharing note:', error);
        showToast('Failed to share note', 'error');
    }
}

// Show/hide loading state
function showLoading(show) {
    loadingSpinner.style.display = show ? 'block' : 'none';
}

// Show empty state
function showEmptyState() {
    notesGrid.innerHTML = '';
    emptyState.style.display = 'block';
}

// Burn animation
function showBurnAnimation() {
    burnOverlay.style.display = 'flex';
}

function hideBurnAnimation() {
    setTimeout(() => {
        burnOverlay.style.display = 'none';
    }, 1000);
}

// Toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 'exclamation-triangle';
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'toastSlide 0.3s ease-out reverse';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// Create floating particles
function createFloatingParticles() {
    const particlesContainer = document.getElementById('particles');
    const particleCount = 20;
    
    for (let i = 0; i < particleCount; i++) {
        setTimeout(() => {
            createParticle(particlesContainer);
        }, i * 200);
    }
}

function createParticle(container) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    
    // Random properties
    const size = Math.random() * 4 + 2;
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    const duration = Math.random() * 4 + 4;
    const delay = Math.random() * 2;
    
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    particle.style.left = `${x}px`;
    particle.style.top = `${y}px`;
    particle.style.animationDuration = `${duration}s`;
    particle.style.animationDelay = `${delay}s`;
    
    container.appendChild(particle);
    
    // Remove and recreate after animation
    setTimeout(() => {
        particle.remove();
        createParticle(container);
    }, (duration + delay) * 1000);
}

// Add wiggle animation
const style = document.createElement('style');
style.textContent = `
    @keyframes wiggle {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(1deg); }
        75% { transform: rotate(-1deg); }
    }
`;
document.head.appendChild(style);

// Handle window resize for particles
window.addEventListener('resize', () => {
    // Recreate particles with new window dimensions
    const particlesContainer = document.getElementById('particles');
    particlesContainer.innerHTML = '';
    createFloatingParticles();
});

// Add some performance optimizations
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        // Recalculate layouts if needed
    }, 250);
});

// Preload critical animations
document.addEventListener('DOMContentLoaded', () => {
    // Trigger GPU acceleration for smoother animations
    const elements = document.querySelectorAll('.glass-card, .sticky-note, .mood-btn');
    elements.forEach(el => {
        el.style.transform = 'translateZ(0)';
    });
});

// Event delegation for dynamically created notes
// Event delegation for dynamically created notes
notesGrid.addEventListener('click', (e) => {
    const note = e.target.closest('.sticky-note');
    if (!note) return;

    // Ignore clicks on buttons inside the note
    if (e.target.closest('.burn-btn') || e.target.closest('.share-btn')) {
        return;
    }

    const text = note.querySelector('.note-text')?.innerText || "";
    const timestamp = note.querySelector('.note-timestamp')?.innerText || "";
    const noteId = note.dataset.noteId; 
    const moodClass = [...note.classList].find(c => c.startsWith("mood-"))?.replace("mood-", "") || "neutral";

    document.getElementById('modalNoteText').innerText = text;
    document.getElementById('modalNoteTimestamp').innerText = timestamp;

    // store ID + mood on modal
    const modalContent = document.getElementById('noteModalContent');
    modalContent.dataset.noteId = noteId;
    modalContent.className = "note-modal-content"; // reset styles
    modalContent.classList.add(`emotion-${moodClass}`);

    document.getElementById('noteModal').style.display = 'flex';
});



// Close modal
function closeNoteModal() {
    document.getElementById('noteModal').style.display = 'none';
}

// Close when clicking outside modal content
document.getElementById('noteModal').addEventListener('click', (e) => {
    if (e.target.id === 'noteModal') {
        closeNoteModal();
    }
});

// Burn modal note
function burnModalNote() {
    const modal = document.getElementById('noteModal');
    const modalContent = document.getElementById('noteModalContent');
    const noteId = modalContent.dataset.noteId;

    // Play burn animation only in modal
    modalContent.classList.add('burning');

    setTimeout(() => {
        modalContent.classList.remove('burning');
        modal.style.display = 'none';

        if (noteId) {
            // Delete from DB silently
            fetch(`/notes/${noteId}`, { method: 'DELETE' })
                .then(res => {
                    if (res.ok) {
                        // Remove from notes[] array
                        notes = notes.filter(n => n.id != noteId);

                        // Remove from DOM (no burn animation)
                        const noteEl = document.querySelector(`.sticky-note[data-note-id="${noteId}"]`);
                        if (noteEl) noteEl.remove();
                    } else {
                        console.error("Failed to delete note");
                    }
                })
                .catch(err => console.error("Error deleting note:", err));
        }
    }, 2600); // matches your burn animation duration
}




    // Start burn animation on modal
    modalContent.classList.add('burning');

    // After animation → remove note + close modal





