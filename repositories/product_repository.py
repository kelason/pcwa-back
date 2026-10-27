"""Data access for products. Only this layer knows Supabase query syntax.

The soft-delete predicate (`deleted_at is null`) lives here, in exactly one
place, so list/search/stats/export can never disagree about trash.
"""
from datetime import datetime, timezone

from core.supabase_client import get_supabase_client


class SupabaseProductRepository:
    def _base_query(self, include_deleted=False):
        query = get_supabase_client().table("products").select("*", count="exact")
        if not include_deleted:
            query = query.is_("deleted_at", "null")
        return query

    def list(self, *, category_id=None, search=None, min_price=None,
             max_price=None, in_stock=False, sort_by="name", page=1,
             page_size=10, include_deleted=False):
        query = self._base_query(include_deleted)
        if category_id:
            query = query.eq("category_id", str(category_id))
        if search and search.strip():
            query = query.ilike("name", f"%{search.strip()}%")
        if min_price is not None:
            query = query.gte("price", float(min_price))
        if max_price is not None:
            query = query.lte("price", float(max_price))
        if in_stock:
            query = query.gt("stock", 0)
        if sort_by == "price_low":
            query = query.order("price", desc=False)
        elif sort_by == "price_high":
            query = query.order("price", desc=True)
        else:
            query = query.order("name", desc=False)
        start = (page - 1) * page_size
        response = query.range(start, start + page_size - 1).execute()
        return response.data or [], response.count or 0

    def list_all(self, *, category_id=None, search=None):
        rows, _ = self.list(category_id=category_id, search=search,
                            page=1, page_size=100000)
        return rows

    def list_deleted(self, *, page=1, page_size=10):
        query = (
            get_supabase_client().table("products").select("*", count="exact")
            .not_.is_("deleted_at", "null").order("name", desc=False)
        )
        start = (page - 1) * page_size
        response = query.range(start, start + page_size - 1).execute()
        return response.data or [], response.count or 0

    def get(self, product_id, include_deleted=False):
        response = (
            get_supabase_client().table("products").select("*")
            .eq("id", str(product_id)).execute()
        )
        if not response.data:
            return None
        row = response.data[0]
        if not include_deleted and row.get("deleted_at") is not None:
            return None
        return row

    def stats_rows(self):
        response = (
            get_supabase_client().table("products").select("price, stock")
            .is_("deleted_at", "null").execute()
        )
        return response.data or []

    def create(self, data):
        response = get_supabase_client().table("products").insert(data).execute()
        return response.data[0] if response.data else None

    def update(self, product_id, data):
        response = (
            get_supabase_client().table("products").update(data)
            .eq("id", str(product_id)).execute()
        )
        return response.data[0] if response.data else None

    def set_deleted(self, product_id, deleted_at):
        return self.update(product_id, {"deleted_at": deleted_at})

    def delete_permanent(self, product_id):
        response = (
            get_supabase_client().table("products").delete()
            .eq("id", str(product_id)).execute()
        )
        return bool(response.data)

    def add_audit(self, product_id, actor, action, before, after):
        response = (
            get_supabase_client().table("product_audit")
            .insert({
                "product_id": str(product_id),
                "actor": actor,
                "action": action,
                "before": before,
                "after": after,
            })
            .execute()
        )
        return response.data[0] if response.data else None

    def list_audit(self, product_id):
        response = (
            get_supabase_client().table("product_audit").select("*")
            .eq("product_id", str(product_id))
            .order("created_at", desc=False).execute()
        )
        return response.data or []


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
