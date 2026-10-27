from conftest import make_category, make_product


def test_update_category_renames(client):
    cat = make_category(client, "Old")
    r = client.put(f"/categories/{cat['id']}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_delete_unused_category_returns_204(client):
    cat = make_category(client)
    assert client.delete(f"/categories/{cat['id']}").status_code == 204
    assert client.get("/categories/").json() == []


def test_delete_category_with_products_returns_409(client):
    cat = make_category(client)
    make_product(client, cat["id"])
    r = client.delete(f"/categories/{cat['id']}")
    assert r.status_code == 409
    assert "detail" in r.json()


def test_update_missing_category_returns_404(client):
    r = client.put("/categories/00000000-0000-0000-0000-000000000000", json={"name": "X"})
    assert r.status_code == 404


def test_create_category_empty_name_returns_422(client):
    r = client.post("/categories/", json={"name": "  "})
    assert r.status_code == 422
