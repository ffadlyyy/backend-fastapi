from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from config import ALGORITHM, SECRET_KEY, TOKEN_MENIT

def hash_password(password: str) -> str:
    hasil = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hasil.decode()

def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def buat_token(user_id: int) -> str:
    sekarang = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": sekarang,
        "exp": sekarang + timedelta(minutes=TOKEN_MENIT),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def baca_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None