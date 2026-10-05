// Auto-refresh functionality for Recent Tickets (Default: False)
let refreshInterval = null;
let countdownInterval = null;
let secondsLeft = 60;
let isAutoRefreshEnabled = false;

function updateCountdown() {
    const label = document.getElementById('refresh-timer-label');
    if (label && isAutoRefreshEnabled) {
        label.textContent = `${secondsLeft}s`;
        secondsLeft--;

        if (secondsLeft < 0) {
            label.textContent = 'Refreshing...';
            setTimeout(() => {
                window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
            }, 500);
        }
    }
}

function startAutoRefresh() {
    isAutoRefreshEnabled = true;
    secondsLeft = 60;
    if (countdownInterval) clearInterval(countdownInterval);
    if (refreshInterval) clearInterval(refreshInterval);

    updateCountdown();
    countdownInterval = setInterval(updateCountdown, 1000);
    refreshInterval = setInterval(() => {
        window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
    }, 60000);

    const label = document.getElementById('refresh-timer-label');
    if (label) label.textContent = '60s';
}

function stopAutoRefresh() {
    isAutoRefreshEnabled = false;
    if (refreshInterval) clearInterval(refreshInterval);
    if (countdownInterval) clearInterval(countdownInterval);
    refreshInterval = null;
    countdownInterval = null;

    const label = document.getElementById('refresh-timer-label');
    if (label) label.textContent = 'Off';
}

document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('toggle-index-refresh');
    if (toggle) {
        const autoRefreshEnabled = localStorage.getItem('zendesk.index.autoRefresh') === 'true';
        toggle.checked = autoRefreshEnabled;
        if (autoRefreshEnabled) {
            startAutoRefresh();
        }

        toggle.addEventListener('change', function () {
            localStorage.setItem('zendesk.index.autoRefresh', String(this.checked));
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }

    // Default indicator text
    const label = document.getElementById('refresh-timer-label');
    if (label && (!toggle || !toggle.checked)) label.textContent = 'Off';
});

// Pause when page is hidden (if enabled)
document.addEventListener('visibilitychange', function () {
    if (!isAutoRefreshEnabled) return;
    if (document.hidden) {
        if (countdownInterval) clearInterval(countdownInterval);
        if (refreshInterval) clearInterval(refreshInterval);
    } else {
        startAutoRefresh();
    }
});

// Optional: Allow manual refresh with cache bypass
function manualRefresh() {
    stopAutoRefresh();
    window.location.href = window.location.href.split('?')[0] + '?t=' + new Date().getTime();
}