document.addEventListener('DOMContentLoaded', loadReports);

// Store chart instances globally to destroy them before re-creating
let chartComparison = null;
let chartTrend = null;
let chartCategories = null;
let chartTop5 = null;

async function loadReports() {
    try {
        const res = await axios.get('/api/reports');
        const data = res.data;

        // --- 1. Update Cards ---
        document.getElementById('cardIncome').textContent = fmtMoney(data.cards.income);
        document.getElementById('cardProfit').textContent = fmtMoney(data.cards.profit);
        document.getElementById('cardTicket').textContent = fmtMoney(data.cards.avg_ticket);

        // --- 2. Update Stock Alerts Table ---
        const tbody = document.getElementById('stockAlertBody');
        tbody.innerHTML = '';

        if (!data.alerts || data.alerts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted">¡Todo bien! No hay stock crítico.</td></tr>';
        } else {
            data.alerts.forEach(item => {
                tbody.innerHTML += `
                <tr>
                    <td class="fw-bold text-dark">${item.producto}</td>
                    <td class="text-muted small">${item.variante}</td>
                    <td class="text-danger fw-bold text-center">${item.stock} un.</td>
                    <td class="text-end"><span class="badge bg-danger rounded-pill">Reabastecer</span></td>
                </tr>
            `;
            });
        }

        // --- 3. Initialize/Update Charts ---

        // Helper to clean up old charts
        const resetChart = (chartInstance) => {
            if (chartInstance) chartInstance.destroy();
        };

        resetChart(chartComparison);
        resetChart(chartTrend);
        resetChart(chartCategories);
        resetChart(chartTop5);

        // Chart 1: Comparison (Bar)
        const ctxComparison = document.getElementById('chartComparison').getContext('2d');
        chartComparison = new Chart(ctxComparison, {
            type: 'bar',
            data: {
                labels: ['Ayer', 'Hoy'],
                datasets: [{
                    label: 'Ventas (S/)',
                    data: [data.charts.comparison.yesterday, data.charts.comparison.today],
                    backgroundColor: ['#9ca3af', '#4f46e5'],
                    borderRadius: 6,
                    barThickness: 50
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });

        // Chart 2: Monthly Trend (Line)
        const ctxTrend = document.getElementById('chartTrend').getContext('2d');
        chartTrend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: data.charts.trend.labels,
                datasets: [{
                    label: 'Ventas Diarias',
                    data: data.charts.trend.values,
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });

        // Chart 3: Category Profit (Doughnut)
        const ctxCat = document.getElementById('chartCategories').getContext('2d');
        chartCategories = new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: data.charts.categories.labels,
                datasets: [{
                    data: data.charts.categories.values,
                    backgroundColor: [
                        '#4f46e5', '#10b981', '#f59e0b', '#ef4444',
                        '#8b5cf6', '#ec4899', '#6366f1'
                    ],
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true } }
                }
            }
        });

        // Chart 4: Top 5 Bestsellers (Horizontal Bar)
        const ctxTop5 = document.getElementById('chartTop5').getContext('2d');
        chartTop5 = new Chart(ctxTop5, {
            type: 'bar',
            data: {
                labels: data.charts.top5.labels,
                datasets: [{
                    label: 'Unidades',
                    data: data.charts.top5.values,
                    backgroundColor: '#10b981', // Green for success
                    borderRadius: 4,
                    barThickness: 20
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bars
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });

    } catch (error) {
        console.error("Error loading reports data:", error);
        // Optional: Show error in UI
    }
}

function fmtMoney(val) {
    return 'S/ ' + (parseFloat(val) || 0).toFixed(2);
}
