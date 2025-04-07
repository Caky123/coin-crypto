from pydantic import BaseModel


class CoinBase(BaseModel):
    id_text: str
    name: str
    symbol: str


class CoinCreate(CoinBase):
    pass

    class Config:
        orm_mode = True
