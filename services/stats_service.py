"""Dashboard aggregates, computed from repository rows."""


class StatsService:
    def __init__(self, products, categories):
        self.products = products
        self.categories = categories

    def get_stats(self) -> dict:
        rows = self.products.stats_rows()
        total = len(rows)
        if total == 0:
            return {"total_products": 0, "total_categories": len(self.categories.list()),
                    "average_price": 0, "inventory_value": 0}
        prices = [float(r["price"]) for r in rows]
        inventory = sum(float(r["price"]) * int(r.get("stock") or 0) for r in rows)
        return {
            "total_products": total,
            "total_categories": len(self.categories.list()),
            "average_price": round(sum(prices) / total, 2),
            "inventory_value": round(inventory, 2),
        }
