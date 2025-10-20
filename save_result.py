import json
from time import sleep
from datetime import datetime
import os

from visualizacao_de_dados.api import get_main_data

def save_data():
    """Busca dados da API e salva no result.json, substituindo completamente o arquivo anterior"""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Buscando dados da API...")
        data = get_main_data()
        
        # Salva com encoding UTF-8 e sobrescreve o arquivo (modo 'w')
        with open('result.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Dados atualizados! Total de itens: {len(data)}")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Erro ao buscar/salvar dados: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SERVIÇO DE ATUALIZAÇÃO DE DADOS - OLIVAR")
    print("=" * 60)
    print(f"Intervalo de atualização: 12 horas")
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Primeira execução imediata
    save_data()
    
    # Loop infinito com atualização a cada 12 horas
    while True:
        sleep(12 * 60 * 60)  # 12 horas
        save_data()