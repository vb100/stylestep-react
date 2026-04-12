from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


class ImageValidationError(Exception):
    pass


class ImageOptimizationError(Exception):
    pass


def verify_uploaded_image(uploaded_file) -> None:
    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError("Uploaded file is not a valid image.") from exc
    finally:
        uploaded_file.seek(0)


def optimize_image_to_jpeg(
    uploaded_file,
    max_dimension: int | None = None,
    quality: int | None = None,
) -> ContentFile:
    max_dimension = max_dimension or settings.IMAGE_OPTIMIZED_MAX_DIM
    quality = quality or settings.IMAGE_OPTIMIZED_QUALITY

    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode != "RGB":
                image = image.convert("RGB")

            resampling_lanczos = getattr(Image, "Resampling", Image).LANCZOS
            image.thumbnail((max_dimension, max_dimension), resampling_lanczos)

            output = BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)
            return ContentFile(output.read())
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageOptimizationError("Image optimization failed.") from exc
