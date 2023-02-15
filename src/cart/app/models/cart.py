from pydantic import BaseModel, Field
from typing import Optional, List


class CartItemModel(BaseModel):
    id: str = Field(
        regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    quantity: str


class CartModel(BaseModel):
    id: Optional[str] = Field(
        regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    items: List[CartItemModel]


class CartPaginateModel(BaseModel):
    items: List[CartModel]
    next: Optional[str]
