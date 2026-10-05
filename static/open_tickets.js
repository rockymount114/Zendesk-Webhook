// open_tickets.js - Client-side pagination, real-time filtering, sorting, CSV export, and auto-refresh

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
    const selectPageSize = document.getElementById('select-page-size');
    const paginationInfoText = document.getElementById('pagination-info-text');
    const paginationControls = document.getElementById('pagination-controls');
    const tableBody = document.getElementById('tickets-tbody');
    const noResultsRow = document.getElementById('no-results-row');
    const sortHeaders = document.querySelectorAll('th.sortable');
    const tableContainer = document.getElementById('table-container');

    let currentSortColumn = 'date';
    let currentSortAsc = false; // default newest first
    let currentPage = 1;
    let pageSize = 25;
    let matchingRows = [];

    // ----------------- Filtering -----------------
    function applyFilters() {
        const idVal = (filterId ? filterId.value.trim().toLowerCase() : '');
        const subjectVal = (filterSubject ? filterSubject.value.trim().toLowerCase() : '');
        const statusVal = (filterStatus ? filterStatus.value.trim().toLowerCase() : '');
        const requesterVal = (filterRequester ? filterRequester.value.trim().toLowerCase() : '');
        const assigneeVal = (filterAssignee ? filterAssignee.value.trim().toLowerCase() : '');
        const startDateVal = (filterStartDate ? filterStartDate.value : '');
        const endDateVal = (filterEndDate ? filterEndDate.value : '');

        const allRows = Array.from(tableBody.querySelectorAll('tr.ticket-row'));
        matchingRows = [];

        allRows.forEach(row => {
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
                matchingRows.push(row);
            }
        });

        currentPage = 1;
        renderPagination();
    }

    // ----------------- Pagination -----------------
    function renderPagination() {
        const total = matchingRows.length;
        const allRows = tableBody.querySelectorAll('tr.ticket-row');

        // Hide all rows initially
        allRows.forEach(r => r.style.display = 'none');

        // Empty state row
        if (noResultsRow) {
            noResultsRow.style.display = (total === 0 && allRows.length > 0) ? '' : 'none';
        }

        let totalPages = 1;
        let startIndex = 0;
        let endIndex = total;

        if (pageSize === 'all') {
            totalPages = 1;
            startIndex = 0;
            endIndex = total;
            matchingRows.forEach(r => r.style.display = '');
        } else {
            totalPages = Math.ceil(total / pageSize) || 1;
            if (currentPage > totalPages) currentPage = totalPages;
            if (currentPage < 1) currentPage = 1;

            startIndex = (currentPage - 1) * pageSize;
            endIndex = Math.min(startIndex + pageSize, total);

            for (let i = startIndex; i < endIndex; i++) {
                if (matchingRows[i]) {
                    matchingRows[i].style.display = '';
                }
            }
        }

        // Update info text
        if (paginationInfoText) {
            if (total === 0) {
                paginationInfoText.textContent = 'Showing 0 tickets';
            } else if (pageSize === 'all' || total <= pageSize) {
                paginationInfoText.textContent = `Showing all ${total} tickets`;
            } else {
                paginationInfoText.textContent = `Showing ${startIndex + 1}–${endIndex} of ${total} tickets (Page ${currentPage} of ${totalPages})`;
            }
        }

        // Render page buttons
        renderPaginationButtons(totalPages);
    }

    function renderPaginationButtons(totalPages) {
        if (!paginationControls) return;
        paginationControls.innerHTML = '';

        if (totalPages <= 1 || pageSize === 'all') {
            return;
        }

        // Helper to create button
        function createBtn(text, pageNum, disabled = false, active = false) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `page-btn ${active ? 'active' : ''}`;
            btn.innerHTML = text;
            btn.disabled = disabled;
            if (!disabled && !active) {
                btn.addEventListener('click', function () {
                    currentPage = pageNum;
                    renderPagination();
                    if (tableContainer) {
                        tableContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            }
            return btn;
        }

        function createEllipsis() {
            const span = document.createElement('span');
            span.className = 'page-ellipsis';
            span.textContent = '...';
            return span;
        }

        // First button
        paginationControls.appendChild(createBtn('«', 1, currentPage === 1));
        // Prev button
        paginationControls.appendChild(createBtn('‹', currentPage - 1, currentPage === 1));

        // Window of page numbers around current
        const delta = 2;
        const start = Math.max(1, currentPage - delta);
        const end = Math.min(totalPages, currentPage + delta);

        if (start > 1) {
            paginationControls.appendChild(createBtn('1', 1, false, currentPage === 1));
            if (start > 2) {
                paginationControls.appendChild(createEllipsis());
            }
        }

        for (let i = start; i <= end; i++) {
            paginationControls.appendChild(createBtn(i.toString(), i, false, i === currentPage));
        }

        if (end < totalPages) {
            if (end < totalPages - 1) {
                paginationControls.appendChild(createEllipsis());
            }
            paginationControls.appendChild(createBtn(totalPages.toString(), totalPages, false, totalPages === currentPage));
        }

        // Next button
        paginationControls.appendChild(createBtn('›', currentPage + 1, currentPage === totalPages));
        // Last button
        paginationControls.appendChild(createBtn('»', totalPages, currentPage === totalPages));
    }

    // Page size dropdown listener
    if (selectPageSize) {
        selectPageSize.addEventListener('change', function () {
            const val = this.value;
            pageSize = (val === 'all') ? 'all' : parseInt(val, 10);
            currentPage = 1;
            renderPagination();
        });
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

        // Re-append in sorted order
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

        // Re-apply filters to update matchingRows order and pagination slice
        applyFilters();
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
            // Export all matching filtered rows across all pages
            if (matchingRows.length === 0) {
                alert('No matching tickets to export.');
                return;
            }

            const headers = ['Ticket ID', 'Subject', 'Requester', 'Assignee', 'Status', 'Priority', 'Created Date (EST)', 'Updated Date (EST)', 'Zendesk URL'];
            const csvRows = [headers.join(',')];

            matchingRows.forEach(r => {
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

    // ----------------- Refresh & Auto-Refresh (Default: False) -----------------
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
        const autoRefreshEnabled = localStorage.getItem('zendesk.openTickets.autoRefresh') === 'true';
        autoRefreshToggle.checked = autoRefreshEnabled;
        if (autoRefreshEnabled) {
            startAutoRefresh();
        } else if (refreshCountdown) {
            refreshCountdown.textContent = 'Off';
        }

        autoRefreshToggle.addEventListener('change', function () {
            localStorage.setItem('zendesk.openTickets.autoRefresh', String(this.checked));
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }

    // Initial filter & pagination pass
    applyFilters();
});
