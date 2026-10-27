"""Data access for categories. Only this layer knows Supabase query syntax."""
from core.supabase_client import get_supabase_client


class SupabaseCategoryRepository:
    def list(self):
        response = get_supabase_client().table("categories").select("*").execute()
        return response.data or []

    def get(self, category_id):
        response = (
            get_supabase_client().table("categories").select("*")
            .eq("id", str(category_id)).execute()
        )
        return response.data[0] if response.data else None

    def get_by_name(self, name):
        response = (
            get_supabase_client().table("categories").select("*")
            .ilike("name", str(name)).execute()
        )
        for row in response.data or []:
            if row["name"].lower() == str(name).lower():
                return row
        return None

    def create(self, data):
        response = get_supabase_client().table("categories").insert(data).execute()
        return response.data[0] if response.data else None

    def update(self, category_id, data):
        response = (
            get_supabase_client().table("categories").update(data)
            .eq("id", str(category_id)).execute()
        )
        return response.data[0] if response.data else None

    def delete(self, category_id):
        response = (
            get_supabase_client().table("categories").delete()
            .eq("id", str(category_id)).execute()
        )
        return bool(response.data)
