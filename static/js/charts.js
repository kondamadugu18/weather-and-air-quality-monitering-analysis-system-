/**
 * AeroWatch Modular Chart.js Helper Scripts
 */

// Global Chart.js dark defaults
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94A3B8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
}

function renderLineChart(canvasId, labels, datasets, yTitle = '') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#E2E8F0', font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: '#1E293B',
                    titleColor: '#38BDF8',
                    bodyColor: '#F8FAFC',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                y: {
                    title: { display: !!yTitle, text: yTitle, color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

function renderBarChart(canvasId, labels, datasets, yTitle = '') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#E2E8F0' }
                },
                tooltip: {
                    backgroundColor: '#1E293B',
                    titleColor: '#38BDF8',
                    bodyColor: '#F8FAFC'
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    title: { display: !!yTitle, text: yTitle, color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}
