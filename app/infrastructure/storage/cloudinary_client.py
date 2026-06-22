import cloudinary
import cloudinary.uploader

from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

FOLDERS = {
    "profile": "femora/profiles",
    "product": "femora/products",
    "review": "femora/reviews",
    "tryon": "femora/tryon",
}


async def upload_image(file_bytes: bytes, folder_key: str, public_id: str | None = None) -> str:
    folder = FOLDERS.get(folder_key, "femora/misc")
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
        transformation=[{"quality": "auto", "fetch_format": "auto"}],
    )
    return result["secure_url"]


async def delete_image(public_id: str) -> None:
    cloudinary.uploader.destroy(public_id)
