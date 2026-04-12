from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from stylist.image_utils import optimize_image_to_jpeg


class ImageProcessingTests(SimpleTestCase):
    def test_optimize_image_resizes_and_converts_to_jpeg(self):
        source = Image.new("RGB", (2400, 1600), color=(30, 100, 150))
        source_buffer = BytesIO()
        source.save(source_buffer, format="PNG")
        source_buffer.seek(0)

        uploaded = SimpleUploadedFile(
            name="source.png",
            content=source_buffer.read(),
            content_type="image/png",
        )
        optimized = optimize_image_to_jpeg(uploaded, max_dimension=1024, quality=80)

        result = Image.open(BytesIO(optimized.read()))
        self.assertEqual(result.format, "JPEG")
        self.assertLessEqual(max(result.size), 1024)
