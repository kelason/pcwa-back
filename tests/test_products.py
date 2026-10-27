from conftest import make_category, make_product


# T1.1 richer fields
def test_create_product_with_rich_fields_round_trips(client):
    cat = make_category(client)
    p = make_product(client, cat["id"], description="Ergonomic", sku="WM-1", stock=7, image_url="https://x/y.png")
    assert p["description"] == "Ergonomic"
    assert p["sku"] == "WM-1"
    assert p["stock"] == 7
    assert p["image_url"] == "https://x/y.png"


def test_create_product_rejects_negative_stock(client):
    cat = make_category(client)
    r = client.post("/products/", json={"name": "A", "price": 1, "category_id": cat["id"], "stock": -1})
    assert r.status_code == 422


def test_create_product_without_optional_fields_still_works(client):
    cat = make_category(client)
    p = make_product(client, cat["id"])
    assert p["stock"] == 0
    assert p["description"] is None


def test_create_product_invalid_price_returns_422_with_detail(client):
    cat = make_category(client)
    r = client.post("/products/", json={"name": "A", "price": -5, "category_id": cat["id"]})
    assert r.status_code == 422
    assert "detail" in r.json()


# T1.2 search
def test_search_filters_by_name_case_insensitive(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="Wireless Mouse")
    make_product(client, cat["id"], name="Keyboard")
    data = client.get("/products/", params={"search": "wireless"}).json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Wireless Mouse"


def test_search_empty_string_behaves_like_no_search(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="A")
    data = client.get("/products/", params={"search": "  "}).json()
    assert data["total"] == 1


def test_search_with_wildcard_chars_does_not_500(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="A")
    r = client.get("/products/", params={"search": "%"})
    assert r.status_code == 200


# T2.2 advanced filters
def test_price_range_filters(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="Cheap", price=5)
    make_product(client, cat["id"], name="Pricey", price=50)
    data = client.get("/products/", params={"min_price": 10, "max_price": 100}).json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Pricey"


def test_in_stock_excludes_zero_stock(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="In", stock=3)
    make_product(client, cat["id"], name="Out", stock=0)
    data = client.get("/products/", params={"in_stock": True}).json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "In"


def test_min_greater_than_max_returns_422(client):
    r = client.get("/products/", params={"min_price": 100, "max_price": 10})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_filters_compose_with_search_and_category(client):
    cat = make_category(client)
    other = make_category(client, "Other")
    make_product(client, cat["id"], name="Red Mouse", price=20, stock=1)
    make_product(client, other["id"], name="Red Mouse", price=20, stock=1)
    data = client.get("/products/", params={"search": "mouse", "category_id": cat["id"], "in_stock": True}).json()
    assert data["total"] == 1
    assert data["items"][0]["category_id"] == cat["id"]


# T2.4 bulk
def test_bulk_delete_removes_listed_only(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    make_product(client, cat["id"], name="B")
    r = client.post("/products/bulk-delete", json={"ids": [a["id"]]})
    assert r.status_code == 200
    assert r.json()["deleted"] == 1
    assert client.get("/products/").json()["total"] == 1


def test_bulk_delete_reports_unknown_id_without_failing_others(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    r = client.post("/products/bulk-delete", json={"ids": [a["id"], "00000000-0000-0000-0000-000000000000"]})
    body = r.json()
    assert body["deleted"] == 1
    assert len(body["failed"]) == 1


def test_bulk_categorize_rejects_unknown_category_422(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    r = client.post("/products/bulk-categorize", json={"ids": [a["id"]], "category_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 422


def test_bulk_empty_ids_returns_422(client):
    r = client.post("/products/bulk-delete", json={"ids": []})
    assert r.status_code == 422


def test_bulk_categorize_moves_products(client):
    cat = make_category(client)
    target = make_category(client, "Target")
    a = make_product(client, cat["id"], name="A")
    r = client.post("/products/bulk-categorize", json={"ids": [a["id"]], "category_id": target["id"]})
    assert r.json()["updated"] == 1
    assert client.get(f"/products/{a['id']}").json()["category_id"] == target["id"]


# T2.5 CSV
def test_export_returns_csv_with_header_and_rows(client):
    cat = make_category(client)
    make_product(client, cat["id"], name="Widget", price=9.5, stock=2)
    r = client.get("/products/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert r.text.splitlines()[0] == "name,description,price,category_name,sku,stock,image_url"
    assert "Widget" in r.text


def test_import_creates_valid_rows_and_reports_bad_price_row(client):
    cat = make_category(client)
    csv_body = (
        "name,description,price,category_name,sku,stock,image_url\n"
        "Good,,10,Electronics,G-1,5,\n"
        "Bad,,not-a-price,Electronics,B-1,5,\n"
    )
    r = client.post("/products/import", files={"file": ("p.csv", csv_body, "text/csv")})
    body = r.json()
    assert body["created"] == 1
    assert len(body["failed"]) == 1
    assert body["failed"][0]["row"] == 3


def test_import_unknown_category_name_is_reported_not_created(client):
    make_category(client)
    csv_body = "name,description,price,category_name,sku,stock,image_url\nX,,10,Nope,,1,\n"
    r = client.post("/products/import", files={"file": ("p.csv", csv_body, "text/csv")})
    assert r.json()["created"] == 0
    assert len(r.json()["failed"]) == 1


def test_export_respects_category_filter(client):
    cat = make_category(client)
    other = make_category(client, "Other")
    make_product(client, cat["id"], name="InCat")
    make_product(client, other["id"], name="InOther")
    r = client.get("/products/export", params={"category_id": cat["id"]})
    assert "InCat" in r.text
    assert "InOther" not in r.text


# T3.3 soft delete / trash / audit
def test_soft_delete_hides_from_list_but_appears_in_trash(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    assert client.delete(f"/products/{a['id']}").status_code == 204
    assert client.get("/products/").json()["total"] == 0
    trash = client.get("/products/trash").json()
    assert trash["total"] == 1
    assert trash["items"][0]["id"] == a["id"]


def test_restore_returns_product_to_list(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    client.delete(f"/products/{a['id']}")
    r = client.post(f"/products/{a['id']}/restore")
    assert r.status_code == 200
    assert client.get("/products/").json()["total"] == 1


def test_permanent_delete_removes_from_trash(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    client.delete(f"/products/{a['id']}")
    assert client.delete(f"/products/{a['id']}/permanent").status_code == 204
    assert client.get("/products/trash").json()["total"] == 0


def test_audit_row_written_on_update_with_actor(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    client.put(f"/products/{a['id']}", json={"name": "A2"})
    audit = client.get(f"/products/{a['id']}/audit").json()
    assert any(row["action"] == "update" and row["actor"] == "staff@example.com" for row in audit)


# Review fixes (whole-branch review, Important)
def test_audit_visible_for_trashed_product(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A")
    client.delete(f"/products/{a['id']}")
    r = client.get(f"/products/{a['id']}/audit")
    assert r.status_code == 200
    assert any(row["action"] == "soft_delete" for row in r.json())


def test_bulk_categorize_reports_unknown_id_without_failing_others(client):
    cat = make_category(client)
    target = make_category(client, "Target")
    a = make_product(client, cat["id"], name="A")
    r = client.post("/products/bulk-categorize", json={
        "ids": [a["id"], "00000000-0000-0000-0000-000000000000"],
        "category_id": target["id"],
    })
    assert r.status_code == 200
    assert r.json()["updated"] == 1
    assert len(r.json()["failed"]) == 1


def test_audit_failure_does_not_misreport_applied_create(client, fake_repos):
    products, _categories = fake_repos
    def broken_audit(*args, **kwargs):
        raise RuntimeError("audit table unavailable")
    products.add_audit = broken_audit
    cat = make_category(client)
    p = make_product(client, cat["id"], name="Applied")
    assert p["name"] == "Applied"
    assert client.get("/products/").json()["total"] == 1


def test_update_can_clear_nullable_fields(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A", description="Keep?", sku="S-1")
    r = client.put(f"/products/{a['id']}", json={"description": None, "sku": None})
    assert r.status_code == 200
    body = r.json()
    assert body["description"] is None
    assert body["sku"] is None


def test_partial_update_does_not_clear_nullable_fields(client):
    cat = make_category(client)
    a = make_product(client, cat["id"], name="A", description="Stay")
    client.put(f"/products/{a['id']}", json={"name": "A2"})
    assert client.get(f"/products/{a['id']}").json()["description"] == "Stay"
