import hashlib
import time

import bcrypt

password = "password123"
data = password.encode()

print("MD5 :", hashlib.md5(data).hexdigest())
print("SHA-256 :", hashlib.sha256(data).hexdigest())

h1 = bcrypt.hashpw(data, bcrypt.gensalt())
h2 = bcrypt.hashpw(data, bcrypt.gensalt())
print("bcrypt 1:", h1.decode())
print("bcrypt 2:", h2.decode())
print("Sama? :", h1 == h2)
print("Cocok :", bcrypt.checkpw(data, h1), bcrypt.checkpw(b"salah", h1))

mulai = time.perf_counter()
for i in range(100_000):
    hashlib.md5(f"tebakan{i}".encode()).hexdigest()
md5_detik = time.perf_counter() - mulai
print(f"\n100.000 tebakan MD5 : {md5_detik:.3f} detik")

for cost in (4, 10, 12):
    garam = bcrypt.gensalt(rounds=cost)
    mulai = time.perf_counter()
    bcrypt.hashpw(data, garam)
    detik = time.perf_counter() - mulai
    perkiraan = detik * 100_000
    print(f"1 hash bcrypt cost {cost:>2}: {detik:.3f} detik "
          f"-> 100.000 tebakan = {perkiraan / 60:.1f} menit")