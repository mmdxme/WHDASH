// js/app.js

// -- State Management --
const State = {
    activeView: 'dashboard',
    activeCompany: 'ALL', // 'ALL', 'SDAD', 'AFRA', 'Carmania'
    isDark: true,
    gridData: [], // Current filtered data for grid
    gridSort: { field: '', asc: true },
    activeChartInstances: {}
};

// -- DOM Elements --
const DOM = {
    loginScreen: document.getElementById('login-screen'),
    mainDashboard: document.getElementById('main-dashboard'),
    loginForm: document.getElementById('login-form'),
    themeToggle: document.getElementById('theme-toggle'),
    sidebar: document.getElementById('sidebar'),
    mobileSidebar: document.getElementById('mobile-sidebar'),
    mobileMenuBtn: document.getElementById('mobile-menu-btn'),
    mobileOverlay: document.getElementById('mobile-sidebar-overlay'),
    companySelectorContainer: document.getElementById('company-selector-container'),
    viewContainer: document.getElementById('view-container'),
    globalSearch: document.getElementById('global-search'),
    searchResults: document.getElementById('searchResults'), // To be implemented later if needed
    
    // Modal
    partModal: document.getElementById('part-modal'),
    modalPartNumber: document.getElementById('modal-part-number'),
    modalCriticalBadge: document.getElementById('modal-critical-badge'),
    modalContentContainer: document.getElementById('modal-content-container'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    modalExportBtn: document.getElementById('modal-export-btn'),
};

// -- Chart Helpers --
Chart.defaults.color = State.isDark ? '#94a3b8' : '#64748b';
Chart.defaults.font.family = "'Inter', sans-serif";

function determineChartColors() {
    return State.isDark ? {
        text: '#cbd5e1',
        grid: '#334155',
        brand: '#3b82f6',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444'
    } : {
        text: '#475569',
        grid: '#e2e8f0',
        brand: '#2563eb',
        success: '#16a34a',
        warning: '#d97706',
        danger: '#dc2626'
    };
}

// -- Core Logic --

function initApp() {
    // Check theme
    if (localStorage.getItem('theme') === 'light') {
        document.documentElement.classList.remove('dark');
        State.isDark = false;
    }
    Chart.defaults.color = determineChartColors().text;

    attachEventListeners();
}

function attachEventListeners() {
    // Login
    DOM.loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        DOM.loginScreen.classList.add('hidden');
        DOM.mainDashboard.classList.remove('hidden');
        renderAppStructure();
        renderActiveView();
    });

    // Theme Toggle
    DOM.themeToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        State.isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('theme', State.isDark ? 'dark' : 'light');
        Chart.defaults.color = determineChartColors().text;
        
        // Re-render charts with new theme colors
        if (State.activeView === 'dashboard') {
            renderDashboardCharts();
        }
    });

    // Mobile Menu
    DOM.mobileMenuBtn.addEventListener('click', () => {
        DOM.mobileSidebar.classList.remove('-translate-x-full');
        DOM.mobileOverlay.classList.remove('hidden');
    });

    DOM.mobileOverlay.addEventListener('click', () => {
        DOM.mobileSidebar.classList.add('-translate-x-full');
        DOM.mobileOverlay.classList.add('hidden');
    });

    // Global Event Delegation for dynamic elements
    document.addEventListener('click', (e) => {
        
        // Navigation clicks
        const navTarget = e.target.closest('[id^="nav-"]');
        if (navTarget) {
            e.preventDefault();
            const view = navTarget.id.replace('nav-', '');
            if (State.activeView !== view) {
                State.activeView = view;
                renderAppStructure(); // Update active states
                renderActiveView();
            }
        }

        // Company selector menu toggle
        if (e.target.closest('#company-menu-button')) {
            const dropdown = document.getElementById('company-dropdown-options').parentElement;
            dropdown.classList.toggle('hidden');
        } else if (!e.target.closest('#company-selector-container')) {
            const dropdown = document.getElementById('company-dropdown-options');
            if (dropdown && dropdown.parentElement) {
                dropdown.parentElement.classList.add('hidden');
            }
        }

        // Company selection
        const companyOption = e.target.closest('[data-company]');
        if (companyOption) {
            e.preventDefault();
            State.activeCompany = companyOption.dataset.company;
            document.getElementById('company-dropdown-options').parentElement.classList.add('hidden');
            renderAppStructure();
            renderActiveView();
        }

        // Logout
        if (e.target.closest('#logout-btn')) {
            DOM.mainDashboard.classList.add('hidden');
            DOM.loginScreen.classList.remove('hidden');
        }

        // Part Link clicks (Opens Modal)
        if (e.target.closest('.part-link')) {
            const partNum = e.target.closest('.part-link').dataset.part;
            openPartModal(partNum);
        }
        
        // Modal Close (Backdrop)
        if (e.target.id === 'part-modal-overlay') {
            closePartModal();
        }

        // Export Excel Button
        if (e.target.closest('#btn-export-excel')) {
            exportToExcel();
        }
    });

    // Global Search (Simple local filter simulation)
    DOM.globalSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (query.length > 2) {
            // Find parts matching
            const results = window.APP_DATA.catalog.filter(p => 
                p.partNumber.toLowerCase().includes(query) || 
                p.description.toLowerCase().includes(query)
            ).slice(0, 5);
            
            // Build dropdown
            let html = '';
            if (results.length > 0) {
                html = results.map(r => `
                    <div class="px-4 py-3 hover:bg-gray-100 dark:hover:bg-slate-700 cursor-pointer border-b border-gray-100 dark:border-slate-700 last:border-0 part-link" data-part="${r.partNumber}">
                        <div class="flex items-center justify-between">
                            <span class="font-medium text-brand-600 dark:text-brand-400">${r.partNumber}</span>
                            <span class="text-xs text-gray-500">${r.brand}</span>
                        </div>
                        <div class="text-sm text-gray-600 dark:text-gray-300 mt-1">${r.description}</div>
                    </div>
                `).join('');
            } else {
                html = `<div class="p-4 text-sm text-gray-500 text-center">No parts found</div>`;
            }
            
            let dropdown = document.getElementById('search-results');
            dropdown.innerHTML = html;
            dropdown.classList.remove('hidden');
        } else {
            document.getElementById('search-results').classList.add('hidden');
        }
    });

    // Close search results when clicking away
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.group') && document.getElementById('search-results')) {
            document.getElementById('search-results').classList.add('hidden');
        }
    });

    // Modal Close Button
    DOM.closeModalBtn.addEventListener('click', closePartModal);
}

function renderAppStructure() {
    const sidebarHtml = window.UI.renderSidebar(State.activeView);
    DOM.sidebar.innerHTML = sidebarHtml;
    DOM.mobileSidebar.innerHTML = sidebarHtml;
    DOM.companySelectorContainer.innerHTML = window.UI.renderCompanySelector(State.activeCompany);
}

function renderActiveView() {
    // Clear previous charts to prevent memory leaks
    Object.keys(State.activeChartInstances).forEach(id => {
        if (State.activeChartInstances[id]) {
            State.activeChartInstances[id].destroy();
        }
    });
    State.activeChartInstances = {};

    switch(State.activeView) {
        case 'dashboard':
            DOM.viewContainer.innerHTML = window.UI.renderDashboardOverview(State.activeCompany);
            setTimeout(renderDashboardCharts, 50); // Small delay to ensure DOM is ready
            break;
        case 'inventory':
            DOM.viewContainer.innerHTML = window.UI.renderInventoryGridPage();
            initInventoryGrid();
            break;
        case 'import':
            DOM.viewContainer.innerHTML = window.UI.renderImportPage();
            break;
        default:
            DOM.viewContainer.innerHTML = `<div class="p-8 text-center text-gray-500">View implementation pending...</div>`;
    }
}

// -- Dashboard Charts Logic --

function renderDashboardCharts() {
    const colors = determineChartColors();
    const items = window.DataService.getEnrichedInventory(State.activeCompany);
    
    // 1. Distribution Chart (Donut)
    const distCtx = document.getElementById('chart-distribution');
    if (distCtx) {
        let data = {};
        if (State.activeCompany === 'ALL') {
            // Distribute by company
            data = items.reduce((acc, curr) => {
                acc[curr.company] = (acc[curr.company] || 0) + curr.value;
                return acc;
            }, {});
        } else {
            // Distribute by category
            data = items.reduce((acc, curr) => {
                acc[curr.category] = (acc[curr.category] || 0) + curr.value;
                return acc;
            }, {});
        }

        State.activeChartInstances['dist'] = new Chart(distCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899', '#14b8a6'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: colors.text } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) { label += ': '; }
                                if (context.parsed !== null) {
                                    label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(context.parsed);
                                }
                                return label;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // 2. Trend Line Chart
    const trendCtx = document.getElementById('chart-trend');
    if (trendCtx) {
        // Just mock some arbitrary months and data lines representing top 5 parts movements
        State.activeChartInstances['trend'] = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [
                    { label: 'Outflow (Sales/Issues)', data: [65, 59, 80, 81, 56, 55, 40], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', tension: 0.4, fill: true },
                    { label: 'Inflow (Receipts)', data: [28, 48, 40, 19, 86, 27, 90], borderColor: '#22c55e', backgroundColor: 'transparent', tension: 0.4 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: colors.text } } },
                scales: {
                    x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                    y: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                },
                interaction: { mode: 'index', intersect: false }
            }
        });
    }

    // 3. Stacked Bar Chart (Cross Company Comparison - only when activeCompany === 'ALL')
    const compCtx = document.getElementById('chart-comparison');
    if (compCtx && State.activeCompany === 'ALL') {
        // Pick top 10 most valuable parts
        const highestValPartsMs = items.sort((a,b) => b.value - a.value);
        const uniqueIds = [...new Set(highestValPartsMs.map(i => i.partId))].slice(0, 10);
        
        const labels = uniqueIds.map(id => window.DataService.getPartById(id).partNumber);
        
        const sdadData = uniqueIds.map(id => { const i = items.find(x => x.partId === id && x.company === 'SDAD'); return i ? i.quantity : 0; });
        const afraData = uniqueIds.map(id => { const i = items.find(x => x.partId === id && x.company === 'AFRA'); return i ? i.quantity : 0; });
        const carmData = uniqueIds.map(id => { const i = items.find(x => x.partId === id && x.company === 'Carmania'); return i ? i.quantity : 0; });

        State.activeChartInstances['comp'] = new Chart(compCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: 'SDAD', data: sdadData, backgroundColor: '#3b82f6' },
                    { label: 'AFRA', data: afraData, backgroundColor: '#10b981' },
                    { label: 'Carmania', data: carmData, backgroundColor: '#8b5cf6' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: colors.text } }, tooltip: { mode: 'index', intersect: false } },
                scales: {
                    x: { stacked: true, grid: { display: false }, ticks: { color: colors.text } },
                    y: { stacked: true, grid: { color: colors.grid }, ticks: { color: colors.text } }
                }
            }
        });
    }
}

// -- Inventory Grid Logic --

function initInventoryGrid() {
    State.gridData = window.DataService.getEnrichedInventory(State.activeCompany);
    
    // Set initial filter values based on global state
    document.getElementById('filter-company').value = State.activeCompany;
    
    renderGridTable();
    
    // Attach Filter Events
    ['filter-company', 'filter-category', 'filter-status'].forEach(id => {
        document.getElementById(id).addEventListener('change', window.GridController.applyFilters);
    });
}

window.GridController = {
    applyFilters: () => {
        const cFilter = document.getElementById('filter-company').value;
        const catFilter = document.getElementById('filter-category').value;
        const statFilter = document.getElementById('filter-status').value;
        
        // Temporarily override global if they filter in grid? Actually, let's just filter the local grid data
        let filtered = window.DataService.getEnrichedInventory(cFilter);
        
        if (catFilter !== 'ALL') filtered = filtered.filter(i => i.category === catFilter);
        if (statFilter !== 'ALL') filtered = filtered.filter(i => i.status === statFilter);
        
        State.gridData = filtered;
        
        // Re-apply sort
        if (State.gridSort.field) {
            window.GridController.sort(State.gridSort.field, false); 
        } else {
            renderGridTable();
        }
    },
    
    sort: (field, toggleDir = true) => {
        if (toggleDir) {
            if (State.gridSort.field === field) {
                State.gridSort.asc = !State.gridSort.asc;
            } else {
                State.gridSort.field = field;
                State.gridSort.asc = true;
            }
        }
        
        const asc = State.gridSort.asc ? 1 : -1;
        
        State.gridData.sort((a, b) => {
            let valA = a[field];
            let valB = b[field];
            
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
            
            if (valA < valB) return -1 * asc;
            if (valA > valB) return 1 * asc;
            return 0;
        });
        
        renderGridTable();
    }
};

function renderGridTable() {
    document.getElementById('grid-container').innerHTML = window.UI.renderInventoryGridTable(State.gridData);
}

function exportToExcel() {
    // Check if XLSX library is loaded
    if (typeof XLSX === "undefined") {
        alert("Excel export library is still loading. Please try again in a moment.");
        return;
    }
    
    const ws_data = State.gridData.map(i => ({
        "Part Number": i.partNumber,
        "Description": i.description,
        "Subsidiary": i.company,
        "Zone Location": i.zone,
        "Brand": i.brand,
        "Type": i.brandType,
        "Category": i.category,
        "Available Quantity": i.quantity,
        "Reorder Point": i.reorderPoint,
        "Status": i.status,
        "Unit Value ($)": i.costPrice
    }));
    
    const ws = XLSX.utils.json_to_sheet(ws_data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Inventory");
    
    XLSX.writeFile(wb, `MMD_DASH_Inventory_${new Date().toISOString().split('T')[0]}.xlsx`);
}

// -- Modal Logic --
let modalChartInstance = null;

function openPartModal(partNumber) {
    const part = window.DataService.getPartByNumber(partNumber);
    if (!part) return;
    
    const inventory = window.DataService.getInventoryByPart(part.id);
    const movements = window.DataService.getMovements(part.id);
    
    // Total quantity across all subsidiaries
    const totalQty = inventory.reduce((s, i) => s + i.quantity, 0);
    const isCriticalGlobal = totalQty < part.reorderPoint;

    DOM.modalPartNumber.textContent = part.partNumber;
    
    if (isCriticalGlobal) {
        DOM.modalCriticalBadge.classList.remove('hidden');
    } else {
        DOM.modalCriticalBadge.classList.add('hidden');
    }

    DOM.modalContentContainer.innerHTML = window.UI.renderPartModalDetails(part, inventory, movements);
    DOM.partModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling

    // Render Modal Chart
    setTimeout(() => {
        const ctx = document.getElementById('modal-movement-chart');
        if (ctx) {
            if (modalChartInstance) modalChartInstance.destroy();
            
            const labels = movements.map(m => `${m.month} ${m.year.toString().slice(2)}`);
            const inData = movements.map(m => m.in);
            const outData = movements.map(m => m.out);
            const colors = determineChartColors();

            modalChartInstance = new Chart(ctx, {
                type: 'bar', // Mixed chart
                data: {
                    labels: labels.reverse(),
                    datasets: [
                        { type: 'line', label: 'Inward', data: inData.reverse(), borderColor: '#22c55e', backgroundColor: 'transparent', tension: 0.3, yAxisID: 'y' },
                        { type: 'bar', label: 'Outward', data: outData.reverse(), backgroundColor: 'rgba(239, 68, 68, 0.7)', yAxisID: 'y' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: colors.text } } },
                    scales: {
                        x: { grid: { display: false }, ticks: { color: colors.text } },
                        y: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                    }
                }
            });
        }
    }, 50);

    // Bind export button for this specific part
    DOM.modalExportBtn.onclick = () => {
        if (typeof XLSX === "undefined") return;
        
        let reportDetails = [
            ["Part Number", part.partNumber],
            ["Description", part.description],
            ["Category", part.category],
            ["Brand", `${part.brand} (${part.brandType})`],
            ["Total Value", `$${inventory.reduce((s,i) => s + i.value, 0)}`],
            [],
            ["Location", "Zone", "Available Stock", "Status"]
        ];
        
        inventory.forEach(i => {
            const isCrit = i.quantity < part.reorderPoint;
            reportDetails.push([i.company, i.zone, i.quantity, isCrit ? 'Critical' : 'Healthy']);
        });

        const ws = XLSX.utils.aoa_to_sheet(reportDetails);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, part.partNumber);
        
        XLSX.writeFile(wb, `${part.partNumber}_Report.xlsx`);
    };
}

function closePartModal() {
    DOM.partModal.classList.add('hidden');
    document.body.style.overflow = '';
    if (modalChartInstance) {
        modalChartInstance.destroy();
        modalChartInstance = null;
    }
}

// Bootstrap
document.addEventListener('DOMContentLoaded', initApp);
