#!/usr/bin/env python3
from database import engine
from models import Base, User

print("=" * 60)
print("🗄️  CRIANDO TABELAS NO BANCO DE DADOS")
print("=" * 60)

try:
    Base.metadata.create_all(engine)
    print("\n✅ Tabelas criadas com sucesso!")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    
    print(f"\nTabelas disponíveis: {len(tabelas)}")
    for tabela in tabelas:
        print(f"   📋 {tabela}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
