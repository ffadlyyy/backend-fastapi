import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY belum diatur atau kurang dari 32 karakter. "
        "Buat file .env berisi SECRET_KEY..., lihat langkah ini."
    )

ALGORITHM = "HS256"
TOKEN_MENIT = 15