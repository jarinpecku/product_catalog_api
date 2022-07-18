from pydantic import BaseModel, Field


class ProductNoId(BaseModel):
    name: str = Field(example="Benzinová sekačka Dosquarna")
    description: str = Field(example="Nejlepší sekačka na trhu. TLDR")


class Product(ProductNoId):
    id: int = Field(example=42)


product_not_found_response = {404: {"content": {"application/json": {"example": dict(detail="Product not found")}}}}
product_conflict_response = {409: {"content": {"application/json": {"example": dict(detail="Product of this name already exists")}}}}
delete_response = {200: {"content": {"application/json": {"example": ""}}},
                   409: {"content": {"application/json": {"example": dict(detail="Product of this name already exists")}}}
                   }
list_of_offers = {200: {"content": {"application/json": {"example": [dict(offer_id=11, product_id=23, price=17, items_in_stock=4),
                                                                     dict(offer_id=14, product_id=23, price=16, items_in_stock=27),
                                                                     dict(offer_id=27, product_id=23, price=15, items_in_stock=1)]}}}}
prices = {200: {"content": {"application/json": {"example": {"prices": [14, 15, 10, 13, 12], "growth": -14.29}}}}}

