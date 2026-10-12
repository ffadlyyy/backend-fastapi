from sqlalchemy import delete

import models
from database import SessionLocal
from security import hash_password

PASSWORD_AWAL = "Toko#12345"

DATA = [
    ("Leanne Graham", "Bret", "Sincere@april.biz"),
    ("Ervin Howell", "Antonette", "Shanna@melissa.tv"),
    ("Clementine Bauch", "Samantha", "Nathan@yesenia.net"),
    ("Patricia Lebsack", "Karianne", "Julianne.OConner@kory.org"),
    ("Chelsey Dietrich", "Kamren", "Lucio_Hettinger@annie.ca"),
]

PESANAN = [
    ("Kopi Arabika", 2, 60000),
    ("Teh Melati", 1, 25000),
    ("Gula Aren", 3, 45000),
]


def isi_data():
    db = SessionLocal()
    try:
        db.execute(delete(models.Order))
        db.execute(delete(models.User))
        sandi = hash_password(PASSWORD_AWAL)
        for nama, uname, email in DATA:
            user = models.User(
                name=nama,
                username=uname,
                email=email,
                saldo=500000,
                password_hash=sandi,
            )
            user.orders = [
                models.Order(produk=p, jumlah=j, total=t)
                for p, j, t in PESANAN
            ]
            db.add(user)
        db.add(
            models.User(
                name="Admin Toko",
                username="admin",
                email="admin@toko.id",
                saldo=0,
                role="admin",
                password_hash=hash_password("Adm1n#Toko-2026"),
            )
        )
        db.commit()
        print("Seed selesai:", len(DATA) + 1, "pengguna,",
              len(DATA) * len(PESANAN), "pesanan")
    finally:
        db.close()


if __name__ == "__main__":
    isi_data()