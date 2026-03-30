// js/data.js

const BRANDS = ['Toyota', 'Nissan', 'Mazda', 'Honda', 'Mercedes-Benz', 'GMC', 'Ford', 'BMW', 'Hyundai', 'Kia'];
const BRAND_TYPES = ['Genuine', 'Aftermarket'];
const CATEGORIES = ['Body', 'Electrical', 'Suspension', 'Engine', 'Transmission', 'Brakes', 'Interior'];
const SUBSIDIARIES = ['SDAD', 'AFRA', 'Carmania'];

// Helper to generate random numbers
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Helper to generate a part number
function generatePN() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const prefix = 'PN-' + randomInt(1000, 9999);
    const suffix = chars.charAt(randomInt(0, 25)) + chars.charAt(randomInt(0, 25));
    return `${prefix}-${suffix}`;
}

// Generate Catalog of Parts
function generatePartsCatalog(count = 50) {
    const catalog = [];
    for (let i = 0; i < count; i++) {
        catalog.push({
            id: `pt_${i}`,
            partNumber: generatePN(),
            description: `Automotive Part ${i + 1}`,
            weight: `${(Math.random() * 10 + 0.5).toFixed(2)} kg`,
            brand: BRANDS[randomInt(0, BRANDS.length - 1)],
            brandType: BRAND_TYPES[randomInt(0, BRAND_TYPES.length - 1)],
            dimension: `${randomInt(10, 100)}x${randomInt(10, 100)}x${randomInt(10, 100)} cm`,
            volume: `${(Math.random() * 0.5 + 0.01).toFixed(3)} m³`,
            category: CATEGORIES[randomInt(0, CATEGORIES.length - 1)],
            costPrice: randomInt(10, 500),
            reorderPoint: randomInt(20, 100)
        });
    }
    return catalog;
}

// Generate active Inventory records linking Parts -> Subsidiaries
function generateInventory(catalog) {
    const inventory = [];
    
    catalog.forEach(part => {
        SUBSIDIARIES.forEach(sub => {
            // Random chance to not have stock in a subsidiary
            if (Math.random() > 0.1) {
                const stock = randomInt(0, 300); // Sometimes goes to 0 (critical)
                inventory.push({
                    id: `inv_${part.id}_${sub}`,
                    partId: part.id,
                    company: sub,
                    quantity: stock,
                    zone: `Zone-${String.fromCharCode(65 + randomInt(0, 5))}-${randomInt(1, 10)}`,
                    value: stock * part.costPrice
                });
            }
        });
    });
    
    return inventory;
}

// Movement History for a specific part (Mocking influx/outflow)
function generateMovements(partId) {
    const movements = [];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Last 6 months
    for(let i=6; i>=0; i--) {
        const d = new Date();
        d.setMonth(d.getMonth() - i);
        
        movements.push({
            month: months[d.getMonth()],
            year: d.getFullYear(),
            in: randomInt(10, 100),
            out: randomInt(5, 90)
        });
    }
    return movements;
}

// Initialize and Expose
const APP_DATA = {
    catalog: generatePartsCatalog(100),
    inventory: [],
    movements: {} // Cached movements by partId
};

APP_DATA.inventory = generateInventory(APP_DATA.catalog);

// Helper functions for data retrieval
const DataService = {
    getPartByNumber: (pn) => APP_DATA.catalog.find(p => p.partNumber === pn),
    getPartById: (id) => APP_DATA.catalog.find(p => p.id === id),
    getAllParts: () => APP_DATA.catalog,
    getInventoryByPart: (partId) => APP_DATA.inventory.filter(i => i.partId === partId),
    
    // Aggregates
    getSystemTotalValue: () => APP_DATA.inventory.reduce((sum, item) => sum + item.value, 0),
    getCompanyTotalValue: (company) => APP_DATA.inventory.filter(i => i.company === company).reduce((sum, item) => sum + item.value, 0),
    
    // Enriched Inventory (Join Part and Inventory)
    getEnrichedInventory: (companyFilter = 'ALL') => {
        let items = APP_DATA.inventory;
        if (companyFilter !== 'ALL') {
            items = items.filter(i => i.company === companyFilter);
        }
        
        return items.map(inv => {
            const part = APP_DATA.catalog.find(p => p.id === inv.partId);
            return {
                ...inv,
                ...part, // spread part details including reorderPoint, partNumber
                status: inv.quantity < part.reorderPoint ? 'Critical' : (inv.quantity < part.reorderPoint * 1.5 ? 'Warning' : 'Healthy')
            };
        });
    },

    getMovements: (partId) => {
        if (!APP_DATA.movements[partId]) {
            APP_DATA.movements[partId] = generateMovements(partId);
        }
        return APP_DATA.movements[partId];
    }
};

window.DataService = DataService;
window.BRANDS = BRANDS;
window.CATEGORIES = CATEGORIES;
