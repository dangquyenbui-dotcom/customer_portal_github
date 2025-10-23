// customer_portal/static/js/inventory.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Customer Inventory page loaded");

    initializeSorting(); // Setup sort handlers first
    attachFilterListeners();
    restoreFilters(); // Restore filters from sessionStorage
    restoreSortState(); // Restore sort state
    updateSortIndicators(); // Update visual indicators for sort
    filterInventoryTable(); // Apply initial filter and sort

    // Export button listener
    document.getElementById('exportBtn').addEventListener('click', exportVisibleDataToXlsx);
});

// --- Global State ---
const FILTER_STORAGE_KEY = 'customerInventoryFilters';
const SORT_STORAGE_KEY = 'customerInventorySort';
let sortState = { // Default sort
    column: 'Part',
    direction: 'asc',
    columnIndex: 0,
    columnType: 'string'
};

// --- Event Listeners ---
function attachFilterListeners() {
    document.getElementById('partFilter').addEventListener('change', filterInventoryTable);
    document.getElementById('binFilter').addEventListener('change', filterInventoryTable);
    document.getElementById('textSearch').addEventListener('input', dtUtils.debounce(filterInventoryTable, 250)); // Debounce text search
    document.getElementById('resetBtn').addEventListener('click', resetFilters);
}

// --- Filter Logic ---
function saveFilters() {
    const filters = {
        part: document.getElementById('partFilter').value,
        bin: document.getElementById('binFilter').value,
        text: document.getElementById('textSearch').value,
    };
    sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filters));
}

function restoreFilters() {
    const savedFilters = JSON.parse(sessionStorage.getItem(FILTER_STORAGE_KEY));
    if (savedFilters) {
        document.getElementById('partFilter').value = savedFilters.part || '';
        document.getElementById('binFilter').value = savedFilters.bin || '';
        document.getElementById('textSearch').value = savedFilters.text || '';
    }
}

function resetFilters() {
    document.getElementById('partFilter').value = '';
    document.getElementById('binFilter').value = '';
    document.getElementById('textSearch').value = '';
    sessionStorage.removeItem(FILTER_STORAGE_KEY);
    filterInventoryTable(); // Re-apply empty filters
}

function filterInventoryTable() {
    const partFilter = document.getElementById('partFilter').value;
    const binFilter = document.getElementById('binFilter').value;
    const textSearch = document.getElementById('textSearch').value.toLowerCase();

    const tableBody = document.getElementById('inventory-body');
    const rows = tableBody.querySelectorAll('tr');
    let visibleCount = 0;

    rows.forEach(row => {
        // Skip header rows if any, or placeholder rows
        if (row.cells.length < 11) return;

        const part = row.cells[0].textContent;
        const description = row.cells[1].textContent.toLowerCase();
        const bin = row.cells[4].textContent;
        const userLot = row.cells[5].textContent.toLowerCase();
        const reference = row.cells[7].textContent.toLowerCase();
        const po = row.cells[8].textContent.toLowerCase();

        let show = true;

        if (partFilter && part !== partFilter) show = false;
        if (binFilter && bin !== binFilter) show = false;
        if (textSearch && !(
               description.includes(textSearch) ||
               userLot.includes(textSearch) ||
               reference.includes(textSearch) ||
               po.includes(textSearch)
           )) {
            show = false;
        }

        row.classList.toggle('hidden-row', !show);
        if (show) visibleCount++;
    });

    updateRowCount(visibleCount, rows.length);
    saveFilters();
    sortTable(); // Re-apply sort after filtering
}

function updateRowCount(visible, total) {
    const rowCountEl = document.getElementById('rowCount');
    if (rowCountEl) {
        rowCountEl.textContent = `Showing ${visible} of ${total} rows`;
    }
}

// --- Sorting Logic (Adapted from Production Portal) ---

function initializeSorting() {
    document.querySelectorAll('.grid-table .sortable').forEach(th => {
        th.addEventListener('click', handleSort);
    });
}

function saveSortState() {
    sessionStorage.setItem(SORT_STORAGE_KEY, JSON.stringify(sortState));
}

function restoreSortState() {
    const savedSort = sessionStorage.getItem(SORT_STORAGE_KEY);
    if (savedSort) {
        try {
            const parsedSort = JSON.parse(savedSort);
            // Basic validation
            if (parsedSort && typeof parsedSort === 'object' && 'column' in parsedSort && 'direction' in parsedSort) {
                sortState = parsedSort;
                 // Find the header element to get the index and type dynamically
                const headerEl = document.querySelector(`.sortable[data-column-id="${sortState.column}"]`);
                if(headerEl) {
                    sortState.columnIndex = Array.from(headerEl.parentElement.children).indexOf(headerEl);
                    sortState.columnType = headerEl.dataset.type || 'string';
                } else {
                    console.warn("Saved sort column header not found, reverting to default.");
                    setDefaultSortState(); // Revert if header is missing
                }
            } else {
                 setDefaultSortState(); // Set default if saved state is invalid
            }
        } catch (e) {
            console.error("Could not parse saved sort state:", e);
            sessionStorage.removeItem(SORT_STORAGE_KEY);
            setDefaultSortState(); // Set default on parse error
        }
    } else {
         setDefaultSortState(); // Set default if nothing is saved
    }
}

function setDefaultSortState() {
     // Default to sorting by 'Part' ascending
    const defaultHeader = document.querySelector('.sortable[data-column-id="Part"]');
     if (defaultHeader) {
         sortState = {
             column: 'Part',
             direction: 'asc',
             columnIndex: Array.from(defaultHeader.parentElement.children).indexOf(defaultHeader),
             columnType: defaultHeader.dataset.type || 'string'
         };
     } else {
         // Fallback if even the Part header isn't found (unlikely)
         sortState = { column: 'Part', direction: 'asc', columnIndex: 0, columnType: 'string' };
     }
}


function handleSort(e) {
    const th = e.currentTarget;
    const columnId = th.dataset.columnId;
    const columnType = th.dataset.type || 'string';
    const columnIndex = Array.from(th.parentElement.children).indexOf(th);

    if (sortState.column === columnId) {
        // Cycle direction: asc -> desc -> none (remove sort) -> asc ...
        // For simplicity, let's just toggle asc/desc for now
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = columnId;
        sortState.direction = 'asc'; // Default to ascending on new column
    }
    sortState.columnIndex = columnIndex;
    sortState.columnType = columnType;

    sortTable();
    updateSortIndicators();
    saveSortState();
}

function updateSortIndicators() {
    document.querySelectorAll('.grid-table .sortable').forEach(th => {
        const indicator = th.querySelector('.sort-indicator');
        if (!indicator) return;

        th.classList.remove('sorted-asc', 'sorted-desc');
        indicator.textContent = ''; // Clear indicator

        if (th.dataset.columnId === sortState.column) {
            if (sortState.direction === 'asc') {
                th.classList.add('sorted-asc');
                indicator.textContent = '↑';
            } else if (sortState.direction === 'desc') {
                th.classList.add('sorted-desc');
                indicator.textContent = '↓';
            }
        }
    });
}

function getSortValue(cell, type) {
    if (!cell) return null; // Handle missing cells
    const text = cell.textContent.trim();
    if (!text || text.toLowerCase() === 'n/a') {
        // Consistent handling for empty/N/A values
        switch (type) {
            case 'numeric': return -Infinity; // Sort N/A numbers first/last depending on direction
            case 'date':    return new Date('2999-12-31'); // Sort N/A dates last
            default:        return ''; // Sort N/A strings first
        }
    }

    switch (type) {
        case 'numeric':
            return parseFloat(text.replace(/,/g, '')) || 0; // Remove commas for parsing
        case 'date':
            // Assuming MM/DD/YYYY format from the SQL query
            const parts = text.match(/(\d{2})\/(\d{2})\/(\d{4})/);
            if (parts) {
                // parts[0] is full match, parts[1]=MM, parts[2]=DD, parts[3]=YYYY
                return new Date(parts[3], parts[1] - 1, parts[2]); // Month is 0-indexed
            }
            return new Date('2999-12-31'); // Treat invalid dates as far future
        default: // string
            return text.toLowerCase();
    }
}

function sortTable() {
    if (!sortState.column || sortState.direction === 'none' || sortState.columnIndex < 0) {
        console.log("Skipping sort, invalid state:", sortState);
        return; // Don't sort if no column selected or index invalid
    }

    const tbody = document.getElementById('inventory-body');
    // Get only visible rows for sorting
    const rows = Array.from(tbody.querySelectorAll('tr:not(.hidden-row)'));

    rows.sort((a, b) => {
        // Ensure rows have enough cells before trying to access them
        if (a.cells.length <= sortState.columnIndex || b.cells.length <= sortState.columnIndex) {
            return 0; // Keep relative order if a row is malformed
        }
        const valA = getSortValue(a.cells[sortState.columnIndex], sortState.columnType);
        const valB = getSortValue(b.cells[sortState.columnIndex], sortState.columnType);

        let comparison = 0;
        if (valA === null && valB === null) comparison = 0;
        else if (valA === null) comparison = -1; // Put nulls first (or last if desc)
        else if (valB === null) comparison = 1;
        else if (valA < valB) comparison = -1;
        else if (valA > valB) comparison = 1;

        return sortState.direction === 'asc' ? comparison : (comparison * -1);
    });

    // Re-append sorted visible rows. Hidden rows remain untouched in their original positions.
    rows.forEach(row => tbody.appendChild(row));
}


// --- Export Logic (Adapted from Production Portal) ---
function exportVisibleDataToXlsx() {
    const exportBtn = document.getElementById('exportBtn');
    exportBtn.disabled = true;
    exportBtn.textContent = '📥 Generating...';

    // Get visible headers
    const headers = Array.from(document.querySelectorAll('.grid-table thead th'))
        .filter(th => th.style.display !== 'none' && th.dataset.columnId !== 'Customer_Part') // Exclude hidden columns
        .map(th => th.textContent.replace('↑','').replace('↓','').trim()); // Clean header text

    const rows = [];
    document.querySelectorAll('#inventory-body tr:not(.hidden-row)').forEach(row => {
        const rowData = [];
        // Iterate through cells corresponding to visible headers
        Array.from(row.cells).forEach((cell, index) => {
             const headerCell = document.querySelector(`.grid-table thead th:nth-child(${index + 1})`);
             if (headerCell && headerCell.style.display !== 'none' && headerCell.dataset.columnId !== 'Customer_Part') {
                 rowData.push(cell.textContent.trim());
             }
        });
        rows.push(rowData);
    });

    if (rows.length === 0) {
        dtUtils.showAlert('No data currently visible to export.', 'info');
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
        return;
    }

    fetch('/inventory/api/export-xlsx', { // Correct API endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headers, rows })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.message || `HTTP error ${response.status}`); });
        }
        const disposition = response.headers.get('Content-Disposition');
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        const filename = (matches != null && matches[1]) ? matches[1].replace(/['"]/g, '') : 'inventory_export.xlsx';
        return Promise.all([response.blob(), filename]);
    })
    .then(([blob, filename]) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
    })
    .catch(error => {
        console.error('Export error:', error);
        dtUtils.showAlert(`An error occurred during the export: ${error.message}`, 'error');
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Download XLSX';
    });
}