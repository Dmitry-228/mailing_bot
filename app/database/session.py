from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DB_URL

engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)
