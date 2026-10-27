"""Credential-free test harness: in-memory repositories + overridden auth.

The production repositories talk to Supabase; these fakes implement the same
repository interface in memory so the full HTTP contract can be tested with
no SUPABASE_URL / SUPABASE_KEY at all.
"""
import uuid

import pytest
from fastapi.testclient import TestClient


class FakeCategoryRepository:
    def __init__(self):
        self.rows = {}

    def list(self):
        return list(self.rows.values())

    def get(self, category_id):
        return self.rows.get(str(category_id))

    def get_by_name(self, name):
        for row in self.rows.values():
            if row["name"].lower() == str(name).lower():
                return row
        return None

    def create(self, data):
        row = {"id": str(uuid.uuid4()), "name": data["name"]}
        self.rows[row["id"]] = row
        return row

    def update(self, category_id, data):
        row = self.rows.get(str(category_id))
        if row is None:
            return None
        row.update({k: v for k, v in data.items() if v is not None})
        return row

    def delete(self, category_id):
        return self.rows.pop(str(category_id), None) is not None

    def count_products(self, category_id, product_repo):
        return sum(
            1
            for p in product_repo.rows.values()
            if p["category_id"] == str(category_id) and p.get("deleted_at") is None
        )


class FakeProductRepository:
    def __init__(self):
        self.rows = {}
        self.audit = []

    # -- reads ---------------------------------------------------------
    def _visible(self, include_deleted=False):
        rows = list(self.rows.values())
        if not include_deleted:
            rows = [r for r in rows if r.get("deleted_at") is None]
        return rows

    def list(self, *, category_id=None, search=None, min_price=None,
             max_price=None, in_stock=False, sort_by="name", page=1,
             page_size=10, include_deleted=False):
        rows = self._visible(include_deleted)
        if category_id:
            rows = [r for r in rows if r["category_id"] == str(category_id)]
        if search:
            needle = search.strip().lower()
            if needle:
                rows = [r for r in rows if needle in r["name"].lower()]
        if min_price is not None:
            rows = [r for r in rows if float(r["price"]) >= float(min_price)]
        if max_price is not None:
            rows = [r for r in rows if float(r["price"]) <= float(max_price)]
        if in_stock:
            rows = [r for r in rows if int(r.get("stock") or 0) > 0]
        if sort_by == "price_low":
            rows.sort(key=lambda r: float(r["price"]))
        elif sort_by == "price_high":
            rows.sort(key=lambda r: float(r["price"]), reverse=True)
        else:
            rows.sort(key=lambda r: r["name"])
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start:start + page_size], total

    def list_all(self, *, category_id=None, search=None):
        rows, _ = self.list(category_id=category_id, search=search,
                            page=1, page_size=100000)
        return rows

    def list_deleted(self, *, page=1, page_size=10):
        rows = [r for r in self.rows.values() if r.get("deleted_at") is not None]
        rows.sort(key=lambda r: r["name"])
        total = len(rows)
        start = (page - 1) * page_size
        return rows[start:start + page_size], total

    def get(self, product_id, include_deleted=False):
        row = self.rows.get(str(product_id))
        if row is None:
            return None
        if not include_deleted and row.get("deleted_at") is not None:
            return None
        return row

    def stats_rows(self):
        return [
            {"price": r["price"], "stock": r.get("stock") or 0}
            for r in self._visible()
        ]

    # -- writes --------------------------------------------------------
    def create(self, data):
        row = {
            "id": str(uuid.uuid4()),
            "name": data["name"],
            "description": data.get("description"),
            "price": data["price"],
            "category_id": str(data["category_id"]),
            "image_url": data.get("image_url"),
            "sku": data.get("sku"),
            "stock": data.get("stock") or 0,
            "deleted_at": None,
        }
        self.rows[row["id"]] = row
        return row

    def update(self, product_id, data):
        row = self.get(product_id, include_deleted=True)
        if row is None:
            return None
        row.update(data)
        return row

    def set_deleted(self, product_id, deleted_at):
        row = self.rows.get(str(product_id))
        if row is None:
            return None
        row["deleted_at"] = deleted_at
        return row

    def delete_permanent(self, product_id):
        return self.rows.pop(str(product_id), None) is not None

    def add_audit(self, product_id, actor, action, before, after):
        entry = {
            "id": str(uuid.uuid4()),
            "product_id": str(product_id),
            "actor": actor,
            "action": action,
            "before": before,
            "after": after,
        }
        self.audit.append(entry)
        return entry

    def list_audit(self, product_id):
        return [a for a in self.audit if a["product_id"] == str(product_id)]


@pytest.fixture()
def fake_repos():
    return FakeProductRepository(), FakeCategoryRepository()


@pytest.fixture()
def client(fake_repos):
    # Imported lazily so a missing implementation fails per-test, not at
    # collection time for the whole suite.
    from main import app
    from api.deps import get_product_service, get_category_service, get_stats_service
    from core.auth import require_user
    from services.product_service import ProductService
    from services.category_service import CategoryService
    from services.stats_service import StatsService

    products, categories = fake_repos
    app.dependency_overrides[get_product_service] = lambda: ProductService(products, categories)
    app.dependency_overrides[get_category_service] = lambda: CategoryService(categories, products)
    app.dependency_overrides[get_stats_service] = lambda: StatsService(products, categories)
    app.dependency_overrides[require_user] = lambda: {"id": "user-1", "email": "staff@example.com"}
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def anon_client(fake_repos):
    """Same app without the auth override: writes must 401."""
    from main import app
    from api.deps import get_product_service, get_category_service, get_stats_service
    from services.product_service import ProductService
    from services.category_service import CategoryService
    from services.stats_service import StatsService

    products, categories = fake_repos
    app.dependency_overrides[get_product_service] = lambda: ProductService(products, categories)
    app.dependency_overrides[get_category_service] = lambda: CategoryService(categories, products)
    app.dependency_overrides[get_stats_service] = lambda: StatsService(products, categories)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_category(client, name="Electronics"):
    response = client.post("/categories/", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def make_product(client, category_id, name="Wireless Mouse", price=25.99, **extra):
    payload = {"name": name, "price": price, "category_id": category_id}
    payload.update(extra)
    response = client.post("/products/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
