from conftest import make_category, make_product


# T2.1 stats
def test_stats_empty_catalog_returns_zeros(client):
    data = client.get("/stats").json()
    assert data == {"total_products": 0, "total_categories": 0, "average_price": 0, "inventory_value": 0}


def test_stats_counts_and_averages_match_seed(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="A", price=10, stock=2)
    make_product(client, cat["id"], name="B", price=20, stock=1)
    data = client.get("/stats").json()
    assert data["total_products"] == 2
    assert data["total_categories"] == 1
    assert data["average_price"] == 15
    assert data["inventory_value"] == 40


# T3.1 auth
def test_create_product_without_token_returns_401(anon_client):
    r = anon_client.post("/products/", json={"name": "A", "price": 1, "category_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 401


def test_list_products_stays_public(anon_client):
    r = anon_client.get("/products/")
    assert r.status_code == 200


def test_create_category_without_token_returns_401(anon_client):
    r = anon_client.post("/categories/", json={"name": "X"})
    assert r.status_code == 401
