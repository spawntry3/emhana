document.addEventListener("DOMContentLoaded", function () {
    const readJSON = (id) => {
        const el = document.getElementById(id);
        return el ? JSON.parse(el.textContent) : null;
    };

    const cfg = window.EMHANA_DASHBOARD_CFG || {};
    const initialLabels = readJSON('initialDates') || [];
    const initialData = readJSON('initialCounts') || [];
    const statusLabels = readJSON('statusLabels') || [];
    const statusData = readJSON('statusData') || [];

    const ctx = document.getElementById('appointmentsChart').getContext('2d');
    const dynamicsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: initialLabels,
            datasets: [{
                label: 'Количество приёмов',
                data: initialData,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#0d6efd'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });

    const switcher = document.getElementById('periodSwitcher');
    const titleEl = document.getElementById('dynamicsTitle');
    const spinner = document.getElementById('chartSpinner');

    if (switcher) {
        switcher.addEventListener('click', async function (e) {
            const btn = e.target.closest('button[data-period]');
            if (!btn || btn.classList.contains('active')) return;

            switcher.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const period = btn.dataset.period;
            spinner.classList.remove('d-none');
            try {
                const resp = await fetch(cfg.chartUrl + '?period=' + period);
                if (!resp.ok) throw new Error('HTTP ' + resp.status);
                const data = await resp.json();
                dynamicsChart.data.labels = data.labels;
                dynamicsChart.data.datasets[0].data = data.counts;
                dynamicsChart.update();
                titleEl.textContent = data.title;
                const periodLabel = document.getElementById('periodLabel');
                if (periodLabel) periodLabel.textContent = data.title;
                history.replaceState(null, '', '?period=' + period);
            } catch (err) {
                console.error('Period switch failed:', err);
            } finally {
                spinner.classList.add('d-none');
            }
        });
    }

    const statusCanvas = document.getElementById('statusChart');
    if (statusCanvas) {
        new Chart(statusCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: statusLabels,
                datasets: [{
                    data: statusData,
                    backgroundColor: ['#ffc107', '#198754', '#6c757d'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                cutout: '65%',
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
});
