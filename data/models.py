from sqlalchemy import Column, Integer, Float, String
from data.database import Base

class Mesure(Base):
    __tablename__ = "mesures"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String)
    station_name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    indice = Column(Float)
    horaire = Column(String)
    date = Column(String)