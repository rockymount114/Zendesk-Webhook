document.addEventListener('DOMContentLoaded', function () {
    const detailSection = document.getElementById('ticket-details');
    const detailTitle = document.getElementById('ticket-details-title');
    const detailLabel = document.getElementById('ticket-details-label');
    const detailCount = document.getElementById('ticket-details-count');
    const detailBody = document.getElementById('ticket-details-body');
    const emptyRow = document.getElementById('ticket-details-empty');
    const closeButton = document.getElementById('ticket-details-close');
    const ticketRows = detailBody
        ? Array.from(detailBody.querySelectorAll('tr[data-status]'))
        : [];
    const countButtons = document.querySelectorAll('.kpi-value-button');
    const labels = {
        all: 'All tickets',
        open: 'Open tickets',
        pending: 'Pending tickets',
        solved: 'Solved tickets',
        closed: 'Closed tickets',
        new: 'New tickets',
        'on-hold': 'On-hold tickets'
    };
    let selectedButton = null;

    function hideDetails() {
        if (!detailSection) return;
        detailSection.hidden = true;
        countButtons.forEach(function (button) {
            button.setAttribute('aria-expanded', 'false');
        });
        if (selectedButton) {
            selectedButton.setAttribute('aria-pressed', 'false');
            selectedButton.focus();
            selectedButton = null;
        }
    }

    countButtons.forEach(function (button) {
        button.setAttribute('aria-pressed', 'false');
        button.addEventListener('click', function () {
            if (!detailSection || !detailTitle || !detailLabel || !detailCount) return;
            const status = this.dataset.status || 'all';

            if (selectedButton === this && !detailSection.hidden) {
                hideDetails();
                return;
            }

            countButtons.forEach(function (countButton) {
                countButton.setAttribute('aria-expanded', 'false');
                countButton.setAttribute('aria-pressed', 'false');
            });

            const visibleRows = [];
            ticketRows.forEach(function (row) {
                const matches = status === 'all' || row.dataset.status === status;
                row.hidden = !matches;
                if (matches) visibleRows.push(row);
            });

            if (emptyRow) emptyRow.hidden = visibleRows.length !== 0;
            detailLabel.textContent = labels[status] || 'Ticket details';
            detailCount.textContent = visibleRows.length;
            detailSection.hidden = false;
            this.setAttribute('aria-expanded', 'true');
            this.setAttribute('aria-pressed', 'true');
            selectedButton = this;
            detailSection.scrollIntoView({
                behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
                    ? 'auto'
                    : 'smooth',
                block: 'start'
            });
            detailTitle.focus({ preventScroll: true });
        });
    });

    if (closeButton) {
        closeButton.addEventListener('click', hideDetails);
    }
});
