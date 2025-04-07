from app.config import Base
from sqlalchemy import (Column, ForeignKey, Integer, Numeric, String, Table,
                        Text)
from sqlalchemy.orm import relationship

user_coin_association = Table(
    "user_coin_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("coin_id_text", Integer, ForeignKey("coins.id_text"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    coins = relationship("Coin", secondary=user_coin_association, back_populates="users")

    def to_dict(self, include_password=False):
        user_dict = {
            "id": self.id,
            "email": self.email,
        }

        if include_password:
            user_dict["password"] = self.password

        return user_dict


class Coin(Base):
    __tablename__ = "coins"

    id_text = Column(Text, primary_key=True, index=True)
    symbol = Column(Text, index=True)
    name = Column(Text)
    price = Column(Numeric)

    users = relationship("User", secondary=user_coin_association, back_populates="coins")
