from pydantic import BaseModel
from typing import List


class BillItemCreate(BaseModel):
    item_code: str
    quantity: int


class SalesResponse(BaseModel):
    message: str
