"""Product image upload via Supabase Storage (T2.6).

The file goes browser -> this endpoint -> Storage bucket `product-images`;
only the public URL is stored on the product. Keys stay server-side.
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.auth import require_user

router = APIRouter(prefix="/uploads", tags=["Uploads"])

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_BYTES = 5 * 1024 * 1024
BUCKET = "product-images"


@router.post("/product-image")
async def upload_product_image(file: UploadFile = File(...),
                               user: dict = Depends(require_user)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=422,
                            detail=f"Only PNG, JPEG or WebP images are allowed, got {file.content_type}")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB")
    if not raw:
        raise HTTPException(status_code=422, detail="Empty file")
    extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[file.content_type]
    object_name = f"{uuid.uuid4()}.{extension}"
    try:
        from core.supabase_client import get_supabase_client
        client = get_supabase_client()
        client.storage.from_(BUCKET).upload(
            object_name, raw, {"content-type": file.content_type})
        url = client.storage.from_(BUCKET).get_public_url(object_name)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc}")
    return {"url": url}
