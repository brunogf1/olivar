document.addEventListener('DOMContentLoaded', function () {
const data = window.initialData || [];
const columns = window.columns || [];
const visibilityKey = 'dt_col_visibility_v1';
const filtersKey = 'dt_col_filters_v1';


const table = $('#tabela').DataTable({
data: data,
columns: columns.map(c => ({ 
  data: c, 
  title: c,
  width: '180px'
})),
autoWidth: false,
orderCellsTop: true,
pageLength: 100,
deferRender: true,
scrollX: true,
scrollY: '600px',
scrollCollapse: true,
fixedColumns: { left: 4, heightMatch: 'auto' },
language: { url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/pt-BR.json' },
initComplete: function () {
// Constrói barra externa de filtros
buildFiltersBar();

  // Ajusta FixedColumns após layout
  setTimeout(() => {
    table.fixedColumns().update();
  }, 100);

  // Aplica filtros salvos (se houver)
  applySavedFiltersOnce();
}
});

// Botão "Colunas" (colVis)
new $.fn.dataTable.Buttons(table, {
buttons: [{ extend: 'colvis', text: 'Colunas', postfixButtons: ['colvisRestore'] }]
});
table.buttons().container().appendTo('#colvis-container');

// Aplica visibilidade salva de colunas
try {
const saved = JSON.parse(localStorage.getItem(visibilityKey) || 'null');
if (saved && Array.isArray(saved)) {
table.columns().every(function (idx) {
const title = $(table.column(idx).header()).text().trim();
const shouldBeVisible = saved.includes(title);
table.column(idx).visible(shouldBeVisible, false);
});
table.columns.adjust().draw(false);
setTimeout(() => {
table.fixedColumns().update();
buildFiltersBar();
applySavedFiltersOnce();
}, 0);
}
} catch (e) { /* ignore */ }

// Persiste visibilidade ao mudar + atualiza barra de filtros
table.on('column-visibility.dt', function () {
const visibleNames = [];
table.columns().every(function (idx) {
if (table.column(idx).visible()) {
const title = $(table.column(idx).header()).text().trim();
visibleNames.push(title);
}
});
localStorage.setItem(visibilityKey, JSON.stringify(visibleNames));

setTimeout(() => {
  table.columns.adjust();
  table.fixedColumns().update();
  buildFiltersBar();
  applySavedFiltersOnce();
}, 0);
});

// Mantém FixedColumns saudável após draw
table.on('draw.dt', function () {
setTimeout(() => {
table.fixedColumns().update();
}, 0);
});

// Exporta Excel respeitando filtros e colunas visíveis
document.getElementById('export-btn').addEventListener('click', function () {
const filtered = table.rows({ search: 'applied' }).data().toArray();
if (!filtered.length) {
alert('Não há dados para exportar.');
return;
}
const headers = table.columns(':visible').header().toArray().map(h => h.textContent.trim());
const rowsAoA = filtered.map(rowObj =>
headers.map(h => (rowObj[h] !== undefined && rowObj[h] !== null) ? rowObj[h] : '')
);
const aoa = [headers, ...rowsAoA];
const ws = XLSX.utils.aoa_to_sheet(aoa);

// AutoFilter
const range = { s: { r: 0, c: 0 }, e: { r: rowsAoA.length, c: headers.length - 1 } };
ws['!autofilter'] = { ref: XLSX.utils.encode_range(range) };

// Larguras
ws['!cols'] = headers.map((h, idx) => {
  let maxLen = String(h).length;
  for (const row of rowsAoA) {
    const len = String(row[idx] ?? '').length;
    if (len > maxLen) maxLen = len;
  }
  return { wch: Math.min(40, Math.max(10, maxLen + 2)) };
});

// Congela cabeçalho e as 4 primeiras colunas no Excel
ws['!freeze'] = { xSplit: 4, ySplit: 1, topLeftCell: "E2", activePane: "bottomRight", state: "frozen" };

const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, 'Estoque');
XLSX.writeFile(wb, 'estoque_filtrado.xlsx', { bookType: 'xlsx', compression: true });
});

// ------------ Barra externa de filtros ------------

function buildFiltersBar() {
let bar = document.getElementById('filters-bar');
if (!bar) {
const toolbar = document.querySelector('.toolbar');
bar = document.createElement('div');
bar.id = 'filters-bar';
if (toolbar && toolbar.parentElement) {
toolbar.insertAdjacentElement('afterend', bar);
} else {
document.body.appendChild(bar);
}
}

// Cabeçalho da barra
bar.innerHTML = '';
const header = document.createElement('div');
header.className = 'filters-header';

const title = document.createElement('div');
title.className = 'filters-title';
title.textContent = 'Filtros por coluna';

const clearBtn = document.createElement('button');
clearBtn.id = 'clear-filters';
clearBtn.textContent = 'Limpar filtros';
clearBtn.addEventListener('click', clearAllFilters);

header.appendChild(title);
header.appendChild(clearBtn);

const row = document.createElement('div');
row.className = 'filters-row';

// Filtros por colunas visíveis
const saved = loadFiltersMap();
const visibleIdx = table.columns(':visible').indexes().toArray();

// Para aplicar de uma vez ao final
const applyQueue = [];

visibleIdx.forEach(idx => {
  const col = table.column(idx);
  const colTitle = $(col.header()).text().trim();

  const wrap = document.createElement('div');
  wrap.className = 'filter-item';

  const label = document.createElement('label');
  label.textContent = colTitle;

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Filtrar...';

  // Valor atual: salvo ou já em uso no DataTables
  const currentSearch = col.search() || saved[colTitle] || '';
  if (currentSearch) {
    input.value = currentSearch;
    // Se DataTables ainda não estiver com esse valor (ex. vindo do storage), agenda aplicação
    if (col.search() !== currentSearch) {
      applyQueue.push({ idx, val: currentSearch });
    }
  }

  input.addEventListener('input', debounce(() => {
    const val = input.value || '';
    col.search(val, false, true);
    saveFilterValue(colTitle, val);
    table.draw(false);
  }, 250));

  wrap.appendChild(label);
  wrap.appendChild(input);
  row.appendChild(wrap);
});

bar.appendChild(header);
bar.appendChild(row);

// Aplica fila de filtros salvos em uma única draw
if (applyQueue.length) {
  applyQueue.forEach(({ idx, val }) => table.column(idx).search(val, false, true));
  table.draw(false);
}
}

function clearAllFilters() {
// Limpa inputs da barra
const inputs = document.querySelectorAll('#filters-bar .filter-item input');
inputs.forEach(inp => inp.value = '');

// Limpa buscas de todas as colunas (visíveis e ocultas)
table.columns().every(function (idx) {
  table.column(idx).search('');
});
table.draw(false);

// Limpa storage
localStorage.removeItem(filtersKey);
}

function applySavedFiltersOnce() {
const saved = loadFiltersMap();
if (!saved || !Object.keys(saved).length) return;

const titlesByIdx = {};
table.columns().every(function (idx) {
  const title = $(table.column(idx).header()).text().trim();
  titlesByIdx[idx] = title;
});

let changed = false;
table.columns().every(function (idx) {
  const title = titlesByIdx[idx];
  const val = saved[title] || '';
  if ((table.column(idx).search() || '') !== val) {
    table.column(idx).search(val, false, true);
    changed = true;
  }
});
if (changed) table.draw(false);
}

// ------------ Utilidades ------------

function loadFiltersMap() {
try { return JSON.parse(localStorage.getItem(filtersKey) || '{}'); }
catch { return {}; }
}

function saveFilterValue(title, val) {
const map = loadFiltersMap();
if (val && val.length) map[title] = val;
else delete map[title];
localStorage.setItem(filtersKey, JSON.stringify(map));
}

function debounce(fn, wait) {
let t;
return function (...args) {
clearTimeout(t);
t = setTimeout(() => fn.apply(this, args), wait);
};
}
});