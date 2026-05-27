from typing import List, Optional, Literal
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from api.supabase_client import supabase

router = APIRouter(prefix="/products", tags=["Products"])

# --- Pydantic Models ---

class ProductBase(BaseModel):
    name: str = Field(..., example="Wireless Mouse")
    price: Decimal = Field(..., ge=0, example=25.99)
    category_id: UUID = Field(..., example="550e8400-e29b-41d4-a716-446655440000")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    category_id: Optional[UUID] = None

class Product(ProductBase):
    id: UUID

class PaginatedProductResponse(BaseModel):
    items: List[Product]
    total: int
    page: int
    size: int

# --- API Endpoints ---

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    """Add a new product to the catalog."""
    data = product.model_dump(mode="json")
    try:
        response = supabase.table("products").insert(data).execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create product")
    
    return response.data[0]

@router.get("/", response_model=PaginatedProductResponse)
async def list_products(
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    page: int = Query(1, ge=1, description="Page number"),
    sort_by: str = Query("name", description="Sort order: name, price_low, or price_high")
):
    """View a list of products with optional category_id filtering, ordered by name, with pagination."""
    page_size = 10
    start = (page - 1) * page_size
    end = start + page_size - 1

    try:
        # Initialize query builder
        query = supabase.table("products").select("*", count="exact")

        # 1. Apply Filters first
        if category_id:
            query = query.eq("category_id", str(category_id))

        # 2. Apply Dynamic Sorting
        if sort_by == "price_low":
            query = query.order("price", desc=False)
        elif sort_by == "price_high":
            query = query.order("price", desc=True)
        else:
            query = query.order("name", desc=False) # Default to ascending for name

        # 3. Apply Range and Execute
        response = query.range(start, end).execute()
    except Exception as e:
        # Catch-all for database or execution errors to prevent ASGI worker crashes
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {
        "items": response.data,
        "total": response.count if response.count is not None else 0,
        "page": page,
        "size": page_size
    }

@router.get("/category/{category_id}", response_model=List[Product])
async def get_products_by_category(category_id: UUID):
    """Retrieve products belonging to a specific category."""
    response = supabase.table("products").select("*").eq("category_id", str(category_id)).execute()
    return response.data

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: UUID):
    """Retrieve a single product by ID."""
    try:
        response = supabase.table("products").select("*").eq("id", str(product_id)).execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
    
    return response.data[0]

@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: UUID, product_update: ProductUpdate):
    """Edit an existing product."""
    update_data = {k: v for k, v in product_update.model_dump(mode="json").items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        response = supabase.table("products").update(update_data).eq("id", str(product_id)).execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
    
    return response.data[0]

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID):
    """Delete a product from the catalog."""
    # Supabase .delete() returns the deleted rows by default in the SDK execute()
    try:
        response = supabase.table("products").delete().eq("id", str(product_id)).execute()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")
    
    return None