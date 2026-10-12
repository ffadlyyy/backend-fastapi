from security import (
    baca_token,
    buat_token,
    hash_password,
    verify_password,
)

h = hash_password("Rahasia123")
print(h)
print(verify_password("Rahasia123", h), verify_password("salah", h))

t = buat_token(7)
print(t)
print(baca_token(t), baca_token(t + "x"))