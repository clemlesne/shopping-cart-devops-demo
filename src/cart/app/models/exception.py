from pydantic import BaseModel
from typing import Optional


class ExceptionDetailModel(BaseModel):
    code: int
    details: Optional[str]
    id: str
    message: str
    type: str


class ExceptionModel(BaseModel):
    exception: ExceptionDetailModel
