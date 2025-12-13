// ========== FUNÇÕES MODAL ==========
function abrirModalCriar() {
  document.getElementById('modalCriar').classList.add('show');
  document.getElementById('nomeInventario').focus();
}

function fecharModalCriar() {
  document.getElementById('modalCriar').classList.remove('show');
  document.getElementById('nomeInventario').value = '';
}

function mostrarAlert(mensagem, tipo = 'danger') {
  const alert = document.getElementById('alert');
  alert.textContent = mensagem;
  alert.className = `alert show alert-${tipo}`;
  setTimeout(() => alert.classList.remove('show'), 4000);
}

// ========== FUNÇÕES API ==========
async function carregarInventarios() {
  try {
    const response = await fetch('/api/inventarios');
    const data = await response.json();
    renderizarTabela(data);
  } catch (err) {
    mostrarAlert('Erro ao carregar inventários: ' + err.message);
  }
}

async function criarInventario() {
  const nome = document.getElementById('nomeInventario').value.trim();
  if (!nome) {
    mostrarAlert('Digite o nome do inventário');
    return;
  }

  try {
    const response = await fetch('/api/inventarios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome })
    });
    const data = await response.json();
    
    if (!response.ok) {
      mostrarAlert(data.erro || 'Erro ao criar inventário');
      return;
    }

    mostrarAlert('Inventário criado com sucesso!', 'success');
    fecharModalCriar();
    carregarInventarios();
  } catch (err) {
    mostrarAlert('Erro: ' + err.message);
  }
}

async function fecharInventario(id) {
  if (!confirm('Tem certeza que deseja FECHAR este inventário?')) return;

  try {
    const response = await fetch(`/api/inventarios/${id}/fechar`, {
      method: 'PUT'
    });
    const data = await response.json();

    if (!response.ok) {
      mostrarAlert(data.erro || 'Erro ao fechar inventário');
      return;
    }

    mostrarAlert('Inventário fechado com sucesso!', 'success');
    carregarInventarios();
  } catch (err) {
    mostrarAlert('Erro: ' + err.message);
  }
}

async function deletarInventario(id) {
  if (!confirm('Tem certeza que deseja DELETAR este inventário?')) return;

  try {
    const response = await fetch(`/api/inventarios/${id}`, {
      method: 'DELETE'
    });
    const data = await response.json();

    if (!response.ok) {
      mostrarAlert(data.erro || 'Erro ao deletar inventário');
      return;
    }

    mostrarAlert('Inventário deletado com sucesso!', 'success');
    carregarInventarios();
  } catch (err) {
    mostrarAlert('Erro: ' + err.message);
  }
}

// ========== RENDERIZAÇÃO RESPONSIVA ==========
function renderizarTabela(inventarios) {
  const tbody = document.getElementById('tabelaInventarios');
  
  if (inventarios.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">Nenhum inventário criado</div></td></tr>`;
    return;
  }

  tbody.innerHTML = inventarios.map(inv => {
    const statusClass = `status-${inv.status.toLowerCase()}`;
    let botoes = '';

    if (inv.status === 'Aberto') {
      botoes = `
        <a href="/inventarios/${inv.id}/leitura" class="btn btn-success">Abrir</a>
        <button onclick="fecharInventario(${inv.id})" class="btn btn-warning">Fechar</button>
        <button onclick="deletarInventario(${inv.id})" class="btn btn-danger">Excluir</button>
      `;
    } else {
      botoes = `
        <a href="/inventarios/${inv.id}/comparativo" class="btn btn-info">Comparativo</a>
        <button onclick="deletarInventario(${inv.id})" class="btn btn-danger">Excluir</button>
      `;
    }

    return `
      <tr>
        <td data-label="Nome"><strong>${inv.nome}</strong></td>
        <td data-label="Início">${inv.data_inicio}</td>
        <td data-label="Fim">${inv.data_fim}</td>
        <td data-label="Status"><span class="status-badge ${statusClass}">${inv.status}</span></td>
        <td data-label="Ações"><div class="actions">${botoes}</div></td>
      </tr>
    `;
  }).join('');
}

// ========== INICIALIZAÇÃO ==========
document.addEventListener('DOMContentLoaded', carregarInventarios);

// Fechar modal ao pressionar ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') fecharModalCriar();
});

// Permitir criar ao pressionar ENTER no input
document.getElementById('nomeInventario').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') criarInventario();
});
