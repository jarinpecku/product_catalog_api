from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    id: Optional[int]
    name: str
    description: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Benzinová sekačka Dosquarna",
                "description": "Nejlepší sekačka na trhu. TLDR",
            }
        }