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

            const formData = new FormData();
            formData.append('pedido_days', document.getElementById('pedidoDays').value);
            formData.append('num_rows', document.getElementById('numRows').value);

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
            } catch (error) {
                showAlert(error.message, false);
            } finally {
                submitBtn.disabled = false;
                btnText.innerHTML = '<i class="fas fa-file-excel"></i> Generar Pedido Maestro';
            }
        });
    }
});
