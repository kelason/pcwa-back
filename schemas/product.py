from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, json_schema_extra={"example": "Wireless Mouse"})
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0, json_schema_extra={"example": 25.99})
    category_id: UUID = Field(..., json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"})
    image_url: Optional[str] = None
    sku: Optional[str] = None
    stock: int = Field(0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    category_id: Optional[UUID] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    stock: Optional[int] = Field(default=None, ge=0)


class Product(ProductBase):
    id: UUID
    deleted_at: Optional[str] = None


class PaginatedProductResponse(BaseModel):
    items: List[Product]
    total: int
    page: int
    size: int


class BulkDeleteRequest(BaseModel):
    ids: List[UUID] = Field(..., min_length=1)


class BulkDeleteResult(BaseModel):
    deleted: int
    failed: List[dict]


class BulkCategorizeRequest(BaseModel):
    ids: List[UUID] = Field(..., min_length=1)
    category_id: UUID


class BulkCategorizeResult(BaseModel):
    updated: int
    failed: List[dict] = []


class ImportResult(BaseModel):
    created: int
    failed: List[dict]


class AuditEntry(BaseModel):
    id: str
    product_id: str
    actor: str
    action: str
    before: Optional[dict] = None
    after: Optional[dict] = None
