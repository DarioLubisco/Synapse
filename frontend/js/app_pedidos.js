document.addEventListener('DOMContentLoaded', () => {
    // Basic Elements
    const fileInput = document.getElementById('subtractionFiles');
    const dropArea = document.getElementById('dropArea');
    const fileListContainer = document.getElementById('fileListContainer');

    const form = document.getElementById('generateForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const alertBox = document.getElementById('alertBox');

    // Category Elements
    const categoriesList = document.getElementById('categoriesList');
    const categoryCount = document.getElementById('categoryCount');
    const categorySearch = document.getElementById('categorySearch');
    const btnSelectAll = document.getElementById('btnSelectAll');
    const btnSelectNone = document.getElementById('btnSelectNone');

    let selectedFiles = []; // Array to store files
    let categoryMap = {};
    let categoryTree = [];

    // --- CONFIG DEFAULTS LOGIC ---
    const btnSaveDefaults = document.getElementById('btnSaveDefaults');
    const inputDays = document.getElementById('pedidoDays');
    const inputRows = document.getElementById('numRows');
    const inputUmbral = document.getElementById('umbralRotacion');

    function loadDefaults() {
        const d_days = localStorage.getItem('syn_ped_days');
        const d_rows = localStorage.getItem('syn_ped_rows');
        const d_umbral = localStorage.getItem('syn_ped_umbral');
        
        if (d_days) inputDays.value = d_days;
        if (d_rows) inputRows.value = d_rows;
        if (d_umbral) inputUmbral.value = d_umbral;
    }
    
    if (btnSaveDefaults) {
        btnSaveDefaults.addEventListener('click', () => {
            localStorage.setItem('syn_ped_days', inputDays.value);
            localStorage.setItem('syn_ped_rows', inputRows.value);
            localStorage.setItem('syn_ped_umbral', inputUmbral.value);
            btnSaveDefaults.innerHTML = '<i class="fas fa-check"></i> Guardado';
            btnSaveDefaults.classList.remove('btn-secondary');
            btnSaveDefaults.classList.add('btn-primary');
            setTimeout(() => {
                btnSaveDefaults.innerHTML = '<i class="fas fa-save"></i> Guardar por Defecto';
                btnSaveDefaults.classList.remove('btn-primary');
                btnSaveDefaults.classList.add('btn-secondary');
            }, 2000);
        });
    }

    loadDefaults();

    // --- CATEGORY LOGIC ---
    async function fetchCategories() {
        try {
            const response = await fetch('/api/pedidos/categories');
            if (!response.ok) throw new Error("Fallo al obtener categorías");
            const data = await response.json();

            const rawCategories = data.categories || [];
            categoryMap = {};
            rawCategories.forEach(cat => {
                categoryMap[cat.id] = {
                    id: cat.id, name: cat.name, parentId: cat.parentId,
                    selected: true, indeterminate: false, children: [], visible: true
                };
            });

            categoryTree = [];
            Object.values(categoryMap).forEach(cat => {
                if (cat.parentId === "0" || !categoryMap[cat.parentId]) {
                    categoryTree.push(cat);
                } else {
                    categoryMap[cat.parentId].children.push(cat);
                }
            });

            renderCategories();
        } catch (error) {
            console.error(error);
            if (categoriesList) {
                categoriesList.innerHTML = `<li style="color:var(--danger); padding:1rem;">Error cargando categorías. Revisa la conexión al motor SQL.</li>`;
            }
        }
    }

    function renderCategories() {
        if (!categoriesList) return;
        categoriesList.innerHTML = '';
        let visibleCount = 0;

        function buildNodeDOM(node) {
            if (!node.visible) return null;
            visibleCount++;

            const li = document.createElement('li');
            li.style.listStyle = 'none';
            const hasChildren = node.children.some(c => c.visible);

            const row = document.createElement('div');
            row.style.display = 'flex';
            row.style.alignItems = 'center';
            row.style.gap = '0.5rem';
            row.style.padding = '0.25rem 0';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `cat_${node.id}`;
            checkbox.value = node.name;
            checkbox.checked = node.selected;
            checkbox.indeterminate = node.indeterminate;
            checkbox.addEventListener('change', (e) => handleCheckboxChange(node.id, e.target.checked));
            
            const label = document.createElement('label');
            label.htmlFor = `cat_${node.id}`;
            label.textContent = node.name;
            if(hasChildren) label.style.fontWeight = 'bold';

            row.appendChild(checkbox);
            row.appendChild(label);
            li.appendChild(row);

            if (hasChildren) {
                const ul = document.createElement('ul');
                ul.style.paddingLeft = '1.5rem';
                node.children.forEach(child => {
                    const childDOM = buildNodeDOM(child);
                    if (childDOM) ul.appendChild(childDOM);
                });
                li.appendChild(ul);
            }
            return li;
        }

        categoryTree.forEach(rootNode => {
            const nodeDOM = buildNodeDOM(rootNode);
            if (nodeDOM) categoriesList.appendChild(nodeDOM);
        });

        if (visibleCount === 0) categoriesList.innerHTML = `<li style="padding:1rem;">No se encontraron categorías.</li>`;
        updateCategoryCount();
    }

    function handleCheckboxChange(id, isChecked) {
        const node = categoryMap[id];
        if (!node) return;
        node.selected = isChecked;
        node.indeterminate = false;

        function updateChildren(n, checkState) {
            n.children.forEach(child => {
                child.selected = checkState;
                child.indeterminate = false;
                const cb = document.getElementById(`cat_${child.id}`);
                if (cb) { cb.checked = checkState; cb.indeterminate = false; }
                updateChildren(child, checkState);
            });
        }
        updateChildren(node, isChecked);
        updateParentState(node.parentId);
        updateCategoryCount();
    }

    function updateParentState(parentId) {
        if (!parentId || parentId === "0") return;
        const parent = categoryMap[parentId];
        if (!parent) return;

        let allSelected = true, noneSelected = true, hasIndeterminate = false;
        parent.children.forEach(child => {
            if (child.selected) noneSelected = false;
            else allSelected = false;
            if (child.indeterminate) hasIndeterminate = true;
        });

        if (allSelected && !hasIndeterminate) { parent.selected = true; parent.indeterminate = false; }
        else if (noneSelected && !hasIndeterminate) { parent.selected = false; parent.indeterminate = false; }
        else { parent.selected = false; parent.indeterminate = true; }

        const cb = document.getElementById(`cat_${parent.id}`);
        if (cb) { cb.checked = parent.selected; cb.indeterminate = parent.indeterminate; }
        updateParentState(parent.parentId);
    }

    function applySearch(filterText) {
        const lowerFilter = filterText.toLowerCase();
        Object.values(categoryMap).forEach(cat => cat.visible = cat.name.toLowerCase().includes(lowerFilter));
        
        function ensureParentVisibility(node) {
            let childIsVisible = false;
            node.children.forEach(child => { if (ensureParentVisibility(child)) childIsVisible = true; });
            if (childIsVisible) node.visible = true;
            return node.visible;
        }
        categoryTree.forEach(ensureParentVisibility);
        renderCategories();
    }

    function updateCategoryCount() {
        if (!categoryCount) return;
        const total = Object.keys(categoryMap).length;
        const checkedCount = Object.values(categoryMap).filter(c => c.selected).length;
        categoryCount.textContent = `${checkedCount} Seleccionadas`;
    }

    if (categorySearch) categorySearch.addEventListener('input', (e) => applySearch(e.target.value));
    if (btnSelectAll) btnSelectAll.addEventListener('click', () => {
        categoryTree.forEach(root => handleCheckboxChange(root.id, true));
    });
    if (btnSelectNone) btnSelectNone.addEventListener('click', () => {
        categoryTree.forEach(root => handleCheckboxChange(root.id, false));
    });

    fetchCategories();

    // --- DRAG AND DROP FILE LOGIC ---
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        if (dropArea) dropArea.addEventListener(eventName, preventDefaults, false);
    });
    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
        if (dropArea) dropArea.addEventListener(eventName, () => dropArea.classList.add('dragover'), false);
    });
    ['dragleave', 'drop'].forEach(eventName => {
        if (dropArea) dropArea.addEventListener(eventName, () => dropArea.classList.remove('dragover'), false);
    });

    if (dropArea) {
        dropArea.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
        dropArea.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
            fileInput.value = '';
        });
    }

    function handleFiles(files) {
        let validFiles = [];
        Array.from(files).forEach(file => {
            if (file.name.endsWith('.xlsx')) {
                if (!selectedFiles.find(f => f.name === file.name)) validFiles.push(file);
            } else {
                showAlert(`"${file.name}" ignorado, debe ser .xlsx`, false);
            }
        });

        if (validFiles.length > 0) {
            selectedFiles = selectedFiles.concat(validFiles);
            hideAlert();
            renderFileList();
        }
    }

    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        renderFileList();
    }

    function renderFileList() {
        if (!fileListContainer) return;
        fileListContainer.innerHTML = '';
        selectedFiles.forEach((file, index) => {
            fileListContainer.innerHTML += `
                <div class="file-chip">
                    <span><i class="fas fa-file-excel"></i> ${file.name}</span>
                    <i class="fas fa-times remove-btn" onclick="removeFile(${index})"></i>
                </div>
            `;
        });
    }

    // --- FORM SUBMISSION ---
    function showAlert(msg, isSuccess) {
        if (alertBox) {
            alertBox.textContent = msg;
            alertBox.style.display = 'block';
            alertBox.className = `alert alert-${isSuccess ? 'success' : 'danger'}`;
            alertBox.style.backgroundColor = isSuccess ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
            alertBox.style.color = isSuccess ? '#10b981' : '#ef4444';
        }
    }
    function hideAlert() { if (alertBox) alertBox.style.display = 'none'; }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            
            submitBtn.disabled = true;
            btnText.innerHTML = '<div class="loader" style="width:20px; height:20px; border-width:2px;"></div> Procesando...';
            
            const excludedSection = document.getElementById('excludedSection');
            if (excludedSection) excludedSection.style.display = 'none';

            const formData = new FormData();
            formData.append('pedido_days', document.getElementById('pedidoDays').value);
            formData.append('num_rows', document.getElementById('numRows').value);
            
            const umbral = document.getElementById('umbralRotacion') ? document.getElementById('umbralRotacion').value : '0.0';
            formData.append('umbral_rotacion', umbral);
            formData.append('preview_mode', 'true'); // We want to preview the exclusions first
            
            const isGeneric = document.getElementById('isGeneric') ? document.getElementById('isGeneric').checked : false;
            formData.append('is_generic', isGeneric ? 'true' : 'false');

            selectedFiles.forEach(file => formData.append('subtraction_files', file));

            const selectedCategoryNames = Object.values(categoryMap)
                .filter(c => c.selected).map(c => c.name);

            if (selectedCategoryNames.length === 0) {
                showAlert("Debe seleccionar al menos una familia.", false);
                submitBtn.disabled = false;
                btnText.innerHTML = 'Generar Pedido Maestro';
                return;
            }

            formData.append('categories', selectedCategoryNames.join(','));

            try {
                const response = await fetch('/api/pedidos/generate', { method: 'POST', body: formData });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Error al calcular el reporte");
                }

                // Parse the JSON response since preview_mode is true
                const data = await response.json();
                
                if (data.excluidos && data.excluidos.length > 0) {
                    // Show the excluded section
                    const tbody = document.getElementById('excludedTableBody');
                    const countSpan = document.getElementById('excludedCount');
                    
                    if (tbody && countSpan && excludedSection) {
                        tbody.innerHTML = '';
                        countSpan.textContent = `${data.excluidos.length} Productos`;
                        
                        data.excluidos.forEach(item => {
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); color: var(--text-primary);">
                                    <input type="checkbox" class="exclude-checkbox" value="${item.BARRA}">
                                </td>
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); font-family: monospace; color: var(--text-primary);">${item.BARRA}</td>
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; color: var(--text-primary);">${item.Descrip || ''}</td>
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); color: var(--danger); font-weight: bold;">${item.RotacionMensual.toFixed(2)}</td>
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); color: var(--text-primary);">${item.Existen || 0}</td>
                                <td style="padding: 0.5rem; border-bottom: 1px solid var(--border-color); color: var(--text-primary);">${item.CANTIDAD}</td>
                            `;
                            tbody.appendChild(tr);
                        });
                        
                        excludedSection.style.display = 'block';
                        showAlert("Se encontraron productos con rotación inferior al umbral. Por favor, revise la lista de exclusiones abajo antes de generar el archivo definitivo.", false);
                        setTimeout(() => {
                            excludedSection.scrollIntoView({ behavior: 'smooth', block: 'end' });
                        }, 100);
                    }
                } else {
                    // No exclusions, generate immediately
                    formData.set('preview_mode', 'false'); // Set to false to get the blob
                    await generateFinalExcel(formData);
                }

            } catch (error) {
                showAlert(error.message, false);
            } finally {
                submitBtn.disabled = false;
                btnText.innerHTML = '<i class="fas fa-file-excel"></i> Generar Pedido Maestro';
            }
        });
    }

    // Logic for Select All in exclusions table
    const selectAllExcluded = document.getElementById('selectAllExcluded');
    if (selectAllExcluded) {
        selectAllExcluded.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.exclude-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        });
    }

    // Logic for Final Generate
    const generateFinalBtn = document.getElementById('generateFinalBtn');
    if (generateFinalBtn) {
        generateFinalBtn.addEventListener('click', async () => {
            hideAlert();
            generateFinalBtn.disabled = true;
            const originalHtml = generateFinalBtn.innerHTML;
            generateFinalBtn.innerHTML = '<div class="loader" style="width:20px; height:20px; border-width:2px; border-color: white transparent transparent transparent;"></div> Generando...';
            
            const formData = new FormData();
            formData.append('pedido_days', document.getElementById('pedidoDays').value);
            formData.append('num_rows', document.getElementById('numRows').value);
            const umbral = document.getElementById('umbralRotacion') ? document.getElementById('umbralRotacion').value : '0.0';
            formData.append('umbral_rotacion', umbral);
            formData.append('preview_mode', 'false'); // Force final download
            
            const isGeneric = document.getElementById('isGeneric') ? document.getElementById('isGeneric').checked : false;
            formData.append('is_generic', isGeneric ? 'true' : 'false');
            
            selectedFiles.forEach(file => formData.append('subtraction_files', file));
            
            const selectedCategoryNames = Object.values(categoryMap)
                .filter(c => c.selected).map(c => c.name);
            formData.append('categories', selectedCategoryNames.join(','));

            // Gather forced includes
            const checkedBoxes = document.querySelectorAll('.exclude-checkbox:checked');
            const forcedBarcodes = Array.from(checkedBoxes).map(cb => cb.value);
            if (forcedBarcodes.length > 0) {
                formData.append('forced_includes', forcedBarcodes.join(','));
            }

            try {
                await generateFinalExcel(formData);
                document.getElementById('excludedSection').style.display = 'none';
            } catch (error) {
                showAlert(error.message, false);
            } finally {
                generateFinalBtn.disabled = false;
                generateFinalBtn.innerHTML = originalHtml;
            }
        });
    }

    async function generateFinalExcel(formData) {
        const response = await fetch('/api/pedidos/generate', { method: 'POST', body: formData });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "Error al generar el archivo Excel");
        }

        const blob = await response.blob();
        let filename = "Pedido.xlsx";
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const match = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (match != null && match[1]) filename = match[1].replace(/['"]/g, '');
        }

        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();

        showAlert("Matríz de Pedidos generada y descargada exitosamente.", true);
        selectedFiles = [];
        renderFileList();
    }
});
