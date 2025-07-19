from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from visualizacao_de_dados.database import db


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str]
    password: Mapped[str]


Base.metadata.create_all(db)
