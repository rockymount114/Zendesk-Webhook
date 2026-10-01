// open_tickets.js - Client-side filtering, sorting, CSV export, and auto-refresh

document.addEventListener('DOMContentLoaded', function () {
    const filterId = document.getElementById('filter-id');
    const filterSubject = document.getElementById('filter-subject');
    const filterStatus = document.getElementById('filter-status');
    const filterRequester = document.getElementById('filter-requester');
    const filterAssignee = document.getElementById('filter-assignee');
    const filterStartDate = document.getElementById('filter-start-date');
    const filterEndDate = document.getElementById('filter-end-date');
    const btnClear = document.getElementById('btn-clear-filters');
    const btnExport = document.getElementById('btn-export-csv');
    const btnRefresh = document.getElementById('btn-refresh');
    const autoRefreshToggle = document.getElementById('toggle-auto-refresh');
    const refreshCountdown = document.getElementById('refresh-countdown');
    const ticketCounter = document.getElementById('ticket-counter');
    const tableBody = document.getElementById('tickets-tbody');
    const noResultsRow = document.getElementById('no-results-row');
    const sortHeaders = document.querySelectorAll('th.sortable');

    let currentSortColumn = 'created_at';
    let currentSortAsc = false; // default newest first

    // ----------------- Filtering -----------------
    function applyFilters() {
        const idVal = (filterId ? filterId.value.trim().toLowerCase() : '');
        const subjectVal = (filterSubject ? filterSubject.value.trim().toLowerCase() : '');
        const statusVal = (filterStatus ? filterStatus.value.trim().toLowerCase() : '');
        const requesterVal = (filterRequester ? filterRequester.value.trim().toLowerCase() : '');
        const assigneeVal = (filterAssignee ? filterAssignee.value.trim().toLowerCase() : '');
        const startDateVal = (filterStartDate ? filterStartDate.value : '');
        const endDateVal = (filterEndDate ? filterEndDate.value : '');

        const rows = tableBody.querySelectorAll('tr.ticket-row');
        let visibleCount = 0;
        const totalCount = rows.length;

        rows.forEach(row => {
            const rowId = (row.dataset.id || '').toLowerCase();
            const rowSubject = (row.dataset.subject || '').toLowerCase();
            const rowStatus = (row.dataset.status || '').toLowerCase();
            const rowRequester = (row.dataset.requester || '').toLowerCase();
            const rowAssignee = (row.dataset.assignee || '').toLowerCase();
            const rowDate = row.dataset.date || ''; // YYYY-MM-DD

            let match = true;

            if (idVal && !rowId.includes(idVal)) match = false;
            if (match && subjectVal && !rowSubject.includes(subjectVal)) match = false;
            if (match && statusVal && statusVal !== 'all' && rowStatus !== statusVal) match = false;
            if (match && requesterVal && !rowRequester.includes(requesterVal)) match = false;
            if (match && assigneeVal && !rowAssignee.includes(assigneeVal)) match = false;
            if (match && startDateVal && rowDate < startDateVal) match = false;
            if (match && endDateVal && rowDate > endDateVal) match = false;

            if (match) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Update counter
        if (ticketCounter) {
            ticketCounter.textContent = `Showing ${visibleCount} of ${totalCount} tickets`;
        }

        // Show/hide empty state row
        if (noResultsRow) {
            noResultsRow.style.display = (visibleCount === 0 && totalCount > 0) ? '' : 'none';
        }
    }

    // Attach filter event listeners
    [filterId, filterSubject, filterRequester, filterAssignee].forEach(input => {
        if (input) {
            input.addEventListener('input', applyFilters);
        }
    });

    [filterStatus, filterStartDate, filterEndDate].forEach(input => {
        if (input) {
            input.addEventListener('change', applyFilters);
        }
    });

    // Clear filters
    if (btnClear) {
        btnClear.addEventListener('click', function () {
            if (filterId) filterId.value = '';
            if (filterSubject) filterSubject.value = '';
            if (filterStatus) filterStatus.value = 'all';
            if (filterRequester) filterRequester.value = '';
            if (filterAssignee) filterAssignee.value = '';
            if (filterStartDate) filterStartDate.value = '';
            if (filterEndDate) filterEndDate.value = '';
            applyFilters();
        });
    }

    // ----------------- Sorting -----------------
    function sortTable(column, asc) {
        const rows = Array.from(tableBody.querySelectorAll('tr.ticket-row'));
        const priorityOrder = { 'urgent': 4, 'high': 3, 'normal': 2, 'low': 1, '': 0 };

        rows.sort((a, b) => {
            let valA = a.dataset[column] || '';
            let valB = b.dataset[column] || '';

            if (column === 'id') {
                valA = parseInt(valA, 10) || 0;
                valB = parseInt(valB, 10) || 0;
            } else if (column === 'priority') {
                valA = priorityOrder[valA.toLowerCase()] || 0;
                valB = priorityOrder[valB.toLowerCase()] || 0;
            } else {
                valA = valA.toLowerCase();
                valB = valB.toLowerCase();
            }

            if (valA < valB) return asc ? -1 : 1;
            if (valA > valB) return asc ? 1 : -1;
            return 0;
        });

        rows.forEach(r => tableBody.appendChild(r));

        // Update header indicators
        sortHeaders.forEach(th => {
            const arrow = th.querySelector('.sort-arrow');
            if (th.dataset.col === column) {
                if (arrow) arrow.textContent = asc ? ' ▲' : ' ▼';
                th.classList.add('active-sort');
            } else {
                if (arrow) arrow.textContent = ' ↕';
                th.classList.remove('active-sort');
            }
        });
    }

    sortHeaders.forEach(th => {
        th.addEventListener('click', function () {
            const col = th.dataset.col;
            if (currentSortColumn === col) {
                currentSortAsc = !currentSortAsc;
            } else {
                currentSortColumn = col;
                currentSortAsc = (col === 'id' || col === 'subject');
            }
            sortTable(currentSortColumn, currentSortAsc);
        });
    });

    // ----------------- CSV Export -----------------
    function escapeCSV(text) {
        if (!text) return '""';
        return `"${text.toString().replace(/"/g, '""')}"`;
    }

    if (btnExport) {
        btnExport.addEventListener('click', function () {
            const rows = Array.from(tableBody.querySelectorAll('tr.ticket-row')).filter(r => r.style.display !== 'none');
            if (rows.length === 0) {
                alert('No visible tickets to export.');
                return;
            }

            const headers = ['Ticket ID', 'Subject', 'Requester', 'Assignee', 'Status', 'Priority', 'Created Date (EST)', 'Updated Date (EST)', 'Zendesk URL'];
            const csvRows = [headers.join(',')];

            rows.forEach(r => {
                const id = r.dataset.id || '';
                const subject = r.dataset.subject || '';
                const requester = r.dataset.requester || '';
                const assignee = r.dataset.assignee || '';
                const status = (r.dataset.status || '').toUpperCase();
                const priority = (r.dataset.priority || 'Normal');
                const created = r.dataset.createdFormatted || '';
                const updated = r.dataset.updatedFormatted || '';
                const url = r.dataset.url || '';

                const line = [
                    escapeCSV(id),
                    escapeCSV(subject),
                    escapeCSV(requester),
                    escapeCSV(assignee),
                    escapeCSV(status),
                    escapeCSV(priority),
                    escapeCSV(created),
                    escapeCSV(updated),
                    escapeCSV(url)
                ];
                csvRows.push(line.join(','));
            });

            const csvBlob = new Blob([csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
            const downloadUrl = URL.createObjectURL(csvBlob);
            const a = document.createElement('a');
            const today = new Date().toISOString().split('T')[0];
            a.href = downloadUrl;
            a.download = `zendesk_open_tickets_${today}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);
        });
    }

    // ----------------- Refresh & Auto-Refresh -----------------
    let countdown = 60;
    let timer = null;

    function refreshPage() {
        const url = new URL(window.location.href);
        url.searchParams.set('refresh', '1');
        url.searchParams.set('t', Date.now());
        window.location.href = url.toString();
    }

    if (btnRefresh) {
        btnRefresh.addEventListener('click', refreshPage);
    }

    function startAutoRefresh() {
        countdown = 60;
        if (refreshCountdown) refreshCountdown.textContent = `${countdown}s`;
        if (timer) clearInterval(timer);

        timer = setInterval(() => {
            countdown--;
            if (refreshCountdown) refreshCountdown.textContent = `${countdown}s`;
            if (countdown <= 0) {
                clearInterval(timer);
                refreshPage();
            }
        }, 1000);
    }

    function stopAutoRefresh() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
        if (refreshCountdown) refreshCountdown.textContent = 'Off';
    }

    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function () {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });

        // Start if checked by default
        if (autoRefreshToggle.checked) {
            startAutoRefresh();
        }
    }

    // Initial filter pass
    applyFilters();
});
