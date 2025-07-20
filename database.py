from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URI = "postgresql://postgres:Azaza130705!@localhost:5432/olivar"
engine  = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
