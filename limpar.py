from database import Session
from models import Inventario, ItemInventario
from sqlalchemy import text

def limpar_tudo():
    db = Session()
    try:
        print("🗑️  Iniciando limpeza do banco de dados...")

        # 1. Apagar Itens Lidos (Tabela Filha de Inventarios)
        rows_itens = db.query(ItemInventario).delete()
        print(f"✓ {rows_itens} registros removidos de 'itens_inventario'")

        # 3. Apagar Inventários (Tabela Pai)
        rows_inv = db.query(Inventario).delete()
        print(f"✓ {rows_inv} registros removidos de 'inventarios'")

        # Confirma as alterações
        db.commit()
        print("\n✅ Limpeza concluída com sucesso! O banco está zerado.")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro ao limpar banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Confirmação de segurança
    resposta = input("ATENÇÃO: Isso apagará TODOS os dados de inventário. Tem certeza? (s/n): ")
    if resposta.lower() == 's':
        limpar_tudo()
    else:
        print("Operação cancelada.")