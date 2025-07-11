from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Time, BigInteger

Base = declarative_base()

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    text = Column(String(1024), nullable=False)
    time = Column(Time, nullable=False)
    active = Column(Boolean, default=True)