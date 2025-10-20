from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URI = "sqlite:///olivar.db"
#DATABASE_URI = "postgresql://postgres:Richard150403@localhost:5432/olivar"
engine  = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
