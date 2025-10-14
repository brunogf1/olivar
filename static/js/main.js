document.addEventListener('DOMContentLoaded', function () {
  const data = window.initialData || [];
  const columns = window.columns || [];
  const visibilityKey = 'dt_col_visibility_v1';

  // Linha extra de filtros no cabeçalho
  const thead = document.querySelector('#tabela thead');
  const filterRow = thead.rows[0].cloneNode(true);
  filterRow.classList.add('filters');
  for (let th of filterRow.children) {
    th.innerHTML = '<input type="text" placeholder="Filtrar..." />';
  }
  thead.appendChild(filterRow);

  const table = $('#tabela').DataTable({
    data: data,
    columns: columns.map(c => ({ data: c, title: c })),
    orderCellsTop: true,
    pageLength: 100,
    deferRender: true,
    language: { url: 'https://cdn.datatables.net/plug-ins/1.13.8/i18n/pt-BR.json' },
    initComplete: function () {
      const api = this.api();
      // Filtros por coluna
      api.columns().every(function (colIdx) {
        const cell = $('.filters th').eq(colIdx);
        const input = $('input', cell);
        input.off('keyup change').on('keyup change', function () {
          const val = this.value || '';
          api.column(colIdx).search(val, false, true).draw();
        });
      });
    }
  });

  // Botão "Colunas" (colVis)
  new $.fn.dataTable.Buttons(table, {
    buttons: [
      { extend: 'colvis', text: 'Colunas', postfixButtons: ['colvisRestore'] }
    ]
  });
  table.buttons().container().appendTo('#colvis-container');

  // Aplica visibilidade salva
  try {
    const saved = JSON.parse(localStorage.getItem(visibilityKey) || 'null');
    if (saved && Array.isArray(saved)) {
      table.columns().every(function (idx) {
        const title = $(table.column(idx).header()).text().trim();
        const shouldBeVisible = saved.includes(title);
        table.column(idx).visible(shouldBeVisible, false);
      });
      table.columns.adjust().draw(false);
    }
  } catch (e) { /* ignore */ }

  // Persiste visibilidade ao mudar
  table.on('column-visibility.dt', function () {
    const visibleNames = [];
    table.columns().every(function (idx) {
      if (table.column(idx).visible()) {
        const title = $(table.column(idx).header()).text().trim();
        visibleNames.push(title);
      }
    });
    localStorage.setItem(visibilityKey, JSON.stringify(visibleNames));
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

    // Tenta congelar cabeçalho
    ws['!freeze'] = { xSplit: 0, ySplit: 1, topLeftCell: "A2", activePane: "bottomLeft", state: "frozen" };

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Estoque');
    XLSX.writeFile(wb, 'estoque_filtrado.xlsx', { bookType: 'xlsx', compression: true });
  });
});