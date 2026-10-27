"""HTTP layer for categories: parse, delegate to CategoryService, respond."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from api.deps import get_category_service
from core.auth import require_user
from schemas.category import Category, CategoryCreate, CategoryUpdate
from services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate,
                          service: CategoryService = Depends(get_category_service),
                          user: dict = Depends(require_user)):
    return service.create_category(category.model_dump(mode="json"))


@router.get("/", response_model=List[Category])
async def list_categories(service: CategoryService = Depends(get_category_service)):
    return service.list_categories()


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: UUID,
                       service: CategoryService = Depends(get_category_service)):
    return service.get_category(category_id)


@router.put("/{category_id}", response_model=Category)
async def update_category(category_id: UUID, category: CategoryUpdate,
                          service: CategoryService = Depends(get_category_service),
                          user: dict = Depends(require_user)):
    return service.update_category(category_id, category.model_dump(mode="json"))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: UUID,
                          service: CategoryService = Depends(get_category_service),
                          user: dict = Depends(require_user)):
    service.delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
