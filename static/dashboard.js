document.addEventListener('DOMContentLoaded', function () {
    const detailSection = document.getElementById('ticket-details');
    const detailTitle = document.getElementById('ticket-details-title');
    const detailLabel = document.getElementById('ticket-details-label');
    const detailCount = document.getElementById('ticket-details-count');
    const detailBody = document.getElementById('ticket-details-body');
    const emptyRow = document.getElementById('ticket-details-empty');
    const closeButton = document.getElementById('ticket-details-close');
    const resetStatusBtn = document.getElementById('reset-status-filter');
    const resetAssigneeBtn = document.getElementById('reset-assignee-filter');

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

    const statusColors = {
        open: '#f97316',
        pending: '#f59e0b',
        solved: '#10b981',
        closed: '#64748b',
        new: '#8b5cf6',
        'on-hold': '#06b6d4'
    };

    let selectedButton = null;

    function hideDetails() {
        if (!detailSection) return;
        detailSection.hidden = true;
        countButtons.forEach(function (button) {
            button.setAttribute('aria-expanded', 'false');
            button.setAttribute('aria-pressed', 'false');
        });
        if (selectedButton) {
            selectedButton.focus();
            selectedButton = null;
        }
        if (resetStatusBtn) resetStatusBtn.hidden = true;
        if (resetAssigneeBtn) resetAssigneeBtn.hidden = true;
    }

    function showTicketDetails(filterFn, labelText, activeBtn) {
        if (!detailSection || !detailTitle || !detailLabel || !detailCount) return;

        countButtons.forEach(function (button) {
            button.setAttribute('aria-expanded', 'false');
            button.setAttribute('aria-pressed', 'false');
        });

        if (activeBtn) {
            activeBtn.setAttribute('aria-expanded', 'true');
            activeBtn.setAttribute('aria-pressed', 'true');
            selectedButton = activeBtn;
        } else {
            selectedButton = null;
        }

        const visibleRows = [];
        ticketRows.forEach(function (row) {
            const matches = filterFn(row);
            row.hidden = !matches;
            if (matches) visibleRows.push(row);
        });

        if (emptyRow) {
            emptyRow.hidden = visibleRows.length !== 0;
            const td = emptyRow.querySelector('td');
            if (td) {
                td.textContent = `No tickets found matching "${labelText}" in the selected date range.`;
            }
        }

        detailLabel.textContent = labelText;
        detailCount.textContent = visibleRows.length;
        detailSection.hidden = false;

        detailSection.scrollIntoView({
            behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches
                ? 'auto'
                : 'smooth',
            block: 'start'
        });
        detailTitle.focus({ preventScroll: true });
    }

    function filterByStatus(status, activeBtn) {
        const normalized = (status || 'all').toLowerCase();
        const displayLabel = labels[normalized] || `${status} tickets`;

        if (resetStatusBtn) resetStatusBtn.hidden = (normalized === 'all');
        if (resetAssigneeBtn) resetAssigneeBtn.hidden = true;

        showTicketDetails(function (row) {
            return normalized === 'all' || row.dataset.status === normalized;
        }, displayLabel, activeBtn);
    }

    function filterByAssignee(assigneeName) {
        if (!assigneeName) return;
        const activeStatuses = ['new', 'open', 'pending', 'on-hold', 'hold'];

        if (resetAssigneeBtn) resetAssigneeBtn.hidden = false;
        if (resetStatusBtn) resetStatusBtn.hidden = true;

        showTicketDetails(function (row) {
            const rowAssignee = row.dataset.assignee || 'Unassigned';
            const rowStatus = (row.dataset.status || '').toLowerCase();
            return rowAssignee === assigneeName && activeStatuses.includes(rowStatus);
        }, `Active tickets for ${assigneeName}`, null);
    }

    // Connect KPI buttons
    countButtons.forEach(function (button) {
        button.setAttribute('aria-pressed', 'false');
        button.addEventListener('click', function () {
            const status = this.dataset.status || 'all';
            if (selectedButton === this && !detailSection.hidden) {
                hideDetails();
                return;
            }
            filterByStatus(status, this);
        });
    });

    if (closeButton) {
        closeButton.addEventListener('click', hideDetails);
    }

    if (resetStatusBtn) {
        resetStatusBtn.addEventListener('click', function () {
            filterByStatus('all', null);
            this.hidden = true;
        });
    }

    if (resetAssigneeBtn) {
        resetAssigneeBtn.addEventListener('click', function () {
            filterByStatus('all', null);
            this.hidden = true;
        });
    }

    // Initialize Chart.js charts
    initCharts();

    function initCharts() {
        const chartDataEl = document.getElementById('chart-data');
        if (!chartDataEl || typeof Chart === 'undefined') {
            return;
        }

        let chartData = null;
        try {
            chartData = JSON.parse(chartDataEl.textContent || '{}');
        } catch (e) {
            console.error('Failed to parse chart-data JSON:', e);
            return;
        }

        if (!chartData || !chartData.has_data) {
            return;
        }

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
        Chart.defaults.font.size = 12;
        Chart.defaults.color = 'oklch(49% 0.025 250)';
        Chart.defaults.animation.duration = prefersReducedMotion ? 0 : 500;

        // Plugin 1: Display total number at the end of each horizontal stacked bar on the right
        const assigneeBarTotalsPlugin = {
            id: 'assigneeBarTotals',
            afterDatasetsDraw(chart) {
                const { ctx, scales: { x } } = chart;
                const meta0 = chart.getDatasetMeta(0);
                if (!meta0 || !meta0.data || !meta0.data.length) return;

                ctx.save();
                ctx.font = '600 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = 'oklch(27% 0.025 250)';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';

                const barCount = meta0.data.length;
                for (let i = 0; i < barCount; i++) {
                    let total = 0;
                    let maxX = x ? x.getPixelForValue(0) : 0;

                    chart.data.datasets.forEach((dataset, dsIndex) => {
                        const val = Number(dataset.data[i]) || 0;
                        total += val;
                        const meta = chart.getDatasetMeta(dsIndex);
                        if (meta && meta.data && meta.data[i] && !meta.hidden) {
                            if (meta.data[i].x > maxX) {
                                maxX = meta.data[i].x;
                            }
                        }
                    });

                    if (meta0.data[i]) {
                        const yPos = meta0.data[i].y;
                        ctx.fillText(String(total), maxX + 7, yPos);
                    }
                }
                ctx.restore();
            }
        };

        // Plugin 2: Display ticket numbers directly on donut slices and center total
        const donutLabelsPlugin = {
            id: 'donutLabels',
            beforeDraw(chart) {
                const { ctx, chartArea } = chart;
                if (!chartArea) return;
                const meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data || !meta.data.length) return;
                const arc0 = meta.data[0];
                if (!arc0) return;

                const centerX = arc0.x;
                const centerY = arc0.y;
                const total = chart.data.datasets[0].data.reduce((a, b) => a + Number(b || 0), 0);

                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                ctx.font = '500 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = 'oklch(49% 0.025 250)';
                ctx.fillText('Total', centerX, centerY - 11);

                ctx.font = '700 20px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = 'oklch(27% 0.025 250)';
                ctx.fillText(String(total), centerX, centerY + 10);
                ctx.restore();
            },
            afterDatasetsDraw(chart) {
                const { ctx } = chart;
                const meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data || !meta.data.length) return;

                ctx.save();
                ctx.font = '700 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#ffffff';

                meta.data.forEach((arc, i) => {
                    const val = chart.data.datasets[0].data[i];
                    if (!val || val <= 0) return;

                    const arcSpan = arc.endAngle - arc.startAngle;
                    if (arcSpan >= 0.26) {
                        const angle = (arc.startAngle + arc.endAngle) / 2;
                        const radius = (arc.innerRadius + arc.outerRadius) / 2;
                        const x = arc.x + Math.cos(angle) * radius;
                        const y = arc.y + Math.sin(angle) * radius;

                        ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
                        ctx.shadowBlur = 3;
                        ctx.fillText(String(val), x, y);
                        ctx.shadowBlur = 0;
                    }
                });
                ctx.restore();
            }
        };

        // Plugin 3: Display ticket numbers directly above line chart data points
        const linePointLabelsPlugin = {
            id: 'linePointLabels',
            afterDatasetsDraw(chart) {
                const { ctx } = chart;
                const meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data || !meta.data.length) return;

                const dataset = chart.data.datasets[0];
                ctx.save();
                ctx.font = '600 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = '#1d4ed8';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';

                meta.data.forEach((point, index) => {
                    const val = dataset.data[index];
                    if (val === undefined || val === null) return;
                    if (val > 0 && typeof point.x === 'number' && typeof point.y === 'number') {
                        ctx.fillText(String(val), point.x, point.y - 5);
                    }
                });
                ctx.restore();
            }
        };

        // 1. Status Breakdown Donut Chart
        const statusCanvas = document.getElementById('statusChart');
        if (statusCanvas && chartData.status_distribution) {
            const dist = chartData.status_distribution;
            const bgColors = dist.statuses.map(st => statusColors[st] || '#94a3b8');
            const totalStatusTickets = dist.counts.reduce((a, b) => a + b, 0);

            new Chart(statusCanvas, {
                type: 'doughnut',
                data: {
                    labels: dist.labels,
                    datasets: [{
                        data: dist.counts,
                        backgroundColor: bgColors,
                        borderWidth: 2,
                        borderColor: '#ffffff',
                        hoverOffset: 6
                    }]
                },
                plugins: [donutLabelsPlugin],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '66%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                boxHeight: 12,
                                borderRadius: 3,
                                usePointStyle: true,
                                padding: 12,
                                font: { size: 11, weight: '500' },
                                generateLabels: function (chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        const dataset = data.datasets[0];
                                        return data.labels.map((label, i) => {
                                            const val = dataset.data[i] || 0;
                                            const meta = chart.getDatasetMeta(0);
                                            return {
                                                text: `${label} (${val})`,
                                                fillStyle: dataset.backgroundColor[i] || '#94a3b8',
                                                strokeStyle: '#ffffff',
                                                lineWidth: 2,
                                                hidden: isNaN(dataset.data[i]) || (meta.data[i] && meta.data[i].hidden),
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const val = context.raw || 0;
                                    const pct = totalStatusTickets > 0 ? ((val / totalStatusTickets) * 100).toFixed(1) : 0;
                                    return ` ${context.label}: ${val} (${pct}%)`;
                                }
                            }
                        }
                    },
                    onHover: function (evt, elements) {
                        evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                    },
                    onClick: function (evt, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const clickedStatus = dist.statuses[index];
                            const matchingBtn = document.querySelector(`.kpi-value-button[data-status="${clickedStatus}"]`);
                            filterByStatus(clickedStatus, matchingBtn);
                        }
                    }
                }
            });
        }

        // 2. Top 10 Assignees Stacked Bar Chart
        const assigneeCanvas = document.getElementById('assigneeChart');
        if (assigneeCanvas && chartData.assignees_workload && chartData.assignees_workload.labels.length > 0) {
            const workload = chartData.assignees_workload;
            const ds = workload.datasets;

            new Chart(assigneeCanvas, {
                type: 'bar',
                data: {
                    labels: workload.labels,
                    datasets: [
                        {
                            label: 'New',
                            data: ds.new,
                            backgroundColor: statusColors.new,
                            borderRadius: 2
                        },
                        {
                            label: 'Open',
                            data: ds.open,
                            backgroundColor: statusColors.open,
                            borderRadius: 2
                        },
                        {
                            label: 'Pending',
                            data: ds.pending,
                            backgroundColor: statusColors.pending,
                            borderRadius: 2
                        },
                        {
                            label: 'On-hold',
                            data: ds.on_hold,
                            backgroundColor: statusColors['on-hold'],
                            borderRadius: 2
                        }
                    ]
                },
                plugins: [assigneeBarTotalsPlugin],
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            right: 32
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            beginAtZero: true,
                            grace: '8%',
                            ticks: { precision: 0, font: { size: 11 } },
                            grid: { color: 'rgba(0, 0, 0, 0.05)' }
                        },
                        y: {
                            stacked: true,
                            ticks: {
                                font: { size: 11, weight: '500' },
                                callback: function (val) {
                                    const label = this.getLabelForValue(val);
                                    return label.length > 18 ? label.substring(0, 16) + '...' : label;
                                }
                            },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 10,
                                boxHeight: 10,
                                borderRadius: 2,
                                usePointStyle: true,
                                padding: 10,
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                title: function (contexts) {
                                    return contexts.length ? contexts[0].label : '';
                                }
                            }
                        }
                    },
                    onHover: function (evt, elements) {
                        evt.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                    },
                    onClick: function (evt, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const clickedAssignee = workload.labels[index];
                            filterByAssignee(clickedAssignee);
                        }
                    }
                }
            });
        }

        // 3. Daily Ticket Volume Trend Area Chart
        const trendCanvas = document.getElementById('trendChart');
        if (trendCanvas && chartData.daily_trends && chartData.daily_trends.labels.length > 0) {
            const trends = chartData.daily_trends;

            new Chart(trendCanvas, {
                type: 'line',
                data: {
                    labels: trends.labels,
                    datasets: [{
                        label: 'Created Tickets',
                        data: trends.counts,
                        tension: 0.35,
                        fill: true,
                        borderColor: '#2563eb',
                        borderWidth: 2,
                        pointBackgroundColor: '#2563eb',
                        pointHoverRadius: 6,
                        pointRadius: trends.labels.length > 45 ? 0 : (trends.labels.length > 20 ? 2 : 3),
                        backgroundColor: function (context) {
                            const chart = context.chart;
                            const { ctx, chartArea } = chart;
                            if (!chartArea) {
                                return 'rgba(37, 99, 235, 0.12)';
                            }
                            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                            gradient.addColorStop(0, 'rgba(37, 99, 235, 0.28)');
                            gradient.addColorStop(1, 'rgba(37, 99, 235, 0.01)');
                            return gradient;
                        }
                    }]
                },
                plugins: [linePointLabelsPlugin],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 18,
                            right: 14,
                            left: 6
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 14,
                                font: { size: 11 }
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grace: '10%',
                            ticks: { precision: 0, font: { size: 11 } },
                            grid: { color: 'rgba(0, 0, 0, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                title: function (contexts) {
                                    if (!contexts.length) return '';
                                    const idx = contexts[0].dataIndex;
                                    const fullDate = trends.full_dates && trends.full_dates[idx] ? trends.full_dates[idx] : contexts[0].label;
                                    return `Date: ${fullDate}`;
                                },
                                label: function (context) {
                                    return ` Tickets Created: ${context.raw}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
});
