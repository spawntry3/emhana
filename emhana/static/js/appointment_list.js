(function () {
    const form = document.getElementById('filterForm');
    const qInput = document.getElementById('q');
    const statusSelect = document.getElementById('status');
    const doctorSelect = document.getElementById('doctor_id');
    const tbody = document.getElementById('appointmentsTbody');
    const pagBox = document.getElementById('paginationContainer');
    const totalCounter = document.getElementById('totalCounter');
    const spinner = document.getElementById('searchSpinner');

    if (!form || !tbody) return;

    let debounceTimer;
    let currentPage = 1;

    function buildUrl(page) {
        const params = new URLSearchParams();
        if (qInput.value.trim())     params.set('q', qInput.value.trim());
        if (statusSelect.value)      params.set('status', statusSelect.value);
        if (doctorSelect.value)      params.set('doctor_id', doctorSelect.value);
        params.set('page', page);
        return '?' + params.toString();
    }

    async function fetchPage(page) {
        currentPage = page;
        spinner.classList.remove('d-none');
        try {
            const resp = await fetch(buildUrl(page), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            tbody.innerHTML = data.rows_html;
            pagBox.innerHTML = data.pagination_html;
            totalCounter.textContent = 'Всего: ' + data.total;

            history.replaceState(null, '', buildUrl(page));
        } catch (e) {
            console.error('Search error:', e);
        } finally {
            spinner.classList.add('d-none');
        }
    }

    qInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchPage(1), 300);
    });

    statusSelect.addEventListener('change', () => fetchPage(1));
    doctorSelect.addEventListener('change', () => fetchPage(1));

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        fetchPage(1);
    });

    pagBox.addEventListener('click', function (e) {
        const link = e.target.closest('a.page-link');
        if (!link) return;
        e.preventDefault();
        const page = parseInt(link.dataset.page, 10);
        if (page && page !== currentPage) fetchPage(page);
    });
})();
