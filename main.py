from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/data/search")
async def get_filtered_data(
    start_date: date,
    end_date: date,
    zone: Optional[str] = None,
    min_index: Optional[float] = None,
    max_index: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Releve).filter(
        models.Releve.date >= start_date,
        models.Releve.date <= end_date
    )

    if zone:
        query = query.filter(models.Releve.zone == zone)
    
    if min_index is not None:
        query = query.filter(models.Releve.indice >= min_index)
        
    if max_index is not None:
        query = query.filter(models.Releve.indice <= max_index)

    return query.all()