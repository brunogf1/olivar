from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str]
    password: Mapped[str]

class StatusInventario(enum.Enum):
    ABERTO = "Aberto"
    FECHADO = "Fechado"
    
class Inventario(Base):
    __tablename__ = 'inventarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(150), nullable=False)
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    status = Column(SQLEnum(StatusInventario), default=StatusInventario.ABERTO)
    criado_em = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'data_inicio': self.data_inicio.strftime('%d/%m/%Y %H:%M') if self.data_inicio else '-',
            'data_fim': self.data_fim.strftime('%d/%m/%Y %H:%M') if self.data_fim else '-',
            'status': self.status.value,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M')
        }

class ItemInventario(Base):
    __tablename__ = 'itens_inventario'
    
    id = Column(Integer, primary_key=True)
    inventario_id = Column(Integer, ForeignKey('inventarios.id'), nullable=False, index=True)
    cod_barra_ord = Column(String(50), nullable=False)
    cod_item = Column(String(50), nullable=False)
    etiq_id = Column(Integer, nullable=False)
    desc_tecnica = Column(String(300), nullable=False)
    mascara = Column(String(200), nullable=False)
    tmasc_item_id = Column(Integer, nullable=False)
    quantidade = Column(Integer, default=1)
    timestamp = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'inventario_id': self.inventario_id,
            'cod_barra_ord': self.cod_barra_ord,
            'cod_item': self.cod_item,
            'etiq_id': self.etiq_id,
            'desc_tecnica': self.desc_tecnica,
            'mascara': self.mascara,
            'tmasc_item_id': self.tmasc_item_id,
            'quantidade': self.quantidade,
            'timestamp': self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else '-'
        }