from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter

import auth
import models
import schemas
from database import get_db
from deps import get_current_user, require_admin

app = FastAPI(
    title="Backend Dashboard Pengguna",
    description=(
        "API sederhana untuk mengelola data pengguna, dibangun "
        "untuk latihan Pengembangan Aplikasi Web."
    ),
    version="3.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/", tags=["Root"])
def baca_root():
    return {"pesan": "Backend FastAPI berjalan"}


@app.get("/me", response_model=schemas.UserRead, tags=["Users"])
def profil_saya(saya: models.User = Depends(get_current_user)):
    return saya


@app.get("/users", response_model=list[schemas.UserPublik], tags=["Users"])
def baca_semua_pengguna(
    q: Optional[str] = None,
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    "/users/{user_id}", response_model=schemas.UserPublik, tags=["Users"]
)
def baca_satu_pengguna(
    user_id: int,
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail="Pengguna tidak ditemukan"
        )
    return user


@app.post(
    "/orders",
    response_model=schemas.OrderRead,
    status_code=201,
    tags=["Orders"],
)
def buat_pesanan(
    data: schemas.OrderCreate,
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = models.Order(user_id=saya.id, **data.model_dump())
    db.add(order)
    db.flush()
    saya.saldo -= data.total
    if saya.saldo < 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Saldo tidak cukup")
    db.commit()
    db.refresh(order)
    return order


@app.get(
    "/orders/saya",
    response_model=list[schemas.OrderRead],
    tags=["Orders"],
)
def pesanan_saya(saya: models.User = Depends(get_current_user)):
    return saya.orders


@app.get(
    "/orders/{order_id}",
    response_model=schemas.OrderRead,
    tags=["Orders"],
)
def baca_satu_pesanan(
    order_id: int,
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(models.Order, order_id)
    if order is None or (
        order.user_id != saya.id and saya.role != "admin"
    ):
        raise HTTPException(
            status_code=404, detail="Pesanan tidak ditemukan"
        )
    return order


@app.get(
    "/orders",
    response_model=list[schemas.OrderRead],
    tags=["Orders"],
)
def baca_semua_pesanan(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.scalars(select(models.Order)).all()


@app.get(
    "/users/{user_id}/orders",
    response_model=list[schemas.OrderRead],
    tags=["Orders"],
)
def pesanan_milik_pengguna(
    user_id: int,
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != saya.id and saya.role != "admin":
        raise HTTPException(
            status_code=404, detail="Pengguna tidak ditemukan"
        )
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(
            status_code=404, detail="Pengguna tidak ditemukan"
        )
    return user.orders


# ---- Endpoint dari Pertemuan 9 (belum diubah) ----
@app.get(
    "/users-dengan-pesanan",
    response_model=list[schemas.UserWithOrders],
    tags=["Users"],
)
def users_dengan_pesanan(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.User).options(selectinload(models.User.orders))
    return db.scalars(stmt).all()

@app.post(
    "/saldo/kirim", response_model=schemas.UserRead, tags=["Saldo"]
)
def kirim_saldo(
    ke_username: str = Form(),
    jumlah: int = Form(gt=0),
    saya: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.User).where(
        models.User.username == ke_username
    )
    penerima = db.scalars(stmt).first()
    if penerima is None or penerima.id == saya.id:
        raise HTTPException(
            status_code=404, detail="Penerima tidak ditemukan"
        )
    if saya.saldo < jumlah:
        raise HTTPException(status_code=400, detail="Saldo tidak cukup")
    saya.saldo -= jumlah
    penerima.saldo += jumlah
    db.commit()
    db.refresh(saya)
    return saya