let dadosOriginais = [];

document.addEventListener('DOMContentLoaded', () => {
    carregarComparativo();
});

// Reutilizando a lógica de alerta se possível, ou recriando simples
function mostrarAlert(mensagem, tipo = 'danger') {
    const alert = document.getElementById('alert');
    if(alert) {
        alert.textContent = mensagem;
        alert.className = `alert show alert-${tipo}`;
        setTimeout(() => alert.classList.remove('show'), 4000);
    } else {
        alert(mensagem);
    }
}

async function sincronizarEstoque() {
    const btn = document.getElementById('btnSync');
    if(!confirm("Atenção: Isso irá apagar os dados locais de estoque e baixar novamente da API.\nDeseja continuar?")) return;

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Sincronizando...';

    try {
        const response = await fetch('/olivar/api/estoque/sincronizar', { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            mostrarAlert(data.mensagem, 'success');
            carregarComparativo(); // Recarrega a tabela
        } else {
            mostrarAlert(data.erro || 'Erro ao sincronizar', 'danger');
        }
    } catch (err) {
        mostrarAlert('Erro de conexão: ' + err.message, 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
    }
}

async function carregarComparativo() {
    const tbody = document.getElementById('tbodyComparativo');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">Carregando dados...</td></tr>';

    try {
        const response = await fetch(`/olivar/api/inventarios/${INVENTARIO_ID}/comparativo`);
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.erro || "Erro ao carregar");

        dadosOriginais = data;
        renderizarTabela(dadosOriginais);
        atualizarResumo(dadosOriginais);

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:red;">Erro: ${err.message}</td></tr>`;
    }
}

function renderizarTabela(dados) {
    const tbody = document.getElementById('tbodyComparativo');
    
    if (dados.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px;">Nenhum item encontrado.</td></tr>`;
        return;
    }

    tbody.innerHTML = dados.map(item => {
        const diff = item.diferenca;
        let rowClass = diff !== 0 ? 'row-divergente' : '';
        let colorClass = diff === 0 ? 'text-success' : (diff < 0 ? 'text-danger' : 'text-primary');
        let sinal = diff > 0 ? '+' : '';

        return `
            <tr class="${rowClass}">
                <td data-label="Código"><strong>${item.cod_item}</strong></td>
                <td data-label="Descrição">
                    <span class="mascara-info">${item.mascara || ''}</span>
                    <span class="desc-info">${item.descricao || 'Sem descrição'}</span>
                </td>
                <td data-label="Sistema" class="text-center">${item.qtd_sistema}</td>
                <td data-label="Lido" class="text-center"><strong>${item.qtd_lida}</strong></td>
                <td data-label="Diferença" class="text-center ${colorClass}">
                    <strong>${sinal}${diff}</strong>
                </td>
            </tr>
        `;
    }).join('');
}

function atualizarResumo(dados) {
    const total = dados.length;
    const divergentes = dados.filter(d => d.diferenca !== 0).length;
    const corretos = total - divergentes;

    document.getElementById('totalItens').innerText = total;
    document.getElementById('totalDivergente').innerText = divergentes;
    document.getElementById('totalCorreto').innerText = corretos;
}

function filtrarTabela() {
    const termo = document.getElementById('searchInput').value.toLowerCase();
    const status = document.getElementById('filterStatus').value;

    const filtrados = dadosOriginais.filter(item => {
        const matchTermo = 
            item.cod_item.toLowerCase().includes(termo) || 
            (item.descricao && item.descricao.toLowerCase().includes(termo)) ||
            (item.mascara && item.mascara.toLowerCase().includes(termo));
        
        let matchStatus = true;
        if (status === 'divergente') matchStatus = item.diferenca !== 0;
        if (status === 'ok') matchStatus = item.diferenca === 0;

        return matchTermo && matchStatus;
    });

    renderizarTabela(filtrados);
}
