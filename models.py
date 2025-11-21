from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
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
    
    id = Column(Integer, primary_key=True),
    nome = Column(String(150), nullable  = True),
    data_inicio = Column(DateTime, nullable = True),
    data_fim = Column(DateTime, nullable = True),
    status = Column(SQLEnum(StatusInventario), default=StatusInventario.ABERTO)
    criado_em = Column(DateTime, default=func.row())
    
    def to_dict(self):
        return { 
            'id': self.id,
            'nome': self.nome,
            'data_inicio': self.data_inicio.strftime('%d/%m/%Y %H:%M') if self.data_inicio else '-',
            'data_fim': self.data_fim.strftime('%d/%m/%Y %H:%M') if self.data_fim else '-',
            'status': self.status.value,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M')
        }