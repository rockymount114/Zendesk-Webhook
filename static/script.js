
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
                        location.reload();
                    }, 500);
                }
            }
        }

        function startAutoRefresh() {
            // Update countdown every second
            countdownInterval = setInterval(updateCountdown, 1000);
            
            // Refresh page every 60 seconds
            refreshInterval = setInterval(() => {
                location.reload();
            }, 60000);
        }

        function stopAutoRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            if (countdownInterval) clearInterval(countdownInterval);
        }

        // Start auto-refresh when page loads
        document.addEventListener('DOMContentLoaded', function() {
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

        // Optional: Allow manual refresh
        function manualRefresh() {
            stopAutoRefresh();
            location.reload();
        }
