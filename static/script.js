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

// Ticket comments functionality
function loadTicketComments(ticketId) {
    return fetch(`/api/ticket/${ticketId}/comments`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            return data;
        })
        .catch(error => {
            console.error('Error loading comments:', error);
            throw error;
        });
}

function showTicketComments(ticketId, ticketElement) {
    // Check if comments already loaded
    const existingComments = ticketElement.querySelector('.ticket-comments');
    if (existingComments) {
        existingComments.style.display = existingComments.style.display === 'none' ? 'block' : 'none';
        return;
    }

    // Create comments container
    const commentsContainer = document.createElement('div');
    commentsContainer.className = 'ticket-comments';
    commentsContainer.innerHTML = `<div class="comments-loading">Loading comments... ⏳</div>`;
    ticketElement.appendChild(commentsContainer);

    // Load comments from API
    loadTicketComments(ticketId)
        .then(data => {
            if (data.comments && data.comments.length > 0) {
                let html = `<div class="comments-header"><h4>📝 Comments (${data.count})</h4></div><div class="comments-list">`;

                data.comments.forEach(comment => {
                    const authorName = comment.author_name || 'Unknown';
                    const createdAt = comment.created_at_formatted || comment.created_at;
                    const body = comment.body || comment.html_body || '';
                    const truncatedBody = body.length > 200 ? body.substring(0, 200) + '...' : body;

                    html += `
                        <div class="comment-item" data-timestamp="${comment.created_at}">
                            <div class="comment-meta">
                                <span class="comment-author">👤 ${authorName}</span>
                                <span class="comment-date" title="Hover for details">🕐 ${createdAt}</span>
                            </div>
                            <div class="comment-body">${truncatedBody}</div>
                        </div>`;
                });

                html += `</div><div class="comments-footer"><span class="cache-status">${data.cache_status === 'cache_hit' ? '⚡' : '🔄'} Cached</span></div>`;
                commentsContainer.innerHTML = html;

                // Add hover effects for timestamps
                const dateSpan = commentsContainer.querySelector('.comment-date');
                if (dateSpan) {
                    dateSpan.addEventListener('mouseenter', function() {
                        this.title = `Created at: ${this.getAttribute('data-timestamp')}`;
                    });
                }
            } else {
                commentsContainer.innerHTML = `<div class="comments-header"><h4>📝 Comments</h4></div>
                    <div class="no-comments">No comments found for this ticket.</div>
                    <div class="comments-footer"><span class="cache-status">${data.cache_status === 'cache_hit' ? '⚡' : '🔄'} Cached</span></div>`;
            }
        })
        .catch(error => {
            commentsContainer.innerHTML = `<div class="comments-header"><h4>📝 Comments</h4></div>
                <div class="comments-error">❌ Failed to load comments</div>
                <div class="comments-footer"><span class="error-message">${error.message}</span></div>`;
        });
}

function addCommentClickHandlers() {
    const ticketItems = document.querySelectorAll('.ticket-item');
    ticketItems.forEach(item => {
        const ticketId = item.getAttribute('data-ticket-id') ||
                       item.querySelector('.ticket-id')?.textContent?.replace('#', '');
        if (ticketId) {
            item.style.cursor = 'pointer';
            item.title = 'Click to view comments';
            item.addEventListener('click', function(e) {
                // Don't trigger if clicking on a link
                if (e.target.tagName === 'A') return;
                showTicketComments(ticketId, item);
            });
        }
    });
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

    // Add comment click handlers
    addCommentClickHandlers();
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