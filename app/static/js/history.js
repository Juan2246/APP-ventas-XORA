document.addEventListener('DOMContentLoaded', loadHistory);

async function loadHistory() {
    const date = document.getElementById('filterDate').value;
    const search = document.getElementById('filterSearch').value;

    try {
        const res = await axios.get('/api/history', { params: { date, search } });
        const data = res.data;
        const tbody = document.getElementById('historyTable');
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-5 text-muted">No se encontraron registros.</td></tr>';
            return;
        }

        data.forEach(item => {
            const profitClass = item.ganancia >= 0 ? 'text-success' : 'text-danger';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="small text-muted">${item.fecha}</td>
                <td>
                    <div class="fw-bold">${item.producto}</div>
                    <div class="small text-muted">${item.variante}</div>
                </td>
                <td><span class="badge bg-secondary bg-opacity-10 text-secondary border">${item.metodo}</span></td>
                <td class="text-center">${item.cantidad}</td>
                <td>S/ ${item.precio_unitario.toFixed(2)}</td>
                <td class="fw-bold">S/ ${item.total_venta.toFixed(2)}</td>
                <td class="fw-bold ${profitClass}">S/ ${item.ganancia.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error(error);
    }
}
