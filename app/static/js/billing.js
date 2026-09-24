let cart = []; // Array to store { id, name, price, qty, stock }

const searchInput = document.getElementById('productSearch');
const resultsResults = document.getElementById('searchResults');
const tableBody = document.getElementById('billingTableBody');
const emptyRow = document.getElementById('emptyRow');
const totalDisplay = document.getElementById('totalAmount');

// Search Logic
let debounceTimer;
searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();

    if (query.length < 2) {
        resultsResults.style.display = 'none';
        return;
    }

    debounceTimer = setTimeout(() => {
        fetch(`/api/search_variants?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                resultsResults.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(item => {
                        const isNestedOption = item.id.toString().includes('_');
                        const badgeColor = isNestedOption ? 'bg-success' : 'bg-primary';

                        const a = document.createElement('a');
                        a.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center p-3 mb-1 border rounded shadow-sm'; // Tactile: padding, spacing, shadow
                        a.style.cursor = 'pointer';
                        a.innerHTML = `
                            <div>
                                <span class="fs-5 fw-bold text-dark">${item.nombre_completo}</span><br>
                                <small class="text-muted fs-6">Stock: ${item.stock}</small>
                            </div>
                            <span class="badge ${badgeColor} rounded-pill fs-6 px-3 py-2">S/ ${item.precio_sugerido.toFixed(2)}</span>
                        `;
                        a.onclick = () => addToCart(item);
                        resultsResults.appendChild(a);
                    });
                    resultsResults.style.display = 'block';
                } else {
                    resultsResults.style.display = 'none';
                }
            });
    }, 300);
});

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsResults.contains(e.target)) {
        resultsResults.style.display = 'none';
    }
});

function addToCart(item) {
    // Hide dropdown
    resultsResults.style.display = 'none';
    searchInput.value = '';

    // Check stock
    if (item.stock <= 0) {
        Swal.fire('Sin Stock', 'Este producto no tiene stock disponible.', 'error');
        return;
    }

    // Check exists
    const existing = cart.find(p => p.id === item.id);
    if (existing) {
        if (existing.qty < item.stock) {
            existing.qty++;
        } else {
            Swal.fire('Límite', 'Stock máximo alcanzado.', 'warning');
        }
    } else {
        cart.push({
            id: item.id,
            name: item.nombre_completo,
            price: item.precio_sugerido,
            qty: 1,
            stock: item.stock
        });
    }
    renderCart();
}

function renderCart() {
    tableBody.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        tableBody.appendChild(emptyRow);
        totalDisplay.textContent = 'S/ 0.00';
        return;
    }

    cart.forEach((item, index) => {
        const subtotal = item.price * item.qty;
        total += subtotal;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span class="fw-medium">${item.name}</span></td>
            <td>
                <input type="number" class="form-control form-control-sm" style="width: 100px;" 
                       value="${item.price.toFixed(2)}" step="0.5" 
                       onchange="updatePrice(${index}, this.value)">
            </td>
            <td>
                <input type="number" class="form-control form-control-sm" style="width: 80px;" 
                       value="${item.qty}" min="1" max="${item.stock}" 
                       onchange="updateQty(${index}, this.value)">
            </td>
            <td class="fw-bold">S/ ${subtotal.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger border-0" onclick="removeItem(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
        tableBody.appendChild(tr);
    });

    totalDisplay.textContent = `S/ ${total.toFixed(2)}`;
}

window.updatePrice = (index, val) => {
    val = parseFloat(val);
    if (val < 0) val = 0;
    cart[index].price = val;
    renderCart();
}

window.updateQty = (index, val) => {
    val = parseInt(val);
    const item = cart[index];
    if (val > item.stock) {
        Swal.fire('Error', `Stock insuficiente. Disponible: ${item.stock}`, 'error');
        val = item.stock;
    }
    if (val < 1) val = 1;
    cart[index].qty = val;
    renderCart();
}

window.removeItem = (index) => {
    cart.splice(index, 1);
    renderCart();
}

window.clearCart = () => {
    cart = [];
    renderCart();
}

window.setPaymentMethod = (method, btn) => {
    const input = document.getElementById('paymentMethod');
    input.value = method;

    // Visual updates for Buttons
    const buttons = btn.parentElement.querySelectorAll('button');
    buttons.forEach(b => {
        b.classList.remove('btn-primary', 'text-white');
        b.classList.add('btn-outline-secondary');
    });

    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-primary', 'text-white');

    // Toggle Cash Section
    const container = document.getElementById('cashChangeContainer');
    if (method === 'Efectivo') {
        container.style.display = 'block';
        document.getElementById('cashInput').focus();
        calcChange();
    } else {
        container.style.display = 'none';
    }
}

window.calcChange = () => {
    const total = cart.reduce((acc, item) => acc + (item.price * item.qty), 0);
    const paidStr = document.getElementById('cashInput').value;
    const paid = parseFloat(paidStr) || 0;
    const change = paid - total;

    const display = document.getElementById('changeDisplay');

    if (paid < total && paidStr) {
        display.innerHTML = `<span class="text-danger">Faltan S/ ${(total - paid).toFixed(2)}</span>`;
    } else {
        display.className = 'h3 fw-bold text-primary mb-0';
        display.textContent = `S/ ${Math.max(0, change).toFixed(2)}`;
    }
}

// Hook renderCart to update change if total updates
const originalRenderCart = renderCart;
renderCart = () => {
    originalRenderCart();
    if (document.getElementById('paymentMethod').value === 'Efectivo') {
        calcChange();
    }
};

window.finalizeSale = async () => {
    if (cart.length === 0) {
        Swal.fire('Carrito Vacío', 'Agrega productos antes de finalizar.', 'info');
        return;
    }

    const method = document.getElementById('paymentMethod').value;
    const total = cart.reduce((acc, item) => acc + (item.price * item.qty), 0);

    // Validation for Cash
    if (method === 'Efectivo') {
        const paid = parseFloat(document.getElementById('cashInput').value) || 0;
        if (paid < total) {
            Swal.fire({
                icon: 'warning',
                title: 'Monto Insuficiente',
                text: `El pago en efectivo es menor al total. Faltan S/ ${(total - paid).toFixed(2)}`,
                confirmButtonColor: '#ffc107'
            });
            return;
        }
    }

    const payload = {
        total: total,
        metodo_pago: method,
        items: cart.map(item => ({
            id: item.id,
            cantidad: item.qty,
            precio: item.price
        }))
    };

    try {
        const res = await axios.post('/process_sale', payload);
        if (res.data.success) {
            // Show change in success message for convenience
            let msg = 'La venta se ha procesado correctamente.';
            if (method === 'Efectivo') {
                const paid = parseFloat(document.getElementById('cashInput').value) || 0;
                msg += ` Vuelto: S/ ${(paid - total).toFixed(2)}`;
            }

            Swal.fire('¡Venta Exitosa!', msg, 'success');
            clearCart();
            document.getElementById('cashInput').value = '';
            calcChange();
        }
    } catch (err) {
        console.error(err);
        const msg = err.response?.data?.message || 'Hubo un problema al procesar la venta.';
        Swal.fire('Error', msg, 'error');
    }
}
