from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Electronics"})

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Category name cannot be empty")
        return cleaned


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class Category(CategoryBase):
    id: UUID
