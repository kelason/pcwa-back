"""Business rules for products. No HTTP routing, no Supabase syntax here;
routers translate, repositories store, this layer decides."""
import csv
import io
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status

from repositories.product_repository import utc_now_iso

PAGE_SIZE = 10
CSV_HEADER = ["name", "description", "price", "category_name", "sku", "stock", "image_url"]
MAX_IMPORT_ROWS = 1000


def _jsonable(row):
    if row is None:
        return None
    return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in dict(row).items()}


class ProductService:
    def __init__(self, products, categories):
        self.products = products
        self.categories = categories

    # -- audit -----------------------------------------------------------
    def _audit(self, product_id, actor, action, before, after):
        # Audit is best-effort: Supabase REST gives no transaction spanning
        # the mutation and this insert, so failing the request after the
        # write applied would misreport applied work (review finding).
        # The failure is logged loudly instead of hidden.
        try:
            self.products.add_audit(product_id, actor, action, _jsonable(before), _jsonable(after))
        except Exception as exc:  # pragma: no cover - exercised via monkeypatch test
            print(f"AUDIT WRITE FAILED product={product_id} action={action}: {exc}")

    def list_audit(self, product_id):
        row = self.products.get(product_id, include_deleted=True)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Product {product_id} not found")
        return self.products.list_audit(product_id)

    # -- reads -----------------------------------------------------------
    def list_products(self, *, category_id=None, search=None, min_price=None,
                      max_price=None, in_stock=False, sort_by="name", page=1):
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=422,
                                detail="min_price cannot be greater than max_price")
        items, total = self.products.list(
            category_id=str(category_id) if category_id else None,
            search=search, min_price=min_price, max_price=max_price,
            in_stock=in_stock, sort_by=sort_by, page=page, page_size=PAGE_SIZE,
        )
        return {"items": items, "total": total, "page": page, "size": PAGE_SIZE}

    def list_trash(self, *, page=1):
        items, total = self.products.list_deleted(page=page, page_size=PAGE_SIZE)
        return {"items": items, "total": total, "page": page, "size": PAGE_SIZE}

    def get_product(self, product_id):
        row = self.products.get(product_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Product {product_id} not found")
        return row

    def list_by_category(self, category_id):
        rows, _ = self.products.list(category_id=str(category_id), page=1, page_size=100000)
        return rows

    # -- writes ----------------------------------------------------------
    def _require_category(self, category_id):
        if self.categories.get(category_id) is None:
            raise HTTPException(status_code=422,
                                detail=f"Category {category_id} does not exist")

    def create_product(self, data: dict, actor: str):
        self._require_category(data["category_id"])
        try:
            row = self.products.create(data)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        if row is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Failed to create product")
        self._audit(row["id"], actor, "create", None, row)
        return row

    NULLABLE_FIELDS = {"description", "image_url", "sku"}

    def update_product(self, product_id, data: dict, actor: str):
        # Explicit null clears a nullable field; null for anything else is
        # treated as "not provided" (routers dump with exclude_unset=True).
        cleaned = {k: v for k, v in data.items()
                   if v is not None or k in self.NULLABLE_FIELDS}
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="No fields provided for update")
        if "category_id" in cleaned:
            self._require_category(cleaned["category_id"])
        before = self.get_product(product_id)
        row = self.products.update(product_id, cleaned)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Product {product_id} not found")
        self._audit(product_id, actor, "update", before, row)
        return row

    def delete_product(self, product_id, actor: str):
        """Soft delete (T3.3): the row moves to trash, it is not destroyed."""
        before = self.get_product(product_id)
        self.products.set_deleted(product_id, utc_now_iso())
        self._audit(product_id, actor, "soft_delete", before, None)

    def restore_product(self, product_id, actor: str):
        row = self.products.get(product_id, include_deleted=True)
        if row is None or row.get("deleted_at") is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Deleted product {product_id} not found")
        restored = self.products.set_deleted(product_id, None)
        self._audit(product_id, actor, "restore", row, restored)
        return restored

    def delete_permanent(self, product_id, actor: str):
        row = self.products.get(product_id, include_deleted=True)
        if row is None or row.get("deleted_at") is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Deleted product {product_id} not found")
        self.products.delete_permanent(product_id)
        self._audit(product_id, actor, "permanent_delete", row, None)

    # -- bulk ------------------------------------------------------------
    def bulk_delete(self, ids, actor: str):
        deleted, failed = 0, []
        for product_id in ids:
            try:
                self.delete_product(product_id, actor)
                deleted += 1
            except HTTPException as exc:
                failed.append({"id": str(product_id), "reason": str(exc.detail)})
        return {"deleted": deleted, "failed": failed}

    def bulk_categorize(self, ids, category_id, actor: str):
        self._require_category(category_id)
        updated, failed = 0, []
        for product_id in ids:
            try:
                before = self.get_product(product_id)
                self.products.update(product_id, {"category_id": str(category_id)})
                self._audit(product_id, actor, "update", before,
                            self.products.get(product_id))
                updated += 1
            except HTTPException as exc:
                failed.append({"id": str(product_id), "reason": str(exc.detail)})
        return {"updated": updated, "failed": failed}

    # -- CSV ---------------------------------------------------------------
    def export_csv(self, *, category_id=None, search=None) -> str:
        rows = self.products.list_all(
            category_id=str(category_id) if category_id else None, search=search)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CSV_HEADER)
        for row in rows:
            category = self.categories.get(row["category_id"])
            writer.writerow([
                row["name"], row.get("description") or "", row["price"],
                category["name"] if category else "",
                row.get("sku") or "", row.get("stock") or 0,
                row.get("image_url") or "",
            ])
        return buffer.getvalue()

    def import_csv(self, text: str, actor: str):
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames != CSV_HEADER:
            raise HTTPException(status_code=422,
                                detail=f"CSV header must be: {','.join(CSV_HEADER)}")
        created, failed = 0, []
        for index, raw in enumerate(reader, start=2):
            if index - 1 > MAX_IMPORT_ROWS:
                raise HTTPException(status_code=422,
                                    detail=f"Import exceeds {MAX_IMPORT_ROWS} rows")
            try:
                category = self.categories.get_by_name((raw.get("category_name") or "").strip())
                if category is None:
                    raise ValueError(f"Unknown category '{raw.get('category_name')}'")
                try:
                    price = Decimal((raw.get("price") or "").strip())
                except InvalidOperation:
                    raise ValueError(f"Invalid price '{raw.get('price')}'")
                if price < 0:
                    raise ValueError("Price cannot be negative")
                name = (raw.get("name") or "").strip()
                if not name:
                    raise ValueError("Name cannot be empty")
                stock_raw = (raw.get("stock") or "0").strip() or "0"
                try:
                    stock = int(stock_raw)
                except ValueError:
                    raise ValueError(f"Invalid stock '{stock_raw}'")
                if stock < 0:
                    raise ValueError("Stock cannot be negative")
                row = self.products.create({
                    "name": name,
                    "description": (raw.get("description") or "").strip() or None,
                    "price": price,
                    "category_id": category["id"],
                    "sku": (raw.get("sku") or "").strip() or None,
                    "stock": stock,
                    "image_url": (raw.get("image_url") or "").strip() or None,
                })
                if row is None:
                    raise ValueError("Failed to create product")
                self._audit(row["id"], actor, "create", None, row)
                created += 1
            except ValueError as exc:
                failed.append({"row": index, "reason": str(exc)})
            except Exception as exc:
                failed.append({"row": index, "reason": f"Storage error: {exc}"})
        return {"created": created, "failed": failed}
