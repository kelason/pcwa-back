"""Composition root: routers ask for a service, this builds it from the
Supabase repositories. Tests override these factories with in-memory fakes."""
from repositories.category_repository import SupabaseCategoryRepository
from repositories.product_repository import SupabaseProductRepository
from services.category_service import CategoryService
from services.product_service import ProductService
from services.stats_service import StatsService

_product_repo = SupabaseProductRepository()
_category_repo = SupabaseCategoryRepository()


def get_product_service() -> ProductService:
    return ProductService(_product_repo, _category_repo)


def get_category_service() -> CategoryService:
    return CategoryService(_category_repo, _product_repo)


def get_stats_service() -> StatsService:
    return StatsService(_product_repo, _category_repo)
