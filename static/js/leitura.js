// ========== ESTADO GLOBAL ==========
const inventarioId = window.location.pathname.split('/')[2];

// ========== FUNÇÕES UTILITÁRIAS ==========
function mostrarAlert(mensagem, tipo = 'danger') {
  const alert = document.getElementById('alert');
  alert.textContent = mensagem;
  alert.className = `alert show alert-${tipo}`;
  setTimeout(() => alert.classList.remove('show'), 3000);
}

function mostrarScanStatus() {
  const status = document.getElementById('scanStatus');
  status.classList.add('active');
  setTimeout(() => status.classList.remove('active'), 1500);
}

// ========== CARREGAR ITENS SALVOS ==========
async function carregarItensSalvos() {
  try {
    const response = await fetch(`/olivar/api/inventarios/${inventarioId}/itens`);
    const itens = await response.json();
    
    if (itens.length === 0) {
      renderizarTabelaVazia();
      return;
    }
    
    renderizarTabela(itens);
  } catch (err) {
    mostrarAlert('Erro ao carregar itens: ' + err.message);
  }
}

// ========== ADICIONAR ITEM (QUANTIDADE AUTOMÁTICA DA API) ==========
async function adicionarItem() {
  const codigoInput = document.getElementById('barcodeInput');
  const codigo = codigoInput.value.trim();

  if (!codigo) {
    mostrarAlert('Leia um código de barras válido');
    codigoInput.focus();
    return;
  }

  // 1. Valida código na API
  try {
    const response = await fetch(`/olivar/api/validar-codigo-barras?codigo=${encodeURIComponent(codigo)}`);
    
    if (!response.ok) {
      mostrarAlert(` Código "${codigo}" não encontrado no catálogo`, 'danger');
      codigoInput.value = '';
      codigoInput.focus();
      return;
    }

    // Não precisamos fazer nada com o JSON aqui, pois o backend vai revalidar e pegar a qtd
    await response.json();
    
  } catch (err) {
    mostrarAlert('Erro ao validar código: ' + err.message);
    return;
  }

  // 2. Adiciona ao inventário (Backend decide a quantidade)
  try {
    const response = await fetch(`/olivar/api/inventarios/${inventarioId}/itens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cod_barra_ord: codigo
        // Quantidade removida daqui. O backend pega da API externa.
      })
    });

    const resultado = await response.json();

    if (!response.ok) {
      mostrarAlert(resultado.erro || 'Erro ao adicionar item');
      codigoInput.focus();
      return;
    }

    mostrarAlert(
      resultado.mensagem === 'Item incrementado' 
        ? ` Quantidade incrementada (Qtd Etiqueta: ${resultado.dados.quantidade})`
        : ` ${resultado.dados.desc_tecnica} adicionado`,
      'success'
    );

    carregarItensSalvos();
    mostrarScanStatus();

    // Limpa input
    codigoInput.value = '';
    codigoInput.focus();

  } catch (err) {
    mostrarAlert('Erro ao salvar item: ' + err.message);
  }
}

// ========== RENDERIZAÇÃO ==========
function renderizarTabelaVazia() {
  const tbody = document.getElementById('tabelaItens');
  tbody.innerHTML = `
    <tr>
      <td colspan="5">
        <div class="empty-state">
          <p>Nenhum item lido ainda</p>
      </td>
    </tr>
  `;
}

function renderizarTabela(itens) {
  const tbody = document.getElementById('tabelaItens');
  
  if (itens.length === 0) {
    renderizarTabelaVazia();
    return;
  }

  tbody.innerHTML = itens.map(item => `
    <tr class="last-scanned">
      <td><code>${item.cod_barra_ord}</code></td>
      <td>${item.desc_tecnica}</td>
      <td>${item.mascara}</td>
      <td><strong>${item.quantidade}</strong></td>
      <td>${item.timestamp}</td>
    </tr>
  `).join('');
}

// ========== EVENT LISTENERS ==========
document.getElementById('barcodeInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    adicionarItem();
  }
});

// Manter foco no campo de código de barras
document.addEventListener('click', (e) => {
  if (e.target.tagName === 'INPUT') {
    return;
  }
  document.getElementById('barcodeInput').focus();
});

// ========== INICIALIZAÇÃO ==========
document.addEventListener('DOMContentLoaded', () => {
  carregarItensSalvos();
  document.getElementById('barcodeInput').focus();
});