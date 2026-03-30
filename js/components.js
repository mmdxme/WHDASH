// js/components.js

const UI = {
    renderSidebarItem: (icon, label, isActive = false, id = '') => `
        <a href="#" id="${id}" class="flex items-center gap-3 px-4 py-3 mx-2 rounded-lg text-sm font-medium transition-colors ${
            isActive ? 'bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400' 
                     : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white'
        }">
            <i class="${icon} ${isActive ? 'text-brand-600 dark:text-brand-400' : 'text-gray-400 group-hover:text-gray-500'} text-lg w-5 text-center"></i>
            ${label}
        </a>
    `,
    
    renderSidebar: (activeView) => `
        <div class="p-6">
            <div class="flex items-center gap-3 text-brand-600 dark:text-brand-500">
                <i class="fa-solid fa-boxes-stacked text-2xl"></i>
                <span class="text-xl font-bold tracking-tight text-gray-900 dark:text-white">MMD DASH</span>
            </div>
        </div>
        
        <nav class="flex-1 overflow-y-auto py-4 space-y-1">
            <div class="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-4">Main Menu</div>
            ${UI.renderSidebarItem('fa-solid fa-chart-line', 'Dashboard', activeView === 'dashboard', 'nav-dashboard')}
            ${UI.renderSidebarItem('fa-solid fa-table', 'Inventory Grid', activeView === 'inventory', 'nav-inventory')}
            
            <div class="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 mt-8">Operations</div>
            ${UI.renderSidebarItem('fa-solid fa-file-import', 'Import Data', activeView === 'import', 'nav-import')}
            ${UI.renderSidebarItem('fa-brands fa-wpforms', 'Purchase Orders', activeView === 'po', 'nav-po')}
            ${UI.renderSidebarItem('fa-solid fa-truck-fast', 'Movements', activeView === 'movements', 'nav-movements')}
        </nav>
        
        <div class="p-4 border-t border-gray-200 dark:border-slate-700">
            <button id="logout-btn" class="flex items-center gap-3 w-full px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors">
                <i class="fa-solid fa-arrow-right-from-bracket"></i>
                Sign out
            </button>
        </div>
    `,

    renderCompanySelector: (activeCompany) => `
        <div class="relative inline-block text-left group">
            <button type="button" class="inline-flex justify-center w-full rounded-md border border-gray-300 dark:border-slate-600 shadow-sm px-4 py-2 bg-white dark:bg-slate-800 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700 focus:outline-none transition-colors" id="company-menu-button">
                ${activeCompany === 'ALL' ? 'Holding Company (All)' : activeCompany}
                <i class="fa-solid fa-chevron-down ml-2 -mr-1 h-5 w-5 text-gray-400 pt-0.5"></i>
            </button>

            <!-- Dropdown panel -->
            <div class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-slate-800 ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 dark:divide-slate-700 hidden group-hover:block z-50 transition-opacity">
                <div class="py-1" role="menu" id="company-dropdown-options">
                    <a href="#" class="group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${activeCompany === 'ALL' ? 'font-bold bg-gray-50 dark:bg-slate-700' : ''}" data-company="ALL">
                        <i class="fa-solid fa-globe mr-3 text-gray-400 group-hover:text-gray-500"></i>
                        Holding Company (All)
                    </a>
                    <a href="#" class="group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${activeCompany === 'SDAD' ? 'font-bold bg-gray-50 dark:bg-slate-700' : ''}" data-company="SDAD">
                        <i class="fa-solid fa-building mr-3 text-brand-500"></i>
                        SDAD
                    </a>
                    <a href="#" class="group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${activeCompany === 'AFRA' ? 'font-bold bg-gray-50 dark:bg-slate-700' : ''}" data-company="AFRA">
                        <i class="fa-solid fa-building mr-3 text-brand-500"></i>
                        AFRA
                    </a>
                    <a href="#" class="group flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors ${activeCompany === 'Carmania' ? 'font-bold bg-gray-50 dark:bg-slate-700' : ''}" data-company="Carmania">
                        <i class="fa-solid fa-building mr-3 text-brand-500"></i>
                        Carmania
                    </a>
                </div>
            </div>
        </div>
    `,

    renderDashboardOverview: (activeCompany) => {
        // Compute Metrics
        const inventoryItems = DataService.getEnrichedInventory(activeCompany);
        
        let totalValue = 0;
        let totalParts = 0;
        let criticalCount = 0;
        
        inventoryItems.forEach(item => {
            totalValue += item.value;
            totalParts += item.quantity;
            if (item.status === 'Critical') criticalCount++;
        });

        return `
            <!-- KPI Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 fade-in">
                
                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col items-start relative overflow-hidden group hover:shadow-md transition-shadow">
                    <div class="absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-green-50 to-transparent dark:from-green-900/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div class="p-3 rounded-lg bg-green-100 text-green-600 dark:bg-green-500/20 dark:text-green-400 mb-4">
                        <i class="fa-solid fa-dollar-sign text-xl"></i>
                    </div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Inventory Value</p>
                    <h4 class="text-3xl font-bold text-gray-900 dark:text-white">
                        $${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </h4>
                </div>

                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 flex flex-col items-start relative overflow-hidden group hover:shadow-md transition-shadow">
                    <div class="absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-brand-50 to-transparent dark:from-brand-900/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div class="p-3 rounded-lg bg-brand-100 text-brand-600 dark:bg-brand-500/20 dark:text-brand-400 mb-4">
                        <i class="fa-solid fa-cubes text-xl"></i>
                    </div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Parts in Stock</p>
                    <h4 class="text-3xl font-bold text-gray-900 dark:text-white">
                        ${totalParts.toLocaleString()}
                    </h4>
                </div>

                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-red-200 dark:border-red-900/50 p-6 flex flex-col items-start relative overflow-hidden group hover:shadow-md transition-shadow">
                    <div class="absolute right-0 top-0 h-full w-24 bg-gradient-to-l from-red-50 to-transparent dark:from-red-900/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div class="p-3 rounded-lg bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400 mb-4 animate-pulse">
                        <i class="fa-solid fa-triangle-exclamation text-xl"></i>
                    </div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Critical Low Stock Alerts</p>
                    <h4 class="text-3xl font-bold text-red-600 dark:text-red-400">
                        ${criticalCount} Items
                    </h4>
                </div>

            </div>

            <!-- Charts Section -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 fade-in" style="animation-delay: 0.1s;">
                <!-- Chart 1: Distribution -->
                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Inventory Value Distribution</h3>
                    <div class="relative h-64 w-full flex justify-center items-center">
                        <canvas id="chart-distribution"></canvas>
                    </div>
                </div>

                <!-- Chart 2: Movement Trend -->
                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Stock Movement Trend (Top 5 Parts)</h3>
                    <div class="relative h-64 w-full">
                        <canvas id="chart-trend"></canvas>
                    </div>
                </div>
            </div>

            <!-- Chart 3: Cross-Company Comparison (Full Width) -->
            ${activeCompany === 'ALL' ? `
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 mb-8 fade-in" style="animation-delay: 0.2s;">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cross-Company Stock Comparison (High-Value Parts)</h3>
                <div class="relative h-80 w-full">
                    <canvas id="chart-comparison"></canvas>
                </div>
            </div>
            ` : ''}

            <!-- Low Stock Mini Table -->
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-6 fade-in" style="animation-delay: 0.3s;">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Low Stock Alerts</h3>
                    <button id="view-all-critical-btn" class="text-sm font-medium text-brand-600 hover:text-brand-500 dark:text-brand-400">View All</button>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
                        <thead>
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Part Number</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Description</th>
                                <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Location</th>
                                <th class="px-6 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Stock</th>
                                <th class="px-6 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Action</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 dark:divide-slate-700">
                            ${inventoryItems.filter(i => i.status === 'Critical').slice(0, 5).map(item => `
                                <tr class="hover:bg-gray-50 dark:hover:bg-slate-750 transition-colors">
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <button class="font-medium text-brand-600 dark:text-brand-400 hover:underline part-link" data-part="${item.partNumber}">
                                            ${item.partNumber}
                                        </button>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-300">
                                        ${item.description}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-300">
                                            ${item.company} | ${item.zone}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-right">
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800/50">
                                            ${item.quantity} / ${item.reorderPoint}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-center text-sm">
                                        <button class="text-brand-600 hover:text-brand-900 dark:text-brand-400 dark:hover:text-brand-300 bg-brand-50 w-full hover:bg-brand-100 dark:bg-brand-900/20 dark:hover:bg-brand-900/40 px-3 py-1 rounded transition-colors">
                                            Reorder
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    renderInventoryGridFilters: () => `
        <div class="mb-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
                <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Company</label>
                <select id="filter-company" class="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm text-gray-900 dark:text-gray-100">
                    <option value="ALL">All Subsidiaries</option>
                    <option value="SDAD">SDAD</option>
                    <option value="AFRA">AFRA</option>
                    <option value="Carmania">Carmania</option>
                </select>
            </div>
            <div>
                <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Category</label>
                <select id="filter-category" class="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm text-gray-900 dark:text-gray-100">
                    <option value="ALL">All Categories</option>
                    ${window.CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('')}
                </select>
            </div>
            <div>
                <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</label>
                <select id="filter-status" class="mt-1 block w-full pl-3 pr-10 py-2 border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 rounded-md shadow-sm focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm text-gray-900 dark:text-gray-100">
                    <option value="ALL">All Statuses</option>
                    <option value="Critical">Critical</option>
                    <option value="Warning">Warning</option>
                    <option value="Healthy">Healthy</option>
                </select>
            </div>
            <div class="flex items-end">
                <button id="btn-export-excel" class="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-slate-600 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors dark:text-gray-200 h-[38px]">
                    <i class="fa-solid fa-file-excel text-green-600 dark:text-green-500 mr-2"></i>
                    Export to Excel
                </button>
            </div>
        </div>
    `,

    renderInventoryGridRow: (item) => {
        let statusClass = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800';
        if (item.status === 'Critical') statusClass = 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800';
        if (item.status === 'Warning') statusClass = 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200 dark:border-amber-800';

        return `
            <tr class="hover:bg-gray-50 dark:hover:bg-slate-750 transition-colors cursor-pointer group part-link" data-part="${item.partNumber}">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="ml-4">
                            <div class="text-sm font-medium text-brand-600 dark:text-brand-400 group-hover:underline">
                                ${item.partNumber}
                            </div>
                            <div class="text-xs text-gray-500 dark:text-gray-400">
                                ${item.description}
                            </div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-300">
                        ${item.company}
                    </span>
                    <div class="text-xs text-gray-500 mt-1 dark:text-gray-400">${item.zone}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    <div>${item.brand}</div>
                    <div class="text-xs opacity-75">${item.brandType}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                    ${item.category}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right">
                    <div class="text-sm font-bold text-gray-900 dark:text-gray-100">${item.quantity}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">ROP: ${item.reorderPoint}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusClass}">
                        ${item.status}
                    </span>
                </td>
            </tr>
        `;
    },

    renderInventoryGridTable: (items) => `
        <div class="overflow-x-auto bg-white dark:bg-slate-800 rounded-xl shadow border border-gray-200 dark:border-slate-700">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-700" id="data-table">
                <thead class="bg-gray-50 dark:bg-slate-850">
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('partNumber')">
                            Part Number <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('company')">
                            Subsidiary <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('brand')">
                            Brand <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('category')">
                            Category <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                        <th scope="col" class="px-6 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('quantity')">
                            Stock <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                        <th scope="col" class="px-6 py-3 text-center text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-700 transition" onclick="GridController.sort('status')">
                            Status <i class="fa-solid fa-sort ml-1"></i>
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-700" id="data-table-body">
                    ${items.map(UI.renderInventoryGridRow).join('')}
                </tbody>
            </table>
            
            ${items.length === 0 ? `
                <div class="py-12 text-center">
                    <i class="fa-solid fa-box-open text-4xl text-gray-300 dark:text-slate-600 mb-3"></i>
                    <p class="text-gray-500 dark:text-gray-400 text-sm">No inventory records found matching your criteria.</p>
                </div>
            ` : ''}
            
            <div class="px-6 py-4 border-t border-gray-200 dark:border-slate-700 flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <span>Showing ${items.length} records</span>
                <!-- In a real app, pagination controls go here -->
                <div class="flex gap-2">
                    <button class="px-3 py-1 border border-gray-300 dark:border-slate-600 rounded bg-gray-50 dark:bg-slate-700 opacity-50 cursor-not-allowed">Previous</button>
                    <button class="px-3 py-1 border border-gray-300 dark:border-slate-600 rounded bg-gray-50 dark:bg-slate-700 opacity-50 cursor-not-allowed">Next</button>
                </div>
            </div>
        </div>
    `,

    renderInventoryGridPage: () => `
        <div class="fade-in">
            <div class="mb-6 flex items-center justify-between">
                <div>
                    <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Master Inventory Grid</h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Advanced multi-column filtering and export capabilities</p>
                </div>
            </div>
            
            ${UI.renderInventoryGridFilters()}
            
            <div id="grid-container">
                <!-- Data populated by JS -->
            </div>
        </div>
    `,

    renderImportPage: () => `
        <div class="fade-in max-w-4xl mx-auto mt-8">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Import Inventory Data</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-8">Upload CSV or Excel files to update quantities and create new part numbers in bulk.</p>
            
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-200 dark:border-slate-700 p-8 text-center border-dashed border-2">
                <div class="w-16 h-16 mx-auto bg-brand-50 dark:bg-brand-500/10 rounded-full flex items-center justify-center mb-4">
                    <i class="fa-solid fa-cloud-arrow-up text-2xl text-brand-600 dark:text-brand-400"></i>
                </div>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">Upload a file</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">XLSX, CSV up to 10MB</p>
                <button class="inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition-colors">
                    Browse Files
                </button>
            </div>
            
            <div class="mt-8">
                <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Recent Imports</h4>
                <div class="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 divide-y divide-gray-200 dark:divide-slate-700">
                    <div class="p-4 flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <i class="fa-solid fa-file-excel text-green-500 text-xl"></i>
                            <div>
                                <p class="text-sm font-medium text-gray-900 dark:text-gray-100">inventory_update_sdad_mar21.xlsx</p>
                                <p class="text-xs text-gray-500 dark:text-gray-400">Mar 21, 2026 • 24kb</p>
                            </div>
                        </div>
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                            Completed, 134 records parsed
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `,

    renderPartModalDetails: (part, inventory, movements) => `
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Part Spec Card -->
            <div class="col-span-1 md:col-span-1 bg-gray-50 dark:bg-slate-800/50 rounded-xl p-5 border border-gray-200 dark:border-slate-700 shadow-sm">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4 border-b border-gray-200 dark:border-slate-700 pb-2">Master Details</h4>
                
                <dl class="space-y-3">
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.description}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Brand / Type</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.brand} (${part.brandType})</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Category</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.category}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Weight</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.weight}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Dimensions</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.dimension}</dd>
                    </div>
                    <div class="flex justify-between">
                        <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Volume</dt>
                        <dd class="text-sm text-gray-900 dark:text-white font-medium text-right">${part.volume}</dd>
                    </div>
                    <div class="flex justify-between pt-2 border-t border-gray-200 dark:border-slate-700">
                        <dt class="text-sm font-bold text-gray-900 dark:text-white">Reorder Point</dt>
                        <dd class="text-sm font-bold text-brand-600 dark:text-brand-400">${part.reorderPoint} pcs</dd>
                    </div>
                </dl>
            </div>

            <!-- Subsidiary Breakdown -->
            <div class="col-span-1 md:col-span-2 space-y-6">
                
                <!-- Stock Level Indicator -->
                <div class="bg-white dark:bg-slate-800 rounded-xl p-5 border border-gray-200 dark:border-slate-700 shadow-sm">
                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4 border-b border-gray-200 dark:border-slate-700 pb-2">Subsidiary Stock Distribution</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        ${SUBSIDIARIES.map(sub => {
                            const subInv = inventory.find(i => i.company === sub);
                            if (!subInv) {
                                return `
                                <div class="p-3 bg-gray-50 dark:bg-slate-900 rounded-lg text-center border border-gray-100 dark:border-slate-700/50">
                                    <h5 class="font-bold text-gray-700 dark:text-gray-300 text-sm">${sub}</h5>
                                    <p class="text-gray-400 dark:text-gray-500 text-xl font-medium mt-1">0</p>
                                    <p class="text-xs text-gray-400 mt-1">No Stock</p>
                                </div>`;
                            }
                            
                            const isCrit = subInv.quantity < part.reorderPoint;
                            return `
                                <div class="p-3 ${isCrit ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800/50' : 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800/50'} rounded-lg text-center border">
                                    <h5 class="font-bold text-gray-700 dark:text-gray-300 text-sm">${sub}</h5>
                                    <p class="${isCrit ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'} text-2xl font-bold mt-1">${subInv.quantity}</p>
                                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1"><i class="fa-solid fa-location-dot mr-1"></i>${subInv.zone}</p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Trend Chart -->
                <div class="bg-white dark:bg-slate-800 rounded-xl p-5 border border-gray-200 dark:border-slate-700 shadow-sm">
                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4 border-b border-gray-200 dark:border-slate-700 pb-2">Historical Movement</h4>
                    <div class="relative h-48 w-full">
                        <canvas id="modal-movement-chart"></canvas>
                    </div>
                </div>

            </div>
        </div>
    `
};

window.UI = UI;
