"""HTTP layer for products: parse, delegate to ProductService, respond.
All business rules live in services/product_service.py."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from api.deps import get_product_service
from core.auth import actor_of, require_user
from schemas.product import (
    AuditEntry,
    BulkCategorizeRequest,
    BulkCategorizeResult,
    BulkDeleteRequest,
    BulkDeleteResult,
    ImportResult,
    PaginatedProductResponse,
    Product,
    ProductCreate,
    ProductUpdate,
)
from services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


def _dump(model) -> dict:
    return model.model_dump(mode="json")


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate,
                         service: ProductService = Depends(get_product_service),
                         user: dict = Depends(require_user)):
    return service.create_product(_dump(product), actor_of(user))


@router.get("/", response_model=PaginatedProductResponse)
async def list_products(
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    in_stock: bool = Query(False),
    page: int = Query(1, ge=1),
    sort_by: str = Query("name"),
    service: ProductService = Depends(get_product_service),
):
    return service.list_products(
        category_id=category_id, search=search, min_price=min_price,
        max_price=max_price, in_stock=in_stock, sort_by=sort_by, page=page)


@router.get("/export")
async def export_products(
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    service: ProductService = Depends(get_product_service),
):
    body = service.export_csv(category_id=category_id, search=search)
    return Response(content=body, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=products.csv"})


@router.post("/import", response_model=ImportResult)
async def import_products(
    file: UploadFile = File(...),
    service: ProductService = Depends(get_product_service),
    user: dict = Depends(require_user),
):
    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail="CSV file exceeds 2 MB")
    return service.import_csv(raw.decode("utf-8-sig"), actor_of(user))


@router.post("/bulk-delete", response_model=BulkDeleteResult)
async def bulk_delete(payload: BulkDeleteRequest,
                      service: ProductService = Depends(get_product_service),
                      user: dict = Depends(require_user)):
    return service.bulk_delete(payload.ids, actor_of(user))


@router.post("/bulk-categorize", response_model=BulkCategorizeResult)
async def bulk_categorize(payload: BulkCategorizeRequest,
                          service: ProductService = Depends(get_product_service),
                          user: dict = Depends(require_user)):
    return service.bulk_categorize(payload.ids, payload.category_id, actor_of(user))


@router.get("/trash", response_model=PaginatedProductResponse)
async def list_trash(page: int = Query(1, ge=1),
                     service: ProductService = Depends(get_product_service),
                     user: dict = Depends(require_user)):
    return service.list_trash(page=page)


@router.get("/category/{category_id}", response_model=List[Product])
async def get_products_by_category(category_id: UUID,
                                   service: ProductService = Depends(get_product_service)):
    return service.list_by_category(category_id)


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: UUID,
                      service: ProductService = Depends(get_product_service)):
    return service.get_product(product_id)


@router.get("/{product_id}/audit", response_model=List[AuditEntry])
async def get_product_audit(product_id: UUID,
                            service: ProductService = Depends(get_product_service),
                            user: dict = Depends(require_user)):
    return service.list_audit(product_id)


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: UUID, product_update: ProductUpdate,
                         service: ProductService = Depends(get_product_service),
                         user: dict = Depends(require_user)):
    return service.update_product(
        product_id, product_update.model_dump(mode="json", exclude_unset=True),
        actor_of(user))


@router.post("/{product_id}/restore", response_model=Product)
async def restore_product(product_id: UUID,
                          service: ProductService = Depends(get_product_service),
                          user: dict = Depends(require_user)):
    return service.restore_product(product_id, actor_of(user))


@router.delete("/{product_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_permanent(product_id: UUID,
                                   service: ProductService = Depends(get_product_service),
                                   user: dict = Depends(require_user)):
    service.delete_permanent(product_id, actor_of(user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID,
                         service: ProductService = Depends(get_product_service),
                         user: dict = Depends(require_user)):
    service.delete_product(product_id, actor_of(user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
