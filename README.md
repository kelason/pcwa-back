# Product Catalog API (pcwa-back)

A high-performance backend service for managing a product catalog and categories. This project is built using FastAPI and integrates with Supabase for data persistence.

## 🌐 Live API

The production API is accessible at: [https://pcwa-back.vercel.app/](https://pcwa-back.vercel.app/)

## 🚀 Tech Stack

*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
*   **Validation:** [Pydantic v2](https://docs.pydantic.dev/)
*   **Async Support:** Fully asynchronous endpoints
*   **Environment Management:** `python-dotenv`

## 🛠️ Features

*   **Product Management:** Full CRUD for products with rich fields (description, image_url, SKU, stock).
*   **Search & Filtering:** Server-side name search, category, price-range and in-stock filters; sorting by name/price; pagination (10/page).
*   **Category Management:** Create, rename, and guarded delete (409 while products still use the category).
*   **Bulk & CSV:** Bulk delete (partial-success report), bulk re-categorize, CSV export/import with per-row failure report.
*   **Dashboard Stats:** `GET /stats` with totals, average price, inventory value.
*   **Image Upload:** `POST /uploads/product-image` to Supabase Storage (`product-images` bucket).
*   **Auth:** Supabase Auth via `POST /auth/login`; every write requires a Bearer token, reads stay public.
*   **Soft Delete & Audit:** Deletes move products to trash (`GET /products/trash`, restore, permanent delete); every mutation writes a `product_audit` row with the actor.
*   **CORS Middleware:** Configurable CORS settings for secure frontend integration.

## Architecture (layered)

```
main.py              FastAPI app, exception handlers, CORS (thin entry)
api/                 HTTP layer only: parse -> service -> response
  deps.py            Composition root (services built from repositories)
services/            Business rules (category guard, bulk, CSV, stats, audit)
repositories/        Supabase data access; the deleted_at predicate lives here only
schemas/             Pydantic request/response models
core/                config, lazy Supabase client, bearer-auth dependency
middleware/          CORS setup
supabase/migrations/ SQL to run in the Supabase SQL editor (fields, bucket, realtime, soft-delete/audit)
tests/               pytest suite, credential-free (in-memory repositories)
```

Request flow: router (`api/`) -> service (`services/`) -> repository
(`repositories/`) -> Supabase. Tests replace repositories and auth through
FastAPI dependency overrides in `tests/conftest.py`, so no real Supabase
project is needed: `venv/bin/python -m pytest -q`.

Setup checklist in Supabase: run the four files in `supabase/migrations/` in
order, create a staff user in Auth (used by `POST /auth/login`), and keep
`SUPABASE_URL` / `SUPABASE_KEY` / `FRONTEND_URL` in `.env`.

## 📋 Prerequisites

- Python 3.10+
- A Supabase Project

## ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cognizant-assesment-back
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install fastapi uvicorn supabase python-dotenv pydantic
    ```

4.  **Environment Setup:**
    Create a `.env` file in the root directory:
    ```env
    SUPABASE_URL="https://cckwqqijhshedzagymyu.supabase.co"
    SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNja3dxcWlqaHNoZWR6YWd5bXl1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTgyOTI5MiwiZXhwIjoyMDk1NDA1MjkyfQ.C0NorDtFsfnn6m-kD4SWoPoCeZjdT2LK-STYkUhG9NY"
    FRONTEND_URL=http://localhost:5173
    ```
    *Note: The Supabase client automatically handles URL formatting, ensuring compatibility even if the URL contains redundant path segments.*

## 🚀 Running the App

Start the development server with:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
Access the interactive documentation (Swagger UI) at `http://localhost:8000/docs`.

## 🔌 API Endpoints

### Products
- `GET /products/` - List products (Paginated, optional `category_id` filter)
- `POST /products/` - Create a new product
- `GET /products/{id}` - Get a specific product
- `PUT /products/{id}` - Update an existing product
- `DELETE /products/{id}` - Delete a product
- `GET /products/category/{category_id}` - Quick filter by category

### Categories
- `GET /categories/` - List all categories
- `POST /categories/` - Create a new category
- `GET /categories/{id}` - Get category details
