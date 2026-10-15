// Auto-refresh functionality for Recent Tickets (Default: False)
let refreshInterval = null;
let countdownInterval = null;
let secondsLeft = 60;
let isAutoRefreshEnabled = false;

function updateCountdown() {
    const labels = document.querySelectorAll('.refresh-timer-label, #refresh-timer-label');
    if (isAutoRefreshEnabled) {
        labels.forEach(label => {
            label.textContent = `${secondsLeft}s`;
        });
        secondsLeft--;

        if (secondsLeft < 0) {
            labels.forEach(label => {
                label.textContent = 'Refreshing...';
            });
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

    const labels = document.querySelectorAll('.refresh-timer-label, #refresh-timer-label');
    labels.forEach(label => {
        label.textContent = '60s';
    });
}

function stopAutoRefresh() {
    isAutoRefreshEnabled = false;
    if (refreshInterval) clearInterval(refreshInterval);
    if (countdownInterval) clearInterval(countdownInterval);
    refreshInterval = null;
    countdownInterval = null;

    const labels = document.querySelectorAll('.refresh-timer-label, #refresh-timer-label');
    labels.forEach(label => {
        label.textContent = 'Off';
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const toggles = document.querySelectorAll('.toggle-index-refresh, #toggle-index-refresh');
    if (toggles.length > 0) {
        const autoRefreshEnabled = localStorage.getItem('zendesk.index.autoRefresh') === 'true';
        toggles.forEach(t => {
            t.checked = autoRefreshEnabled;
        });

        if (autoRefreshEnabled) {
            startAutoRefresh();
        } else {
            const labels = document.querySelectorAll('.refresh-timer-label, #refresh-timer-label');
            labels.forEach(label => {
                label.textContent = 'Off';
            });
        }

        toggles.forEach(toggle => {
            toggle.addEventListener('change', function () {
                const checked = this.checked;
                localStorage.setItem('zendesk.index.autoRefresh', String(checked));
                toggles.forEach(t => {
                    t.checked = checked;
                });
                if (checked) {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
            });
        });
    }
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