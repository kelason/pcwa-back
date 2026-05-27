from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from postgrest.exceptions import APIError

from middleware.cors import setup_cors
from api.categories import router as categories_router
from api.products import router as products_router

app = FastAPI(
    title="Product Catalog API",
    description="A CRUD API for managing a product catalog using FastAPI and Supabase",
    version="1.0.0"
)

setup_cors(app)

# --- Global Exception Handler ---

@app.exception_handler(APIError)
async def supabase_api_error_handler(request: Request, exc: APIError):
    """Catch Supabase/PostgREST errors and return them cleanly."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "code": exc.code, "hint": exc.hint},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catch Pydantic validation errors and print details for debugging."""
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )

# --- Include Routers ---
app.include_router(categories_router)
app.include_router(products_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
