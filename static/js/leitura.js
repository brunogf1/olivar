// ========== ESTADO GLOBAL ==========
const inventarioId = window.location.pathname.split('/')[3];
let alertTimeout = null; // Para controlar o tempo do alerta no topo

// ========== FUNÇÕES UTILITÁRIAS ==========

// 1. Alerta no Topo da Tela
function mostrarAlert(mensagem, tipo = 'danger') {
  const alert = document.getElementById('alert');
  
  // Reinicia timer se já houver um alerta (para não sumir rápido demais)
  if (alertTimeout) clearTimeout(alertTimeout);

  alert.textContent = mensagem;
  alert.className = 'alert'; // Limpa classes anteriores
  alert.classList.add(`alert-${tipo}`);
  
  // Força repintura para garantir animação
  requestAnimationFrame(() => {
    alert.classList.add('show');
  });

  // Esconde após 4 segundos
  alertTimeout = setTimeout(() => {
    alert.classList.remove('show');
  }, 4000);
}

// 2. Feedback Visual abaixo do Input (ScanStatus)
function mostrarScanStatus(tipo) {
  const status = document.getElementById('scanStatus');
  
  // Reseta classes para garantir a cor certa
  status.className = 'scan-status';
  
  if (tipo === 'success') {
    status.textContent = '✓ Sucesso';
    status.classList.add('success'); // Verde
  } 
  else if (tipo === 'duplicate') {
    status.textContent = '⚠ Código já lido!';
    status.classList.add('warning'); // Laranja (NOVO)
  }
  else {
    status.textContent = '✕ Código inválido'; 
    status.classList.add('error');   // Vermelho
  }

  // Ativa a animação de opacidade
  requestAnimationFrame(() => {
    status.classList.add('active');
  });

  // Esconde após 1.5 segundos
  setTimeout(() => {
    status.classList.remove('active');
  }, 1500);
}

// ========== CARREGAR ITENS SALVOS ==========
async function carregarItensSalvos() {
  try {
    const response = await fetch(`/olivar/api/inventarios/${inventarioId}/itens`);
    
    if (!response.ok) throw new Error("Falha ao buscar itens");

    const itens = await response.json();
    
    // Apenas passamos a lista completa; o filtro de 3 itens ocorre no renderizarTabela
    if (itens.length === 0) {
      renderizarTabelaVazia();
      return;
    }
    
    renderizarTabela(itens);
  } catch (err) {
    console.error(err); // Log silencioso ao carregar para não poluir a tela inicial
  }
}

// ========== ADICIONAR ITEM (Lógica Principal) ==========
async function adicionarItem() {
  const codigoInput = document.getElementById('barcodeInput');
  const codigo = codigoInput.value.trim();

  // 1. Validação local: Campo vazio
  if (!codigo) {
    mostrarScanStatus('error');
    mostrarAlert('Leia um código de barras válido', 'warning');
    codigoInput.focus();
    return;
  }

  try {
    const response = await fetch(`/olivar/api/inventarios/${inventarioId}/itens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cod_barra_ord: codigo })
    });

    let resultado;
    try {
        resultado = await response.json();
    } catch (e) {
        throw new Error("Erro de comunicação com o servidor.");
    }

    // === TRATAMENTO DE RESPOSTAS ===
    if (!response.ok) {
      
      // CASO 1: Item Duplicado (Status 409 Conflict)
      if (response.status === 409) {
        mostrarScanStatus('duplicate'); // Mostra amarelo "Já lido"
        mostrarAlert(resultado.erro, 'warning'); // Alerta amarelo no topo
      } 
      // CASO 2: Outros Erros (404 Não encontrado, 500 Erro server)
      else {
        mostrarScanStatus('error'); // Mostra vermelho "Inválido"
        mostrarAlert(resultado.erro || 'Erro desconhecido', 'danger');
      }

      // Limpa e foca imediatamente para não travar a operação
      codigoInput.value = ''; 
      codigoInput.focus();
      return;
    }

    // === SUCESSO ===
    mostrarScanStatus('success');

    const msgSucesso = `Sucesso: ${resultado.dados.desc_tecnica}`;
    mostrarAlert(msgSucesso, 'success');

    // Atualiza tabela
    carregarItensSalvos();
    
    // Limpa e foca para o próximo
    codigoInput.value = '';
    codigoInput.focus();

  } catch (err) {
    // Erro de Rede/Fetch
    mostrarScanStatus('error');
    mostrarAlert('Erro: ' + err.message, 'danger');
    codigoInput.value = '';
    codigoInput.focus();
  }
}

// ========== RENDERIZAÇÃO DA TABELA ==========
function renderizarTabelaVazia() {
  const tbody = document.getElementById('tabelaItens');
  tbody.innerHTML = `
    <tr>
      <td colspan="4" style="text-align: center; padding: 20px; color: #6c757d;">
        Nenhum item lido ainda
      </td>
    </tr>
  `;
}

function renderizarTabela(itens) {
  const tbody = document.getElementById('tabelaItens');
  
  if (!itens || itens.length === 0) {
    renderizarTabelaVazia();
    return;
  }

  // === ALTERAÇÃO: Filtra apenas os 3 primeiros itens ===
  // (Assumindo que a API já retorna ordenado por timestamp DESC)
  const ultimos3 = itens.slice(0, 3);

  tbody.innerHTML = ultimos3.map(item => `
    <tr class="last-scanned">
      <td data-label="Código"><code>${item.cod_barra_ord}</code></td>
      <td data-label="Descrição">${item.desc_tecnica || item.cod_item}</td>
      <td data-label="Máscara">${item.mascara}</td>
      <td data-label="Qtd"><strong>${item.quantidade}</strong></td>
    </tr>
  `).join('');
}

// ========== EVENT LISTENERS ==========

// Enviar ao pressionar Enter
document.getElementById('barcodeInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    adicionarItem();
  }
});

// Manter foco no input (Trap Focus para Coletores)
document.addEventListener('click', (e) => {
  const tag = e.target.tagName;
  // Só devolve o foco se não clicou em algo interativo
  if (tag !== 'BUTTON' && tag !== 'A' && tag !== 'INPUT') {
    document.getElementById('barcodeInput').focus();
  }
});

// ========== INICIALIZAÇÃO ==========
document.addEventListener('DOMContentLoaded', () => {
  carregarItensSalvos();
  
  // Pequeno delay para garantir foco no Android após renderizar
  setTimeout(() => {
      document.getElementById('barcodeInput').focus();
  }, 500);
});
