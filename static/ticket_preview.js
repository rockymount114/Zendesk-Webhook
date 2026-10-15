// ticket_preview.js - Universal Slide-Over Ticket Preview Drawer
// Handles interactive preview for All Open Tickets, Recent Tickets, and Dashboard Details.

(function () {
    'use strict';

    let drawer, backdrop, closeBtn, prevBtn, nextBtn, zendeskLink;
    let ticketIdEl, statusBadge, priorityBadge, subjectEl;
    let requesterEl, assigneeEl, createdAtEl, updatedAtEl, descriptionEl;
    let conversationSection, commentsCountEl, commentsTimeline;

    let currentTicketElement = null;
    let currentTicketId = null;
    let commentsAbortController = null;
    let lastActiveElement = null;

    function initElements() {
        drawer = document.getElementById('ticket-preview-drawer');
        backdrop = document.getElementById('ticket-drawer-backdrop');
        closeBtn = document.getElementById('drawer-close-btn');
        prevBtn = document.getElementById('drawer-prev-btn');
        nextBtn = document.getElementById('drawer-next-btn');
        zendeskLink = document.getElementById('drawer-zendesk-link');

        ticketIdEl = document.getElementById('drawer-ticket-id');
        statusBadge = document.getElementById('drawer-ticket-status');
        priorityBadge = document.getElementById('drawer-ticket-priority');
        subjectEl = document.getElementById('drawer-ticket-subject');

        requesterEl = document.getElementById('drawer-requester');
        assigneeEl = document.getElementById('drawer-assignee');
        createdAtEl = document.getElementById('drawer-created-at');
        updatedAtEl = document.getElementById('drawer-updated-at');
        descriptionEl = document.getElementById('drawer-description');

        conversationSection = document.getElementById('drawer-conversation-section');
        commentsCountEl = document.getElementById('drawer-comments-count');
        commentsTimeline = document.getElementById('drawer-comments-timeline');
    }

    // Retrieve list of currently visible ticket elements in active view
    function getVisibleTicketItems() {
        // Priority 1: Open tickets table
        const openTableRows = Array.from(document.querySelectorAll('#tickets-tbody tr.ticket-row'));
        if (openTableRows.length > 0) {
            return openTableRows.filter(r => r.style.display !== 'none');
        }

        // Priority 2: Dashboard detail table
        const dashDetailBody = document.getElementById('ticket-details-body');
        if (dashDetailBody) {
            const dashRows = Array.from(dashDetailBody.querySelectorAll('tr.ticket-row'));
            if (dashRows.length > 0) {
                return dashRows.filter(r => r.style.display !== 'none' && !r.hasAttribute('hidden'));
            }
        }

        // Priority 3: Recent tickets list (Home)
        const recentItems = Array.from(document.querySelectorAll('.tickets-list .ticket-item'));
        if (recentItems.length > 0) {
            return recentItems;
        }

        // Fallback: any ticket-row or ticket-item in document
        return Array.from(document.querySelectorAll('.ticket-row, .ticket-item')).filter(r => {
            return r.style.display !== 'none' && !r.hasAttribute('hidden');
        });
    }

    function updateNavButtons() {
        if (!prevBtn || !nextBtn || !currentTicketElement) return;

        const visibleItems = getVisibleTicketItems();
        const currentIndex = visibleItems.indexOf(currentTicketElement);

        if (currentIndex === -1) {
            prevBtn.disabled = true;
            nextBtn.disabled = true;
            return;
        }

        prevBtn.disabled = (currentIndex <= 0);
        nextBtn.disabled = (currentIndex >= visibleItems.length - 1);
    }

    function navigateRelative(delta) {
        const visibleItems = getVisibleTicketItems();
        const currentIndex = visibleItems.indexOf(currentTicketElement);

        if (currentIndex === -1) return;

        const newIndex = currentIndex + delta;
        if (newIndex >= 0 && newIndex < visibleItems.length) {
            openPreview(visibleItems[newIndex]);
        }
    }

    function getInitials(name) {
        if (!name || typeof name !== 'string') return '?';
        const parts = name.trim().split(/\s+/);
        if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    function formatCommentTimestamp(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            if (isNaN(date.getTime())) return isoString;
            return date.toLocaleString('en-US', {
                timeZone: 'America/New_York',
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            }) + ' EST';
        } catch (e) {
            return isoString;
        }
    }

    function formatFileSize(bytes) {
        if (!bytes || isNaN(bytes)) return '';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function fetchComments(ticketId, requesterName, assigneeName) {
        if (commentsAbortController) {
            commentsAbortController.abort();
        }
        commentsAbortController = new AbortController();

        // Keep conversation section hidden until we confirm follow-up comments exist
        if (conversationSection) conversationSection.hidden = true;
        if (commentsTimeline) commentsTimeline.innerHTML = '';
        if (commentsCountEl) commentsCountEl.textContent = '0';

        fetch(`/api/tickets/${ticketId}/comments`, {
            signal: commentsAbortController.signal,
            headers: { 'Accept': 'application/json' }
        })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`Server returned ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                const comments = Array.isArray(data.comments) ? data.comments : [];

                // Zendesk comment #1 is always the ticket's original description (already displayed above).
                // Follow-up conversation activity consists of comments from index 1 onward.
                if (comments.length <= 1) {
                    // No follow-up replies or notes: keep section hidden cleanly
                    if (conversationSection) conversationSection.hidden = true;
                    return;
                }

                const followUpComments = comments.slice(1);
                const usersList = Array.isArray(data.users) ? data.users : [];
                const usersMap = {};

                usersList.forEach(u => {
                    if (u && u.id) usersMap[u.id] = u.name || 'Unknown';
                });

                if (commentsCountEl) {
                    commentsCountEl.textContent = followUpComments.length;
                }

                if (commentsTimeline) {
                    commentsTimeline.innerHTML = '';

                    // Render each follow-up comment
                    followUpComments.forEach(comment => {
                        const card = document.createElement('article');
                        const isInternal = (comment.public === false);
                        card.className = `comment-card ${isInternal ? 'comment-internal' : 'comment-public'}`;

                        // Resolve author name
                        let authorName = usersMap[comment.author_id];
                        if (!authorName) {
                            if (requesterName && requesterName !== 'Unknown' && comment.author_id === data.requester_id) {
                                authorName = requesterName;
                            } else if (assigneeName && assigneeName !== 'Unassigned' && comment.author_id === data.assignee_id) {
                                authorName = assigneeName;
                            } else {
                                authorName = `User #${comment.author_id}`;
                            }
                        }

                        const initials = getInitials(authorName);
                        const formattedDate = formatCommentTimestamp(comment.created_at);

                        // Header
                        const header = document.createElement('div');
                        header.className = 'comment-header';

                        const avatar = document.createElement('div');
                        avatar.className = `comment-avatar ${isInternal ? 'avatar-internal' : 'avatar-public'}`;
                        avatar.textContent = initials;
                        avatar.setAttribute('aria-hidden', 'true');

                        const metaGroup = document.createElement('div');
                        metaGroup.className = 'comment-meta-group';

                        const authorSpan = document.createElement('span');
                        authorSpan.className = 'comment-author-name';
                        authorSpan.textContent = authorName;

                        const dateSpan = document.createElement('span');
                        dateSpan.className = 'comment-date';
                        dateSpan.textContent = formattedDate;

                        metaGroup.appendChild(authorSpan);
                        metaGroup.appendChild(dateSpan);

                        const badge = document.createElement('span');
                        if (isInternal) {
                            badge.className = 'comment-badge badge-internal';
                            badge.textContent = '🔒 Internal Note';
                        } else {
                            badge.className = 'comment-badge badge-public';
                            badge.textContent = 'Public Reply';
                        }

                        header.appendChild(avatar);
                        header.appendChild(metaGroup);
                        header.appendChild(badge);
                        card.appendChild(header);

                        // Comment body text
                        const bodyDiv = document.createElement('div');
                        bodyDiv.className = 'comment-body-text';
                        bodyDiv.textContent = comment.body || comment.plain_body || '(Empty comment)';
                        card.appendChild(bodyDiv);

                        // Attachments if present
                        if (Array.isArray(comment.attachments) && comment.attachments.length > 0) {
                            const attContainer = document.createElement('div');
                            attContainer.className = 'comment-attachments-list';

                            comment.attachments.forEach(att => {
                                const attLink = document.createElement('a');
                                attLink.className = 'comment-attachment-pill';
                                attLink.href = att.content_url || '#';
                                attLink.target = '_blank';
                                attLink.rel = 'noopener noreferrer';
                                attLink.title = `Download ${att.file_name || 'attachment'}`;

                                const icon = document.createElement('span');
                                icon.textContent = '📎 ';
                                icon.setAttribute('aria-hidden', 'true');

                                const nameSpan = document.createElement('span');
                                nameSpan.className = 'attachment-name';
                                nameSpan.textContent = att.file_name || 'Attachment';

                                attLink.appendChild(icon);
                                attLink.appendChild(nameSpan);

                                if (att.size) {
                                    const sizeSpan = document.createElement('span');
                                    sizeSpan.className = 'attachment-size';
                                    sizeSpan.textContent = ` (${formatFileSize(att.size)})`;
                                    attLink.appendChild(sizeSpan);
                                }

                                attContainer.appendChild(attLink);
                            });

                            card.appendChild(attContainer);
                        }

                        commentsTimeline.appendChild(card);
                    });
                }

                // Reveal section once follow-up comments are rendered
                if (conversationSection) {
                    conversationSection.hidden = false;
                }
            })
            .catch(err => {
                if (err.name === 'AbortError') return;
                // Silently hide conversation section on errors to avoid confusing users
                if (conversationSection) conversationSection.hidden = true;
            });
    }

    function openPreview(ticketElement) {
        if (!drawer || !backdrop || !ticketElement) return;

        currentTicketElement = ticketElement;
        const ds = ticketElement.dataset;
        currentTicketId = ds.id;

        // Populate header
        if (ticketIdEl) ticketIdEl.textContent = `#${ds.id || '0'}`;

        const rawStatus = (ds.status || 'new').toLowerCase();
        const normStatus = (rawStatus === 'hold') ? 'on-hold' : rawStatus;
        if (statusBadge) {
            statusBadge.textContent = normStatus.toUpperCase();
            statusBadge.className = `status-badge status-${normStatus}`;
        }

        const rawPriority = (ds.priority || 'Normal').trim();
        const normPriority = rawPriority ? (rawPriority.charAt(0).toUpperCase() + rawPriority.slice(1).toLowerCase()) : 'Normal';
        if (priorityBadge) {
            priorityBadge.textContent = normPriority;
            priorityBadge.className = `priority-badge priority-${normPriority.toLowerCase()}`;
        }

        if (zendeskLink) {
            zendeskLink.href = ds.url || `https://${window.location.hostname}/agent/tickets/${ds.id}`;
        }

        // Populate fields
        if (subjectEl) subjectEl.textContent = ds.subject || 'No subject';
        if (requesterEl) requesterEl.textContent = ds.requester || 'Unknown';
        if (assigneeEl) assigneeEl.textContent = ds.assignee || 'Unassigned';
        if (createdAtEl) createdAtEl.textContent = ds.createdFormatted || 'N/A';
        if (updatedAtEl) updatedAtEl.textContent = ds.updatedFormatted || 'N/A';

        if (descriptionEl) {
            descriptionEl.textContent = ds.description || 'No description provided.';
        }

        // Hide conversation section while checking in background
        if (conversationSection) conversationSection.hidden = true;
        if (commentsTimeline) commentsTimeline.innerHTML = '';
        if (commentsCountEl) commentsCountEl.textContent = '0';

        updateNavButtons();

        // Reveal drawer
        drawer.classList.add('is-open');
        backdrop.classList.add('is-open');
        drawer.setAttribute('aria-hidden', 'false');
        document.body.classList.add('ticket-drawer-open');

        // Scroll drawer body to top
        const drawerBody = drawer.querySelector('.drawer-body');
        if (drawerBody) drawerBody.scrollTop = 0;

        drawer.focus();

        // Check for follow-up comments in background
        if (currentTicketId) {
            fetchComments(currentTicketId, ds.requester, ds.assignee);
        }
    }

    function closePreview() {
        if (!drawer || !backdrop) return;

        drawer.classList.remove('is-open');
        backdrop.classList.remove('is-open');
        drawer.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('ticket-drawer-open');

        if (commentsAbortController) {
            commentsAbortController.abort();
            commentsAbortController = null;
        }

        if (conversationSection) conversationSection.hidden = true;

        if (lastActiveElement && typeof lastActiveElement.focus === 'function') {
            lastActiveElement.focus();
        }
        currentTicketElement = null;
        currentTicketId = null;
    }

    document.addEventListener('DOMContentLoaded', function () {
        initElements();

        if (closeBtn) closeBtn.addEventListener('click', closePreview);
        if (backdrop) backdrop.addEventListener('click', closePreview);

        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                navigateRelative(-1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                navigateRelative(1);
            });
        }

        // Global keydown listeners for drawer
        document.addEventListener('keydown', function (e) {
            if (!drawer || !drawer.classList.contains('is-open')) return;

            if (e.key === 'Escape') {
                e.preventDefault();
                closePreview();
            } else if (e.key === 'ArrowUp' || e.key === 'k') {
                if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
                e.preventDefault();
                navigateRelative(-1);
            } else if (e.key === 'ArrowDown' || e.key === 'j') {
                if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
                e.preventDefault();
                navigateRelative(1);
            }
        });

        // Global delegated click listener on ticket elements
        document.addEventListener('click', function (e) {
            // If click originated inside the open preview drawer or its backdrop, let internal controls handle it
            if (e.target.closest('#ticket-preview-drawer') || e.target.closest('#ticket-drawer-backdrop')) {
                return;
            }

            // Find clicked ticket element
            const ticketEl = e.target.closest('.ticket-row, .ticket-item');
            if (!ticketEl) return;

            // If user clicked directly on an external link or a button/input, do not intercept
            if (e.target.closest('a, button, input, select, textarea, label')) {
                return;
            }

            e.preventDefault();
            lastActiveElement = ticketEl;
            openPreview(ticketEl);
        });
    });
})();
