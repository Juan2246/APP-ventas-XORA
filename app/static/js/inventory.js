document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    loadOptions();
});

function resetModalForNewProduct() {
    const form = document.getElementById('addProductForm');
    form.reset();
    document.getElementById('variantId').value = '';
    document.getElementById('actionType').value = 'new';
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-box me-2"></i>Cargar Nueva Mercadería';

    // Enable everything
    document.getElementById('inputNombre').readOnly = false;
    document.getElementById('inputDiseno').readOnly = false;
    document.getElementById('catSelect').disabled = false;
    document.getElementById('origSelect').disabled = false;
    document.getElementById('selectProductType').disabled = false;
    document.getElementById('selectProductType').value = 'general'; // Default

    toggleProductType();
}

function toggleProductType() {
    const type = document.getElementById('selectProductType').value;
    const isNested = (type === 'cigarreria');
    const isGeneral = !isNested;

    // Toggle Category Visibility with d-none
    const catContainer = document.getElementById('container-categoria');
    const catSelect = document.getElementById('catSelect');

    if (isNested) {
        catContainer.classList.add('d-none');
        catSelect.value = 'Cigarros';
    } else {
        catContainer.classList.remove('d-none');
    }

    // Toggle Packaging Config
    document.getElementById('packagingConfig').style.display = isNested ? 'flex' : 'none';

    // Toggle Unit Load Selector
    document.getElementById('divUnitType').style.display = isNested ? 'block' : 'none';
    document.getElementById('divUnitLabel').style.display = isGeneral ? 'block' : 'none';

    // Toggle Price Inputs for Box/Sheet
    document.getElementById('divPriceBox').style.display = isNested ? 'block' : 'none';
    document.getElementById('divPriceSheet').style.display = isNested ? 'block' : 'none';

    // Rename Unit Price Label
    document.getElementById('lblPriceUnit').textContent = isNested ? 'Precio Cajetilla' : 'Precio Venta';

    updateCalculations();
}

function updateCalculations() {
    // Get Type
    const type = document.getElementById('selectProductType').value;
    const isNested = (type === 'cigarreria');

    // Get Config
    const sheetsPerBox = parseInt(document.getElementById('inputPlanchasCaja').value) || 1;
    const packsPerSheet = parseInt(document.getElementById('inputCajetillasPlancha').value) || 1;

    // Display summary
    if (isNested) {
        document.getElementById('lblPacksPerBox').textContent = sheetsPerBox * packsPerSheet;
    }

    // Get Stock Loading
    const qty = parseFloat(document.getElementById('inputStock').value) || 0;
    let multiplier = 1;

    if (isNested) {
        const unitType = document.getElementById('selectUnitType').value;
        if (unitType === 'caja') multiplier = sheetsPerBox * packsPerSheet;
        if (unitType === 'plancha') multiplier = packsPerSheet;
    }

    const totalUnits = qty * multiplier;
    document.getElementById('lblTotalUnits').textContent = totalUnits;

    // Cost Calc
    const totalCost = parseFloat(document.getElementById('inputCostoTotal').value) || 0;
    let costPerUnit = '-';

    if (totalUnits > 0 && totalCost > 0) {
        costPerUnit = (totalCost / totalUnits).toFixed(3);
        document.getElementById('inputPrecioCostoBase').value = costPerUnit;
    } else {
        // If manual cost per unit is set, show it?
        const manualBase = parseFloat(document.getElementById('inputPrecioCostoBase').value);
        if (manualBase) costPerUnit = manualBase.toFixed(3);
    }
    document.getElementById('lblCostPerUnit').textContent = costPerUnit;
}

async function loadOptions() {
    try {
        const res = await axios.get('/api/options');
        renderSelect(document.getElementById('catSelect'), res.data.categorias);
        renderSelect(document.getElementById('origSelect'), res.data.origenes);
    } catch (e) { console.error(e); }
}

function renderSelect(el, items) {
    const currentVal = el.value;
    el.innerHTML = '';
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        el.appendChild(opt);
    });
    if (currentVal) el.value = currentVal;
}

async function addNewOption(type) {
    const title = type === 'categoria' ? 'Nueva Categoría' : 'Nuevo Origen';
    const api = type === 'categoria' ? '/api/category' : '/api/origin';
    const { value: text } = await Swal.fire({
        title: title, input: 'text', inputLabel: 'Nombre', showCancelButton: true,
        inputValidator: (value) => { if (!value) return '¡Debes escribir algo!' }
    });
    if (text) {
        try {
            const res = await axios.post(api, { nombre: text });
            if (res.data.success) {
                Swal.fire('Guardado', 'Opción agregada', 'success');
                loadOptions();
            }
        } catch (e) { Swal.fire('Error', 'No se pudo guardar', 'error'); }
    }
}

async function openManageModal(type) {
    const title = type === 'categoria' ? 'Gestionar Categorías' : 'Gestionar Orígenes';
    document.getElementById('manageModalTitle').textContent = title;

    const list = document.getElementById('manageList');
    list.innerHTML = '<li class="list-group-item text-center"><i class="fas fa-spinner fa-spin"></i> Cargando...</li>';

    new bootstrap.Modal(document.getElementById('manageOptionsModal')).show();

    try {
        const res = await axios.get('/api/options');
        const items = type === 'categoria' ? res.data.categorias : res.data.origenes;

        renderManageList(type, items);
    } catch (e) {
        console.error(e);
        list.innerHTML = '<li class="list-group-item text-danger">Error al cargar datos.</li>';
    }
}

function renderManageList(type, items) {
    const list = document.getElementById('manageList');
    list.innerHTML = '';

    if (items.length === 0) {
        list.innerHTML = '<li class="list-group-item text-muted text-center">No hay registros.</li>';
        return;
    }

    items.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `
            <span>${item}</span>
            <button class="btn btn-sm btn-outline-danger border-0" onclick="deleteOption('${type}', '${item}')">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        list.appendChild(li);
    });
}

async function deleteOption(type, name) {
    const res = await Swal.fire({
        title: '¿Estás seguro?',
        text: `Se eliminará "${name}". Si está en uso, no se permitirá.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (res.isConfirmed) {
        const api = type === 'categoria' ? `/api/category/${encodeURIComponent(name)}` : `/api/origin/${encodeURIComponent(name)}`;
        try {
            const response = await axios.delete(api);
            if (response.data.success) {
                Swal.fire('Eliminado', 'El registro ha sido eliminado.', 'success');
                // Reload both the dropdowns and the manage list
                const optsRes = await axios.get('/api/options');
                // Refresh main selectors
                renderSelect(document.getElementById('catSelect'), optsRes.data.categorias);
                renderSelect(document.getElementById('origSelect'), optsRes.data.origenes);

                // Refresh Manage List
                const items = type === 'categoria' ? optsRes.data.categorias : optsRes.data.origenes;
                renderManageList(type, items);
            }
        } catch (err) {
            const msg = err.response?.data?.message || 'No se pudo eliminar.';
            Swal.fire('Error', msg, 'error');
        }
    }
}

async function loadInventory() {
    try {
        const res = await axios.get('/api/search?q=');
        const data = res.data;
        const tbody = document.getElementById('inventoryTable');
        tbody.innerHTML = '';

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-5 text-muted">Aún no hay productos registrados.</td></tr>';
            return;
        }

        data.forEach(item => {
            // Determine display type
            const isNested = (item.planchas_por_caja > 1 || item.cajetillas_por_plancha > 1); // Or check 'tipo' if exposed

            let priceDisplay = '';
            if (item.precio_sugerido_caja > 0) priceDisplay += `<div>Caja: S/ ${item.precio_sugerido_caja.toFixed(2)}</div>`;
            if (item.precio_sugerido_plancha > 0) priceDisplay += `<div>Plancha: S/ ${item.precio_sugerido_plancha.toFixed(2)}</div>`;
            priceDisplay += `<div>${isNested ? 'Cajetilla' : 'Unidad'}: S/ ${item.precio_sugerido.toFixed(2)}</div>`;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="ps-4 fw-bold text-dark">${item.nombre}</td>
                <td><span class="badge bg-light text-dark border">${item.categoria || '-'}</span></td>
                <td>${item.origen || '-'}</td>
                <td>${item.diseno || '-'}</td>
                <td class="text-center">
                    <span class="badge bg-info-subtle text-info-emphasis rounded-pill fs-7">
                        ${item.stock} un.
                    </span>
                </td>
                <td class="small">${priceDisplay}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick='openRestockModal(${JSON.stringify(item)})' title="Reabastecer">
                        <i class="fas fa-plus"></i>
                    </button>
                     <button class="btn btn-sm btn-outline-secondary" onclick='openEditModal(${JSON.stringify(item)})' title="Editar">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error loading inventory", error);
    }
}

function openRestockModal(item) {
    const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-boxes me-2"></i>Reabastecer Producto';
    document.getElementById('actionType').value = 'restock';
    document.getElementById('variantId').value = item.id;

    // Pre-select type based on existing config
    // Ideally we assume backend returns 'tipo'. If not, infer.
    // If config > 1 -> cigarreria
    let type = 'general';
    if (item.planchas_por_caja > 1 || item.cajetillas_por_plancha > 1) type = 'cigarreria';
    // Or if backend exposes 'tipo' use that. (We should update API to expose it)

    document.getElementById('selectProductType').value = type;
    document.getElementById('selectProductType').disabled = true; // Cannot change type during restock easily
    toggleProductType();

    // Prefill Info (Readonly)
    document.getElementById('inputNombre').value = item.nombre;
    document.getElementById('inputNombre').readOnly = true;

    document.getElementById('catSelect').value = item.categoria;
    document.getElementById('catSelect').disabled = true;

    document.getElementById('origSelect').value = item.origen;
    document.getElementById('origSelect').disabled = true;

    document.getElementById('inputDiseno').value = item.diseno || '';
    document.getElementById('inputDiseno').readOnly = true;

    // Config (Readonly)
    document.getElementById('inputPlanchasCaja').value = item.planchas_por_caja;
    document.getElementById('inputPlanchasCaja').readOnly = true;
    document.getElementById('inputCajetillasPlancha').value = item.cajetillas_por_plancha;
    document.getElementById('inputCajetillasPlancha').readOnly = true;

    // Clear Stock Entry
    document.getElementById('inputStock').value = '';
    document.getElementById('inputCostoTotal').value = '';

    // Prefill Current Prices (Editable)
    document.getElementById('inputPriceBox').value = item.precio_sugerido_caja;
    document.getElementById('inputPriceSheet').value = item.precio_sugerido_plancha;
    document.getElementById('inputPricePack').value = item.precio_sugerido;
    document.getElementById('inputPrecioCostoBase').value = item.precio_costo;

    updateCalculations();
    modal.show();
}

function openEditModal(item) {
    const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
    document.getElementById('modalTitle').innerHTML = '<i class="fas fa-edit me-2"></i>Editar Producto';
    document.getElementById('actionType').value = 'edit';
    document.getElementById('variantId').value = item.id;

    // Determine Type
    let type = 'general';
    if (item.planchas_por_caja > 1 || item.cajetillas_por_plancha > 1) type = 'cigarreria';
    document.getElementById('selectProductType').value = type;
    document.getElementById('selectProductType').disabled = false; // Can switch type in Edit
    toggleProductType();

    // Prefill ALL Fields (Editable)
    document.getElementById('inputNombre').value = item.nombre;
    document.getElementById('catSelect').value = item.categoria;
    document.getElementById('origSelect').value = item.origen;
    document.getElementById('inputDiseno').value = item.diseno || '';

    // Config
    document.getElementById('inputPlanchasCaja').value = item.planchas_por_caja;
    document.getElementById('inputCajetillasPlancha').value = item.cajetillas_por_plancha;

    document.getElementById('inputStock').value = 0;

    // Prices
    document.getElementById('inputPriceBox').value = item.precio_sugerido_caja;
    document.getElementById('inputPriceSheet').value = item.precio_sugerido_plancha;
    document.getElementById('inputPricePack').value = item.precio_sugerido;
    document.getElementById('inputPrecioCostoBase').value = item.precio_costo;

    updateCalculations();
    modal.show();
}

async function submitProduct() {
    const form = document.getElementById('addProductForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Fix numeric types
    data.planchas_por_caja = parseInt(data.planchas_por_caja);
    data.cajetillas_por_plancha = parseInt(data.cajetillas_por_plancha);
    data.stock = parseFloat(data.stock);
    data.costo_total = parseFloat(data.costo_total);
    data.precio_sugerido_caja = parseFloat(data.precio_sugerido_caja) || 0;
    data.precio_sugerido_plancha = parseFloat(data.precio_sugerido_plancha) || 0;
    data.precio_sugerido = parseFloat(data.precio_sugerido) || 0;
    data.precio_costo = parseFloat(data.precio_costo) || 0;

    try {
        const response = await axios.post('/api/product', data);
        if (response.data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Guardado',
                text: response.data.message,
                timer: 1500,
                showConfirmButton: false
            });

            bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
            loadInventory();
        }
    } catch (error) {
        Swal.fire('Error', error.response?.data?.message || 'No se pudo guardar', 'error');
    }
}
