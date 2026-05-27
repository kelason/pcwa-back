from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from api.supabase_client import supabase

router = APIRouter(prefix="/categories", tags=["Categories"])

# --- Pydantic Models ---

class CategoryBase(BaseModel):
    name: str = Field(..., example="Electronics")

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: UUID

# --- API Endpoints ---

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate):
    """Create a new product category."""
    data = category.model_dump(mode="json")
    response = supabase.table("categories").insert(data).execute()
    
    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create category")
    
    return response.data[0]

@router.get("/", response_model=List[Category])
async def list_categories():
    """List all available categories."""
    response = supabase.table("categories").select("*").execute()
    return response.data

@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: UUID):
    """Retrieve a single category by ID."""
    response = supabase.table("categories").select("*").eq("id", str(category_id)).execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {category_id} not found")
    
    return response.data[0]