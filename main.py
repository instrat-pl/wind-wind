
from fastapi import Depends, FastAPI, HTTPException, Query
from wind_wind.db import WindProfile, WindProfileBase, WindProfileMeta, WindProfileWithValues, get_session, bytes_to_array, create_db_and_tables
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()
create_db_and_tables()

@app.get("/profiles", response_model=list[WindProfileMeta])
def search(
    method: str | None = None,
    min_capacity: float | None = None,
    session: Session = Depends(get_session),
):
    # Select only metadata columns so the BLOBs aren't loaded
    stmt = select(*[getattr(WindProfile, f) for f in WindProfileMeta.model_fields])
    if method:
        stmt = stmt.where(WindProfile.method == method)
    if min_capacity is not None:
        stmt = stmt.where(WindProfile.capacity >= min_capacity)
    return [WindProfileMeta(**row._mapping) for row in session.exec(stmt)]

@app.get("/profiles/{id}", response_model=WindProfileWithValues)
def get_one(id: int, session: Session = Depends(get_session)):
    ts = session.get(WindProfile, id)
    if not ts:
        raise HTTPException(404, "Not found")
    values = bytes_to_array(ts.data)
    return WindProfileWithValues(
        **ts.model_dump(exclude={"data"}),
        values=values.tolist(),
    )