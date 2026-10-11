from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

import models
import schemas
from database import get_db

app = FastAPI(
    title="Backend Dashboard Pengguna",
    description=(
        "API sederhana untuk mengelola data pengguna, dibangun "
        "untuk latihan Pengembangan Aplikasi Web."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def baca_root():
    return {"pesan": "Backend FastAPI berjalan"}


@app.get("/users", response_model=list[schemas.UserRead], tags=["Users"])
def baca_semua_pengguna(
    q: Optional[str] = None, db: Session = Depends(get_db)
):
    stmt = select(models.User)
    if q:
        pola = f"%{q}%"
        stmt = stmt.where(
            or_(
                models.User.name.ilike(pola),
                models.User.username.ilike(pola),
            )
        )
    return db.scalars(stmt).all()


@app.get(
    "/users/{user_id}", response_model=schemas.UserRead, tags=["Users"]
)
def baca_satu_pengguna(user_id: int, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail="Pengguna tidak ditemukan"
        )
    return user


@app.post(
    "/users",
    response_model=schemas.UserRead,
    status_code=201,
    tags=["Users"],
)
def tambah_pengguna(
    data: schemas.UserCreate, db: Session = Depends(get_db)
):
    user = models.User(**data.model_dump())
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Username sudah dipakai"
        )
    db.refresh(user)
    return user

@app.post(
    "/orders",
    response_model=schemas.OrderRead,
    status_code=201,
    tags=["Orders"],
)
def buat_pesanan(
    data: schemas.OrderCreate, db: Session = Depends(get_db)
):
    user = db.get(models.User, data.user_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail="Pengguna tidak ditemukan"
        )
    order = models.Order(**data.model_dump())
    db.add(order)
    db.flush()
    user.saldo -= data.total
    if user.saldo < 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Saldo tidak cukup")
    db.commit()
    db.refresh(order)
    return order

@app.get(
    "/users-dengan-pesanan",
    response_model=list[schemas.UserWithOrders],
    tags=["Users"],
)
def users_dengan_pesanan(db: Session = Depends(get_db)):
    stmt = select(models.User).options(
        selectinload(models.User.orders)
    )
    return db.scalars(stmt).all()