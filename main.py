from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

class UserIn(BaseModel):
    name: str
    username: str
    email: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

users_db = [
    {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
    },
    {
        "id": 2,
        "name": "Ervin Howell",
        "username": "Antonette",
        "email": "Shanna@melissa.tv",
    },
    {
        "id": 3,
        "name": "Clementine Bauch",
        "username": "Samantha",
        "email": "Nathan@yesenia.net",
    },
    {
        "id": 4,
        "name": "Patricia Lebsack",
        "username": "Karianne",
        "email": "Julianne.OConner@kory.org",
    },
    {
        "id": 5,
        "name": "Chelsey Dietrich",
        "username": "Kamren",
        "email": "Lucio_Hettinger@annie.ca",
    },
]

@app.get("/")
def baca_root():
    return {"pesan": "Backend FastAPI berjalan"}

@app.get("/users")
def baca_semua_pengguna(q: Optional[str] = None):
    if q:
        kata_kunci = q.lower()
        hasil = [
            u for u in users_db
            if kata_kunci in u["name"].lower()
            or kata_kunci in u["username"].lower()
        ]
        return hasil
    return users_db

@app.get("/users/{user_id}")
def baca_satu_pengguna(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

@app.post("/users", status_code=201)
def tambah_pengguna(user: UserIn):
    id_baru = max(u["id"] for u in users_db) + 1
    pengguna_baru = {
        "id": id_baru,
        **user.model_dump(),
    }
    users_db.append(pengguna_baru)
    return pengguna_baru
