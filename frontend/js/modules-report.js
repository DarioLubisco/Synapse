// Logic for the Refactored Report modules using @module-report-view

// Global State Caches
window.appState = window.appState || {};
window.appState.debitNotes = [];
window.appState.creditNotes = [];
window.appState.retenIva = [];
window.appState.retenIslr = [];

// Shared Number Formatter
const cf = new Intl.NumberFormat('es-VE', { style: 'currency', currency: 'VES' });
const cfd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

// ======================= DEBIT NOTES =======================
async function fetchDebitNotes() {
    const tbody = document.getElementById('debitNotesTableBody');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="10" class="loading-cell"><div class="loader"></div><p>Cargando notas de debito...</p></td></tr>`;

    try {
        const estatus = document.getElementById('dnFilterEstatus')?.value || "";
        const search = document.getElementById('dnFilterProv')?.value || "";
        
        let url = `/api/procurement/debit-notes?estatus=${estatus}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("API error");
        const json = await res.json();
        
        window.appState.debitNotes = Array.isArray(json.data) ? json.data : json;
        renderDebitNotes();
    } catch(err) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:red;">Error cargando datos.</td></tr>`;
        console.error(err);
    }
}

function renderDebitNotes() {
    const tbody = document.getElementById('debitNotesTableBody');
    if (!tbody) return;
    
    // Apply Date Filters
    const dIni = document.getElementById('dnFechaDesde')?.value;
    const dFin = document.getElementById('dnFechaHasta')?.value;
    const uSearch = (document.getElementById('dnFilterProv')?.value || '').toLowerCase().replace(/^0+/, '');
    const statusF = document.getElementById('dnFilterEstatus')?.value || '';

    let data = window.appState.debitNotes.filter(item => {
        if (statusF && item.EstatusND !== statusF) return false;
        
        // Universal search filter stripping leading zeros
        if (uSearch) { 
            const sProv = (item.CodProv || '').toLowerCase();
            const sDesc = (item.Descrip || '').toLowerCase();
            const sNumD = (item.NumeroD || '').toLowerCase().replace(/^0+/, '');
            const sNumN = (item.NumeroN || '').toLowerCase().replace(/^0+/, '');
            
            if(!sProv.includes(uSearch) && !sDesc.includes(uSearch) && !sNumD.includes(uSearch) && !sNumN.includes(uSearch)) return false;
        }
        // Date Logic (Emision)
        if (dIni && new Date(item.FechaE) < new Date(dIni)) return false;
        if (dFin && new Date(item.FechaE) > new Date(dFin)) return false;
        return true;
    });

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-secondary);">No hay notas de débito que coincidan.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(i => {
        return `<tr>
            <td class="col-checkbox"><input type="checkbox" data-id="${i.NumeroD}" data-prov="${i.CodProv}" class="dn-checkbox"></td>
            <td><strong>${i.ProveedorNombre || i.Descrip || i.CodProv}</strong></td>
            <td>${i.NumeroD}</td>
            <td>${i.FechaE ? i.FechaE.split('T')[0] : 'N/A'}</td>
            <td style="text-align: right;">${cf.format(i.MontoDocumentoBs || 0)}</td>
            <td style="text-align: right;">${cf.format(i.TotalPagadoBs || 0)}</td>
            <td style="text-align: right; color: var(--danger); font-weight: bold;">${cf.format(i.MontoNotaDebitoBs || 0)}</td>
            <td style="text-align: right; color: var(--warning);">${cf.format(i.MontoRetencionBs || 0)}</td>
            <td style="text-align: center;"><span class="badge badge-outline">${i.EstatusND || 'PENDIENTE'}</span></td>
            <td>${i.NotaDebitoID || '-'}</td>
            <td style="text-align: center;">
                ${(i.EstatusND !== 'ANULADA') ? `<button class="btn-icon" title="Anular" onclick="anularNotaDebito(${i.Id})"><i data-lucide="trash-2" style="color:var(--danger)"></i></button>` : ''}
            </td>
        </tr>`;
    }).join("");
    lucide.createIcons();
}

let sortAscDN = true;
function sortDebitNotes(field) {
    if (!window.appState.debitNotes) return;
    sortAscDN = !sortAscDN;
    window.appState.debitNotes.sort((a,b) => {
        let valA, valB;
        if (field === 'proveedor') { valA = a.Descrip; valB = b.Descrip; }
        else if (field === 'factura') { valA = a.NumeroD; valB = b.NumeroD; }
        else if (field === 'emision') { valA = a.FechaE; valB = b.FechaE; }
        else if (field === 'monto_orig') { valA = parseFloat(a.MontoDocumentoBs || 0); valB = parseFloat(b.MontoDocumentoBs || 0); }
        else if (field === 'total_pagado') { valA = parseFloat(a.TotalPagadoBs || 0); valB = parseFloat(b.TotalPagadoBs || 0); }
        else if (field === 'diferencial') { valA = parseFloat(a.MontoNotaDebitoBs || 0); valB = parseFloat(b.MontoNotaDebitoBs || 0); }
        
        if (valA < valB) return sortAscDN ? -1 : 1;
        if (valA > valB) return sortAscDN ? 1 : -1;
        return 0;
    });
    renderDebitNotes();
}

// ======================= CREDIT NOTES =======================
async function fetchCreditNotesView() {
    const tbody = document.getElementById('creditNotesTableBody');
    if(!tbody) return;
    tbody.innerHTML = `<tr><td colspan="10" class="loading-cell"><div class="loader"></div><p>Cargando notas de crédito...</p></td></tr>`;

    try {
        const estatus = document.getElementById('cnFilterEstatus')?.value || "";
        const search = document.getElementById('cnFilterProv')?.value || "";
        
        let url = `/api/procurement/credit-notes?estatus=${estatus}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("API error");
        const json = await res.json();
        
        window.appState.creditNotes = Array.isArray(json.data) ? json.data : json;
        renderCreditNotes();
    } catch(err) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;color:red;">Error cargando datos.</td></tr>`;
        console.error(err);
    }
}

function renderCreditNotes() {
    const tbody = document.getElementById('creditNotesTableBody');
    if (!tbody) return;

    const dIni = document.getElementById('cnFechaDesde')?.value;
    const dFin = document.getElementById('cnFechaHasta')?.value;
    const uSearch = (document.getElementById('cnFilterProv')?.value || '').toLowerCase().replace(/^0+/, '');
    const statusF = document.getElementById('cnFilterEstatus')?.value || '';
    
    let data = window.appState.creditNotes.filter(item => {
        if (statusF && item.Estatus !== statusF) return false;
        
        if (uSearch) {
            const sProv = (item.CodProv || '').toLowerCase();
            const sNota = (item.Notas1 || '').toLowerCase();
            const sNumD = (item.NumeroD || item.PagoRef || '').toLowerCase().replace(/^0+/, '');
            if(!sProv.includes(uSearch) && !sNota.includes(uSearch) && !sNumD.includes(uSearch)) return false;
        }
        if (dIni && new Date(item.FechaSolicitud) < new Date(dIni)) return false;
        if (dFin && new Date(item.FechaSolicitud) > new Date(dFin)) return false;
        return true;
    });

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-secondary);">No hay notas de crédito que coincidan.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(i => {
        return `<tr>
            <td><strong>${i.ProveedorNombre || i.Descrip || i.CodProv}</strong></td>
            <td>${i.NumeroD || i.PagoRef || '-'}</td>
            <td><span class="badge ${i.Motivo === 'INDEXACION' ? 'badge-info' : 'badge-default'}">${i.Motivo || 'N/A'}</span></td>
            <td class="amount" style="font-weight:bold; color:var(--success);">${cf.format(i.MontoBs || 0)}</td>
            <td class="amount">${i.TasaCambio ? i.TasaCambio.toFixed(4) : '-'}</td>
            <td class="amount" style="color:var(--success);">${cfd.format(i.MontoUsd || 0)}</td>
            <td>${i.FechaSolicitud ? new Date(i.FechaSolicitud).toLocaleDateString() : '-'}</td>
            <td style="text-align: center;"><span class="badge ${i.Estatus==='PENDIENTE'?'badge-warning':i.Estatus==='APLICADA'?'badge-success':'badge-default'}">${i.Estatus||'PENDIENTE'}</span></td>
            <td>${i.NotaCreditoID || '-'}</td>
            <td style="text-align: center;">
                <button class="btn-icon" title="Ver Detalles"><i data-lucide="eye"></i></button>
                ${(i.Estatus !== 'ANULADA') ? `<button class="btn-icon" title="Anular" onclick="anularNotaCredito(${i.Id})"><i data-lucide="trash-2" style="color:var(--danger)"></i></button>` : ''}
            </td>
        </tr>`;
    }).join("");
    lucide.createIcons();
}

let sortAscCN = true;
function sortCreditNotes(field) {
    if (!window.appState.creditNotes) return;
    sortAscCN = !sortAscCN;
    window.appState.creditNotes.sort((a,b) => {
        let valA, valB;
        if (field === 'proveedor') { valA = a.CodProv; valB = b.CodProv; }
        else if (field === 'factura') { valA = a.NumeroD; valB = b.NumeroD; }
        else if (field === 'motivo') { valA = a.Motivo; valB = b.Motivo; }
        else if (field === 'monto_bs') { valA = parseFloat(a.MontoBs || 0); valB = parseFloat(b.MontoBs || 0); }
        else if (field === 'tasa') { valA = parseFloat(a.TasaCambio || 0); valB = parseFloat(b.TasaCambio || 0); }
        else if (field === 'monto_usd') { valA = parseFloat(a.MontoUsd || 0); valB = parseFloat(b.MontoUsd || 0); }
        else if (field === 'fecha') { valA = a.FechaSolicitud; valB = b.FechaSolicitud; }
        else if (field === 'estatus') { valA = a.Estatus; valB = b.Estatus; }
        
        if (valA < valB) return sortAscCN ? -1 : 1;
        if (valA > valB) return sortAscCN ? 1 : -1;
        return 0;
    });
    renderCreditNotes();
}

// ======================= RETENCIONES IVA =======================
async function fetchRetencionesView() {
    const tbody = document.getElementById('retencionesTableBody');
    if(!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="loading-cell"><div class="loader"></div><p>Cargando retenciones IVA...</p></td></tr>`;

    try {
        const dIni = document.getElementById('retencionesDesde')?.value || "";
        const dFin = document.getElementById('retencionesHasta')?.value || "";
        
        let url = `/api/retenciones`;
        if (dIni || dFin) url += `?desde=${dIni}&hasta=${dFin}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("API error");
        const json = await res.json();
        
        window.appState.retenIva = Array.isArray(json.data) ? json.data : json;
        renderRetencionesIva();
    } catch(err) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:red;">Error cargando datos.</td></tr>`;
        console.error(err);
    }
}

function renderRetencionesIva() {
    const tbody = document.getElementById('retencionesTableBody');
    if (!tbody) return;

    const uSearch = (document.getElementById('retUniversalSearch')?.value || '').toLowerCase().replace(/^0+/, '');
    const statusF = document.getElementById('retFilterEstatus')?.value || "";
    
    let data = window.appState.retenIva.filter(item => {
        if (statusF && item.Estado !== statusF) return false;
        if (uSearch) {
            const sComp = (item.NumeroComprobante || '').toLowerCase();
            const sFact = (item.NumeroD || '').toLowerCase().replace(/^0+/, '');
            const sProv = (item.CodProv || '').toLowerCase();
            if(!sComp.includes(uSearch) && !sFact.includes(uSearch) && !sProv.includes(uSearch)) return false;
        }
        return true;
    });

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-secondary);">No hay retenciones de IVA que coincidan.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(i => {
        return `<tr>
            <td style="font-weight: 500; color: var(--primary-accent);">${i.NumeroComprobante}</td>
            <td>${i.NumeroD || '-'}</td>
            <td>${i.ProveedorNombre || i.Descrip || i.CodProv}</td>
            <td>${i.FechaRetencion ? i.FechaRetencion.split('T')[0] : '-'}</td>
            <td style="text-align: right;">${cf.format(i.MontoTotal || 0)}</td>
            <td style="text-align: right; color: var(--danger); font-weight: bold;">${cf.format(i.MontoRetenido || 0)}</td>
            <td style="text-align: center;">
                <span class="badge ${i.Estado==='GENERADO'?'badge-success':'badge-default'}">${i.Estado||'GENERADO'}</span>
            </td>
            <td style="text-align: center; display:flex; gap:0.25rem; justify-content:center;">
                <button class="btn-icon" title="Imprimir" onclick="window.open('/api/retenciones/${i.Id}/pdf', '_blank')"><i data-lucide="printer"></i></button>
                ${(i.Estado !== 'ANULADA' && i.Estado !== 'ENTERADO') ? `<button class="btn-icon" title="Anular" onclick="anularRetencionIVA(${i.Id})"><i data-lucide="trash-2" style="color:var(--danger)"></i></button>` : ''}
            </td>
        </tr>`;
    }).join("");
    lucide.createIcons();
}

let sortAscIva = true;
function sortRetenciones(field) {
    if (!window.appState.retenIva) return;
    sortAscIva = !sortAscIva;
    window.appState.retenIva.sort((a,b) => {
        let valA, valB;
        if (field === 'comprobante') { valA = a.NumeroComprobante; valB = b.NumeroComprobante; }
        else if (field === 'factura') { valA = a.NumeroD; valB = b.NumeroD; }
        else if (field === 'proveedor') { valA = a.CodProv; valB = b.CodProv; }
        else if (field === 'fecha') { valA = a.FechaRetencion; valB = b.FechaRetencion; }
        else if (field === 'monto_fact') { valA = parseFloat(a.MontoTotal || 0); valB = parseFloat(b.MontoTotal || 0); }
        else if (field === 'retenido') { valA = parseFloat(a.MontoRetenido || 0); valB = parseFloat(b.MontoRetenido || 0); }
        else if (field === 'estado') { valA = a.Estado; valB = b.Estado; }
        
        if (valA < valB) return sortAscIva ? -1 : 1;
        if (valA > valB) return sortAscIva ? 1 : -1;
        return 0;
    });
    renderRetencionesIva();
}

// ======================= RETENCIONES ISLR =======================
async function fetchRetencionesISLR() {
    const tbody = document.getElementById('retencionesIslrTableBody');
    if(!tbody) return;
    tbody.innerHTML = `<tr><td colspan="7" class="loading-cell"><div class="loader"></div><p>Cargando retenciones ISLR...</p></td></tr>`;

    try {
        const dIni = document.getElementById('islrDesde')?.value || "";
        const dFin = document.getElementById('islrHasta')?.value || "";
        
        let url = `/api/retenciones-islr`; 
        if (dIni || dFin) url += `?desde=${dIni}&hasta=${dFin}`;

        const res = await fetch(url);
        // Fallback for mocked behavior in case endpoint is not fully up for GET
        if (!res.ok) {
           console.warn("ISLR list endpoint returned non-200, simulating via general if available");
        }
        
        const json = await res.json();
        window.appState.retenIslr = Array.isArray(json.data) ? json.data : (Array.isArray(json) ? json : []);
        renderRetencionesIslr();
    } catch(err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:red;">Error consultando retenciones (o ruta no completada en backend).</td></tr>`;
        console.error(err);
    }
}

function renderRetencionesIslr() {
    const tbody = document.getElementById('retencionesIslrTableBody');
    if (!tbody) return;

    const uSearch = (document.getElementById('islrUniversalSearch')?.value || '').toLowerCase().replace(/^0+/, '');
    const statusF = document.getElementById('islrFilterEstatus')?.value || "";
    
    let data = window.appState.retenIslr.filter(item => {
        if (statusF && item.Estado !== statusF) return false;
        if (uSearch) {
            const sComp = (item.NumeroComprobante || '').toLowerCase();
            const sFact = (item.NumeroD || '').toLowerCase().replace(/^0+/, '');
            const sProv = (item.CodProv || '').toLowerCase();
            if(!sComp.includes(uSearch) && !sFact.includes(uSearch) && !sProv.includes(uSearch)) return false;
        }
        return true;
    });

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">No hay retenciones de ISLR.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(i => {
        return `<tr>
            <td style="font-weight: 500; color: var(--primary-accent);">${i.NumeroComprobante}</td>
            <td>${i.NumeroD || '-'}</td>
            <td>${i.ProveedorNombre || i.Descrip || i.CodProv}</td>
            <td>${i.FechaRetencion ? i.FechaRetencion.split('T')[0] : '-'}</td>
            <td style="text-align: right;">${cf.format(i.BaseImponibleBs || 0)}</td>
            <td style="text-align: right; color: var(--danger); font-weight: bold;">${cf.format(i.MontoRetenido || 0)}</td>
            <td style="text-align: center;"><span class="badge ${i.Estado==='GENERADO'?'badge-success':'badge-default'}">${i.Estado||'GENERADO'}</span></td>
            <td style="text-align: center;">
                ${(i.Estado !== 'ANULADA' && i.Estado !== 'ENTERADO') ? `<button class="btn-icon" title="Anular" onclick="anularRetencionISLR(${i.Id})"><i data-lucide="trash-2" style="color:var(--danger)"></i></button>` : ''}
            </td>
        </tr>`;
    }).join("");
    lucide.createIcons();
}

let sortAscIslr = true;
function sortIslrTable(field) {
    if (!window.appState.retenIslr) return;
    sortAscIslr = !sortAscIslr;
    window.appState.retenIslr.sort((a,b) => {
        let valA, valB;
        if (field === 'comprobante') { valA = a.NumeroComprobante; valB = b.NumeroComprobante; }
        else if (field === 'factura') { valA = a.NumeroD; valB = b.NumeroD; }
        else if (field === 'proveedor') { valA = a.CodProv; valB = b.CodProv; }
        else if (field === 'fecha') { valA = a.FechaRetencion; valB = b.FechaRetencion; }
        else if (field === 'base') { valA = parseFloat(a.BaseImponibleBs || 0); valB = parseFloat(b.BaseImponibleBs || 0); }
        else if (field === 'retenido') { valA = parseFloat(a.MontoRetenido || 0); valB = parseFloat(b.MontoRetenido || 0); }
        else if (field === 'estado') { valA = a.Estado; valB = b.Estado; }
        
        if (valA < valB) return sortAscIslr ? -1 : 1;
        if (valA > valB) return sortAscIslr ? 1 : -1;
        return 0;
    });
    renderRetencionesIslr();
}

function debouncedIslrSearch() {
    clearTimeout(window._islrSearchTimeout);
    window._islrSearchTimeout = setTimeout(renderRetencionesIslr, 300);
}


// Event Listeners Hooks
document.addEventListener('DOMContentLoaded', () => {
    // Override the generic fetch calls with our new components when buttons are clicked
    const listen = (id, event, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener(event, fn);
    };

    // Debit Notes
    listen('refreshDebitNotesBtn', 'click', fetchDebitNotes);
    listen('dnFilterEstatus', 'change', fetchDebitNotes);
    listen('dnFilterProv', 'keyup', () => {
        clearTimeout(window._dnTmr);
        window._dnTmr = setTimeout(renderDebitNotes, 300);
    });

    // Credit Notes
    listen('refreshCreditNotesBtn', 'click', fetchCreditNotesView);
    listen('cnFilterEstatus', 'change', fetchCreditNotesView);
    listen('cnFilterProv', 'keyup', () => {
        clearTimeout(window._cnTmr);
        window._cnTmr = setTimeout(renderCreditNotes, 300);
    });

    // Retenciones IVA
    listen('refreshRetencionesBtn', 'click', fetchRetencionesView);
    listen('retFilterEstatus', 'change', renderRetencionesIva);
    listen('retUniversalSearch', 'keyup', () => {
        clearTimeout(window._ivaTmr);
        window._ivaTmr = setTimeout(renderRetencionesIva, 300);
    });

    // We override original globals so that sidebar clicks trigger our new functions
    window.fetchCreditNotes = fetchCreditNotesView;
    window._fetchRetenciones = fetchRetencionesView;
    
    // Wire up sidebar for ISLR explicitly since it didn't exist before in script.js logic block
    const islrNav = document.querySelector('.nav-item[data-view="retenciones-islr"]');
    if (islrNav) {
        islrNav.addEventListener('click', fetchRetencionesISLR);
    }
});

// ======================= HELP & CANCELLATIONS =======================

window.openHelpModal = function(module) {
    const modal = document.getElementById('helpModal');
    const body = document.getElementById('helpModalBody');
    if (!modal || !body) return;

    let html = '';
    switch(module) {
        case 'DN':
            html = `
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="clock" style="width: 16px; display: inline-block;"></i> PENDIENTE:</strong> La nota de débito ha sido generada por el sistema debido a un pago excesivo, pero aún no ha sido solicitada formalmente al proveedor.</li>
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="mail" style="width: 16px; display: inline-block;"></i> SOLICITUD ENVIADA:</strong> Se ha notificado al proveedor sobre el excedente vía correo, esperando la emisión legal de la nota.</li>
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="check-circle" style="width: 16px; display: inline-block;"></i> EMITIDA:</strong> El proveedor entregó la nota de débito, ya fue ingresada al sistema Saint y el saldo a favor está disponible.</li>
                <li><strong><i data-lucide="x-circle" style="width: 16px; display: inline-block;"></i> ANULADA:</strong> La transacción fue anulada antes de materializarse. El diferencial a favor se descartó.</li>
            </ul>`;
            break;
        case 'CN':
            html = `
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="clock" style="width: 16px; display: inline-block;"></i> PENDIENTE:</strong> Esperando revisión o carga en el sistema de facturación.</li>
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="check-circle" style="width: 16px; display: inline-block;"></i> APLICADA:</strong> Procesada correctamente e ingresada al estado de cuenta.</li>
                <li><strong><i data-lucide="x-circle" style="width: 16px; display: inline-block;"></i> ANULADA:</strong> Cancelada permanentemente.</li>
            </ul>`;
            break;
        case 'IVA':
        case 'ISLR':
            html = `
            <ul style="list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="file-check" style="width: 16px; display: inline-block;"></i> GENERADO / EMITIDO:</strong> La retención fue calculada y el comprobante ha sido emitido localmente. El abono ha sido transferido en la base de datos de cuentas.</li>
                <li style="margin-bottom: 0.8rem;"><strong><i data-lucide="check-square" style="width: 16px; display: inline-block;"></i> ENTERADO:</strong> El comprobante de la retención ha sido subido/declarado exitosamente al portal del SENIAT. Por ende, no podrá ser anulado desde este módulo.</li>
                <li><strong><i data-lucide="x-circle" style="width: 16px; display: inline-block;"></i> ANULADA:</strong> El comprobante fue anulado internamente y el pago (abono) devuelto al saldo del proveedor.</li>
            </ul>`;
            break;
    }
    
    body.innerHTML = html;
    lucide.createIcons();
    modal.classList.add('active');
};

window.closeHelpModal = function() {
    document.getElementById('helpModal').classList.remove('active');
};

// --- CANCELLATION LOGIC ---
window.anularRetencionIVA = async function(id) {
    if (!confirm("¿Está seguro de anular esta Retención de IVA? Esta acción eliminará el abono asociado permanentemente.")) return;
    try {
        const res = await fetch(`/api/retenciones/${id}`, { method: 'PATCH' });
        if (!res.ok) throw new Error(await res.text());
        alert("Retención de IVA anulada correctamente.");
        fetchRetencionesView();
    } catch(err) {
        alert("Error al anular: " + err.message);
    }
};

window.anularRetencionISLR = async function(id) {
    if (!confirm("¿Está seguro de anular esta Retención ISLR? Esta acción eliminará el abono asociado permanentemente.")) return;
    try {
        const res = await fetch(`/api/retenciones-islr/${id}`, { method: 'PATCH' });
        if (!res.ok) throw new Error(await res.text());
        alert("Retención ISLR anulada correctamente.");
        fetchRetencionesISLR();
    } catch(err) {
        alert("Error al anular: " + err.message);
    }
};

window.anularNotaCredito = async function(id) {
    if (!confirm("¿Está seguro de anular esta Nota de Crédito?")) return;
    try {
        const res = await fetch(`/api/procurement/credit-notes/${id}`, { 
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ Estatus: 'ANULADA' })
        });
        if (!res.ok) throw new Error(await res.text());
        alert("Nota de Crédito anulada correctamente.");
        fetchCreditNotesView();
    } catch(err) {
        alert("Error al anular: " + err.message);
    }
};

window.anularNotaDebito = async function(id) {
    if (!confirm("¿Está seguro de anular esta Nota de Débito?")) return;
    try {
        const res = await fetch(`/api/procurement/debit-notes/${id}`, { method: 'PATCH' });
        if (!res.ok) throw new Error(await res.text());
        alert("Nota de Débito anulada correctamente.");
        fetchDebitNotes();
    } catch(err) {
        alert("Error al anular: " + err.message);
    }
};

