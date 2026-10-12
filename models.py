from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    saldo: Mapped[int] = mapped_column(server_default=text("0"))
    password_hash: Mapped[str] = mapped_column(
        String(255), server_default=""
    )
    role: Mapped[str] = mapped_column(
        String(20), server_default="user"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    produk: Mapped[str] = mapped_column(String(100))
    jumlah: Mapped[int]
    total: Mapped[int]
    user: Mapped["User"] = relationship(back_populates="orders")