from sqlalchemy import Column, Integer, Float, String, Date
from database import Base

class Releve(Base):
    __tablename__ = "releves_indices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    zone = Column(String)
    indice = Column(Float)