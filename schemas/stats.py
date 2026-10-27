from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_products: int
    total_categories: int
    average_price: float
    inventory_value: float
