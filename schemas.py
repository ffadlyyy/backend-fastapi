from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(
        min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$"
    )
    email: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def maks_72_byte(cls, nilai: str) -> str:
        # bcrypt hanya membaca 72 byte pertama password
        if len(nilai.encode()) > 72:
            raise ValueError("Password maksimal 72 byte")
        return nilai


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserPublik(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    email: str

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    email: str
    saldo: int
    role: str


class OrderCreate(BaseModel):
    produk: str
    jumlah: int = Field(gt=0)
    total: int = Field(gt=0)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    produk: str
    jumlah: int
    total: int


class UserWithOrders(UserRead):
    orders: list[OrderRead] = []