document.addEventListener('DOMContentLoaded', () => {
    // Get meditation video element
    const meditationVideo = document.getElementById('meditation-video');
    const durationSelectionArea = document.getElementById('duration-selection-area');
    const timerDisplayArea = document.getElementById('timer-display-area');
    const startSessionButtons = document.querySelectorAll('.start-session');
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const stopBtn = document.getElementById('stopBtn');
    const timerDisplay = document.getElementById('timer');
    // Use the new breathing instruction text inside Lottie
    const breathingInstructionText = document.getElementById('breathing-instruction-text');

    let timerInterval;
    let timeLeft = 0; // Will be set by duration cards
    let initialTime = 0; // To store the initially selected duration for reset
    let isPaused = false;
    let audio = new Audio(); // Initialize Audio object without a source
    const meditationNotification = document.getElementById('meditation-notification'); // Get notification element

    // Breathing animation states
    const breathingStates = ["Breathe In", "Hold", "Breathe Out", "Hold"];
    let breathingStateIndex = 0;
    let breathingInterval;

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function updateTimerDisplay() {
        timerDisplay.textContent = formatTime(timeLeft);
    }

    function startBreathingAnimation() {
        if (breathingInstructionText) {
            breathingInterval = setInterval(() => {
                breathingStateIndex = (breathingStateIndex + 1) % breathingStates.length;
                breathingInstructionText.textContent = breathingStates[breathingStateIndex];
            }, 2000); // Change instruction every 2 seconds
        }
    }

    function stopBreathingAnimation() {
        clearInterval(breathingInterval);
        if (breathingInstructionText) {
            breathingInstructionText.textContent = "Breathe In"; // Reset instruction
        }
    }

    function startTimer() {
        if (timerInterval) {
            clearInterval(timerInterval); // Prevent multiple intervals
        }
        isPaused = false;
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        stopBtn.disabled = false;

        audio.play().catch(e => console.error("Error playing audio:", e));
        if (meditationVideo) {
            meditationVideo.play();
        }
        startBreathingAnimation();

        timerInterval = setInterval(() => {
            if (!isPaused) {
                timeLeft--;
                updateTimerDisplay();
                if (timeLeft <= 0) {
                    clearInterval(timerInterval);
                    timerInterval = null;
                    audio.pause();
                    audio.currentTime = 0;
                    sendCompletionSignal();
                    resetMeditation();
                }
            }
        }, 1000);
    }

    function pauseTimer() {
        isPaused = true;
        audio.pause();
        if (meditationVideo) {
            meditationVideo.pause();
        }
        stopBreathingAnimation();
        startBtn.disabled = false; // Allow resuming
        pauseBtn.disabled = true;
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        audio.pause();
        audio.currentTime = 0;
        if (meditationVideo) {
            meditationVideo.pause();
            meditationVideo.currentTime = 0;
        }
        stopBreathingAnimation();
    // Do NOT send completion signal or update stats on manual stop
    resetMeditation();
    }

    function resetMeditation() {
        clearInterval(timerInterval); // Ensure timer is stopped
        audio.pause();
        audio.currentTime = 0;
        if (meditationVideo) {
            meditationVideo.pause();
            meditationVideo.currentTime = 0;
        }
        stopBreathingAnimation();

        timeLeft = initialTime; // Reset to the initially selected duration
        isPaused = false;
        updateTimerDisplay();
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        stopBtn.disabled = true;

        // Show duration selection, hide timer controls
        durationSelectionArea.style.display = 'block';
        timerDisplayArea.style.display = 'none';
        if (breathingInstructionText) {
            breathingInstructionText.textContent = "Breathe In"; // Reset initial instruction
        }

        // Remove 'selected' class from all duration cards
        // (Removed as it's not applicable to buttons)
    }

    // Update today's progress UI
    function updateMeditationStats(data) {
        // Update weekly sessions count
        const weeklySessionsElem = document.querySelector('.meditation-stats-container .text-success');
        if (weeklySessionsElem) {
            weeklySessionsElem.textContent = data.weekly_sessions;
        }
        // Update total minutes meditated
        const totalMinutesElem = document.querySelector('.meditation-stats-container .text-info');
        if (totalMinutesElem) {
            totalMinutesElem.textContent = data.total_minutes_meditated;
        }
    }

    function sendCompletionSignal() {
        // Calculate actual duration meditated
        const actualDuration = initialTime - timeLeft;
        fetch('/meditation_completed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'completed', duration: actualDuration })

        })
        .then(response => response.json())
        .then(data => {
            console.log('Meditation completion signal sent:', data);
            if (data.success) {
                showNotification('Congratulations! You have completed your meditation session.');
                updateMeditationStats(data);
                // Reload dashboard after notification disappears
                setTimeout(function() {
                    window.location.href = '/dashboard';
                }, 5000); // Wait for overlay to hide
            }
        })
        .catch(error => {
            console.error('Error sending meditation completion signal:', error);
        });
    }

    function showNotification(message) {
        const notificationCard = meditationNotification.querySelector('.meditation-completion-card p');
        if (notificationCard) {
            notificationCard.textContent = message;
        }
        meditationNotification.classList.add('show'); // Add 'show' to the overlay
        setTimeout(() => {
            meditationNotification.classList.remove('show'); // Remove 'show' from the overlay
        }, 5000); // Hide after 5 seconds
    }

    // Event listeners for new Start Session buttons inside each card
    document.querySelectorAll('.start-session-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent bubbling if needed
            const card = button.closest('.duration-card-item');
            const durationMinutes = parseFloat(card.dataset.duration);
            const audioUrl = card.dataset.audio;

            initialTime = durationMinutes * 60;
            timeLeft = initialTime;
            isPaused = false;
            updateTimerDisplay();

            audio.src = audioUrl;

            durationSelectionArea.style.display = 'none';
            timerDisplayArea.style.display = 'block';
        });
    });

    startBtn.addEventListener('click', startTimer);
    pauseBtn.addEventListener('click', pauseTimer);
    stopBtn.addEventListener('click', stopTimer);

    // Initial display setup
    updateTimerDisplay();
    timerDisplayArea.style.display = 'none'; // Hide controls initially
});