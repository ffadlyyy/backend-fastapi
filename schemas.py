from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
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

class OrderCreate(BaseModel):
    user_id: int
    produk: str
    jumlah: int
    total: int

class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    produk: str
    jumlah: int
    total: int

class UserWithOrders(UserRead):
    orders: list[OrderRead] = []