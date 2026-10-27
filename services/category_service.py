"""Business rules for categories. No HTTP, no Supabase syntax here."""
from fastapi import HTTPException, status


class CategoryService:
    def __init__(self, categories, products):
        self.categories = categories
        self.products = products

    def list_categories(self):
        return self.categories.list()

    def get_category(self, category_id):
        row = self.categories.get(category_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Category {category_id} not found")
        return row

    def create_category(self, data: dict):
        try:
            row = self.categories.create(data)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
        if row is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Failed to create category")
        return row

    def update_category(self, category_id, data: dict):
        cleaned = {k: v for k, v in data.items() if v is not None}
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="No fields provided for update")
        row = self.categories.update(category_id, cleaned)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Category {category_id} not found")
        return row

    def delete_category(self, category_id):
        existing = self.categories.get(category_id)
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Category {category_id} not found")
        _, total = self.products.list(category_id=str(category_id), page=1, page_size=1)
        if total > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{existing['name']}' still has {total} product(s); move or delete them first",
            )
        self.categories.delete(category_id)
