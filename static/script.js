// Auto-refresh functionality
let refreshInterval;
let countdownInterval;
let secondsLeft = 60;

function updateCountdown() {
    const indicator = document.getElementById('refresh-indicator');
    if (indicator) {
        indicator.textContent = `Auto-refresh in ${secondsLeft}s`;
        secondsLeft--;
        
        if (secondsLeft < 0) {
            indicator.textContent = 'Refreshing...';
            setTimeout(() => {
                // Force a hard reload to bypass cache
                window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
            }, 500);
        }
    }
}

function startAutoRefresh() {
    // Update countdown every second
    countdownInterval = setInterval(updateCountdown, 1000);
    
    // Refresh page every 60 seconds
    refreshInterval = setInterval(() => {
        // Force a hard reload to bypass cache
        window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
    }, 60000);
}

function stopAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    if (countdownInterval) clearInterval(countdownInterval);
}

// Start auto-refresh when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Ensure CSS is fully loaded before showing content
    if (document.styleSheets.length === 0) {
        console.warn('CSS not loaded, forcing reload...');
        setTimeout(() => {
            window.location.reload(true);
        }, 1000);
        return;
    }
    
    startAutoRefresh();
    updateCountdown(); // Initial countdown display
});

// Stop auto-refresh when page is hidden (user switches tabs)
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        secondsLeft = 60; // Reset countdown
        startAutoRefresh();
    }
});

// Optional: Allow manual refresh with cache bypass
function manualRefresh() {
    stopAutoRefresh();
    window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
}

// Monitor if CSS fails to load and auto-retry
window.addEventListener('load', function() {
    const testElement = document.querySelector('.container');
    if (testElement) {
        const styles = window.getComputedStyle(testElement);
        // Check if CSS is actually applied (max-width should be 1280px)
        if (styles.maxWidth === 'none' || styles.maxWidth === '') {
            console.warn('CSS not properly applied, reloading...');
            setTimeout(() => {
                window.location.reload(true);
            }, 500);
        }
    }
});